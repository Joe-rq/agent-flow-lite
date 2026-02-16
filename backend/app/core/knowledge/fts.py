from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.core.database import DATA_DIR

logger = logging.getLogger(__name__)


FTS_TABLE = "kb_chunks_fts"


def _db_path() -> Path:
    return DATA_DIR / "app.db"


@contextmanager
def _connect(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    db_path = path or _db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()


def _ensure_fts(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_TABLE}
            USING fts5(
                text,
                kb_id UNINDEXED,
                doc_id UNINDEXED,
                chunk_id UNINDEXED,
                chunk_index UNINDEXED,
                metadata UNINDEXED
            )
            """.strip()
        )
        conn.commit()
        return True
    except sqlite3.OperationalError as exc:
        logger.warning("FTS ensure failed: %s", exc)
        return False


def _tokenize_query(query: str) -> list[str]:
    tokens = [t.strip() for t in query.split() if t.strip()]
    return tokens[:12]


def _escape_fts_term(term: str) -> str:
    return '"' + term.replace('"', '""') + '"'


def _build_match_query(query: str) -> str:
    tokens = _tokenize_query(query)
    if not tokens:
        return ""
    return " AND ".join(_escape_fts_term(t) for t in tokens)


def index_document_chunks(
    kb_id: str,
    doc_id: str,
    chunks: list[dict[str, Any]],
    *,
    db_path: Path | None = None,
) -> None:
    if not chunks:
        return

    with _connect(db_path) as conn:
        if not _ensure_fts(conn):
            return

        try:
            conn.execute(
                f"DELETE FROM {FTS_TABLE} WHERE kb_id = ? AND doc_id = ?",
                (kb_id, doc_id),
            )
            rows = []
            for idx, chunk in enumerate(chunks):
                text = str(chunk.get("text") or "")
                metadata = chunk.get("metadata") or {}
                if not isinstance(metadata, dict):
                    metadata = {}
                chunk_index_raw = metadata.get("chunk_index")
                chunk_index_i = idx
                if isinstance(chunk_index_raw, int):
                    chunk_index_i = chunk_index_raw
                elif isinstance(chunk_index_raw, str):
                    try:
                        chunk_index_i = int(chunk_index_raw)
                    except ValueError:
                        chunk_index_i = idx

                chunk_id_raw = metadata.get("chunk_id")
                if isinstance(chunk_id_raw, str) and chunk_id_raw.strip():
                    chunk_id = chunk_id_raw.strip()
                else:
                    chunk_id = f"{doc_id}_chunk_{chunk_index_i}"

                metadata.setdefault("kb_id", kb_id)
                metadata.setdefault("doc_id", doc_id)
                metadata["chunk_index"] = chunk_index_i
                metadata.setdefault("chunk_id", chunk_id)
                rows.append(
                    (
                        text,
                        kb_id,
                        doc_id,
                        chunk_id,
                        chunk_index_i,
                        json.dumps(metadata, ensure_ascii=False),
                    )
                )

            conn.executemany(
                f"""
                INSERT INTO {FTS_TABLE} (text, kb_id, doc_id, chunk_id, chunk_index, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """.strip(),
                rows,
            )
            conn.commit()
        except sqlite3.OperationalError as exc:
            logger.warning("FTS index failed: %s", exc)
            return


def keyword_search(
    kb_id: str,
    query: str,
    *,
    limit: int = 5,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    match_query = _build_match_query(query)
    if not match_query:
        return []

    with _connect(db_path) as conn:
        if not _ensure_fts(conn):
            return []

        try:
            cur = conn.execute(
                f"""
                SELECT text, metadata, kb_id, doc_id, chunk_id, chunk_index, bm25({FTS_TABLE}) AS rank
                FROM {FTS_TABLE}
                WHERE {FTS_TABLE} MATCH ? AND kb_id = ?
                ORDER BY rank
                LIMIT ?
                """.strip(),
                (match_query, kb_id, int(limit)),
            )
            rows = cur.fetchall()
        except sqlite3.OperationalError as exc:
            logger.warning("FTS search failed: %s", exc)
            return []

    results: list[dict[str, Any]] = []
    for row in rows:
        text = row["text"]
        raw_meta = row["metadata"]
        try:
            metadata = json.loads(raw_meta) if raw_meta else {}
        except Exception:
            metadata = {}

        if not isinstance(metadata, dict):
            metadata = {}
        metadata.setdefault("kb_id", row["kb_id"])
        metadata.setdefault("doc_id", row["doc_id"])
        metadata.setdefault("chunk_id", row["chunk_id"])
        try:
            metadata.setdefault("chunk_index", int(row["chunk_index"]))
        except Exception:
            pass

        rank = row["rank"]
        try:
            rank_f = float(rank)
        except Exception:
            rank_f = 0.0
        if rank_f < 0:
            rank_f = 0.0
        score = 1.0 / (1.0 + rank_f)

        results.append(
            {
                "text": text,
                "metadata": metadata,
                "score": round(float(score), 4),
            }
        )

    return results
