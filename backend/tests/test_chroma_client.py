import pytest

from app.core import chroma_client as chroma_module


class _FakeCollection:
    def __init__(self, name: str):
        self.name = name
        self._count = 0
        self.metadata = {"fake": True}
        self.last_add = None
        self.last_delete = None

    def add(self, documents, ids, metadatas):
        self.last_add = {"documents": documents, "ids": ids, "metadatas": metadatas}
        self._count += len(ids)

    def delete(self, where=None):
        self.last_delete = where

    def count(self):
        return self._count


class _FakeClient:
    def __init__(self):
        self.collections: dict[str, _FakeCollection] = {}

    def get_or_create_collection(self, name: str):
        return self.collections.setdefault(name, _FakeCollection(name))

    def get_collection(self, name: str):
        if name not in self.collections:
            raise ValueError("does not exist")
        return self.collections[name]

    def delete_collection(self, name: str):
        if name not in self.collections:
            raise ValueError("does not exist")
        del self.collections[name]


def test_chroma_client_collection_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(
        chroma_module.chromadb, "PersistentClient", lambda *a, **k: fake
    )
    monkeypatch.setattr(chroma_module.os, "makedirs", lambda *a, **k: None)

    client = chroma_module.ChromaClient(persist_directory="/tmp/ignore")
    assert client.collection_exists("kb1") is False
    client.get_or_create_collection("kb1")
    assert client.collection_exists("kb1") is True


def test_chroma_client_delete_collection_returns_false_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(
        chroma_module.chromadb, "PersistentClient", lambda *a, **k: fake
    )
    monkeypatch.setattr(chroma_module.os, "makedirs", lambda *a, **k: None)

    client = chroma_module.ChromaClient(persist_directory="/tmp/ignore")
    assert client.delete_collection("missing") is False


def test_chroma_client_add_document_sets_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(
        chroma_module.chromadb, "PersistentClient", lambda *a, **k: fake
    )
    monkeypatch.setattr(chroma_module.os, "makedirs", lambda *a, **k: None)

    client = chroma_module.ChromaClient(persist_directory="/tmp/ignore")
    client.add_document("kb1", "doc1", "hello", metadata={"source": "unit"})
    collection = fake.get_collection("kb_kb1")
    assert collection.last_add is not None
    assert collection.last_add["ids"] == ["doc1"]
    assert collection.last_add["documents"] == ["hello"]
    assert collection.last_add["metadatas"][0]["document_id"] == "doc1"


def test_chroma_client_get_collection_info_handles_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(
        chroma_module.chromadb, "PersistentClient", lambda *a, **k: fake
    )
    monkeypatch.setattr(chroma_module.os, "makedirs", lambda *a, **k: None)

    client = chroma_module.ChromaClient(persist_directory="/tmp/ignore")
    info = client.get_collection_info("kb1")
    assert info["count"] == 0
    assert info["metadata"] is None


def test_chroma_client_delete_document_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(
        chroma_module.chromadb, "PersistentClient", lambda *a, **k: fake
    )
    monkeypatch.setattr(chroma_module.os, "makedirs", lambda *a, **k: None)

    client = chroma_module.ChromaClient(persist_directory="/tmp/ignore")
    assert client.delete_document("kb1", "doc1") is False

    fake.get_or_create_collection("kb_kb1")
    assert client.delete_document("kb1", "doc1") is True
