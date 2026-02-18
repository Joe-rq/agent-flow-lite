# SKILL.md Specification

> Version: 1.0 | Based on Agent Flow Lite codebase as of 2026-02-18

## 1. Overview

SKILL.md is the skill definition format used by Agent Flow Lite. Each skill is a single Markdown file with YAML frontmatter that defines a reusable prompt template with typed inputs, optional knowledge base integration, and model configuration.

### Design Philosophy

- **File-as-configuration**: Every skill is a plain-text file stored in `data/skills/{name}/SKILL.md`. No database records, no proprietary binary format.
- **Git-friendly**: Skills can be version-controlled, diffed, code-reviewed, and shared as regular files.
- **Human-readable**: A developer or prompt engineer can read and edit a SKILL.md in any text editor without tooling.
- **Progressive disclosure**: The frontmatter captures structured metadata; the Markdown body is the prompt itself.

### Storage Layout

```
backend/data/skills/
  article-summary/
    SKILL.md          # Required: skill definition
    SKILL.md.lock     # Auto-generated: filelock for concurrent access
  code-review/
    SKILL.md
  ...
```

Each skill lives in its own directory. The directory name **must** match the `name` field in the frontmatter (if the frontmatter includes a `name` field). The only required file is `SKILL.md`.

---

## 2. File Structure

A SKILL.md file consists of two sections separated by YAML frontmatter delimiters (`---`):

```
---
<YAML frontmatter>
---

<Markdown body (prompt template)>
```

The parser (`skill_loader.py:parse_skill_md`) splits the content on the first two `---` delimiters:

1. Everything between the first and second `---` is parsed as YAML via `yaml.safe_load`.
2. Everything after the second `---` is the Markdown body (the prompt template).

If the file does not start with `---`, the entire content is treated as the body with an empty frontmatter dict. However, a valid skill **requires** non-empty frontmatter -- loading a skill with empty frontmatter raises a `SkillValidationError`.

### Size Limit

The maximum file size is **50 KB** (51,200 bytes, measured in UTF-8). This is a soft limit enforced on create and update operations.

---

## 3. Frontmatter Schema

### 3.1 Standard Fields (Agent Skills Specification)

| Field | Required | Type | Constraints | Description |
|-------|----------|------|-------------|-------------|
| `name` | No* | `string` | 1-64 chars, `[a-z0-9-]`, no leading/trailing/consecutive hyphens | Skill identifier. Must match the directory name if present. |
| `description` | No** | `string` | 1-1024 chars | Human-readable description of the skill's purpose. Defaults to the skill name if omitted. |
| `license` | No | `string` | max 64 chars | License identifier (e.g., `MIT`, `Apache-2.0`). |
| `metadata` | No | `object` | Arbitrary key-value pairs | Extension metadata (author, version, tags, etc.). |

\* `name` is not strictly required in the frontmatter. If omitted, the directory name is used. If present, it **must** match the directory name exactly, or loading fails with a validation error.

\** `description` defaults to the skill `name` if not provided in frontmatter.

### 3.2 Extension Fields (Agent Flow Lite)

| Field | Required | Type | Constraints | Description |
|-------|----------|------|-------------|-------------|
| `inputs` | No | `array[InputDef]` | See Input Definition below | Declares input variables available in the prompt template. |
| `knowledge_base` | No | `string` | max 256 chars | ID or name of a knowledge base to use for RAG retrieval during execution. |
| `model` | No | `object` | Must be a dict (string values are ignored) | LLM model configuration. |
| `model.temperature` | No | `float` | 0.0 - 2.0 | Sampling temperature. Default: `0.7`. |
| `model.max_tokens` | No | `int` | 1 - 8192 | Maximum tokens to generate. Default: `2000`. |
| `user_id` | No | `string` | max 256 chars | Owner user ID. Auto-injected on creation if not present in frontmatter. |

### 3.3 Input Definition (`inputs[]`)

Each element in the `inputs` array defines a variable that can be referenced in the prompt body via `{{name}}`.

| Field | Required | Type | Constraints | Description |
|-------|----------|------|-------------|-------------|
| `name` | Yes | `string` | 1-64 chars | Variable name used in `{{name}}` placeholders. Entries without a `name` are silently skipped. |
| `label` | No | `string` | 1-128 chars | UI display label. Defaults to `name` if omitted. |
| `type` | No | `string` | `"text"` or `"textarea"` | Input widget type. Defaults to `"text"`. Invalid values fall back to `"text"`. |
| `required` | No | `boolean` | | Whether the input must be provided at execution time. Default: `false`. |
| `default` | No | `string` | max 1024 chars | Default value used when the input is not provided. |
| `description` | No | `string` | max 512 chars | Help text for the input. |

---

## 4. Skill Name Rules

The skill name serves as both the identifier and the filesystem directory name. Validation is enforced in both `SkillLoader._validate_name_format()` and the `SkillCreateRequest` Pydantic model.

**Rules:**

1. Lowercase only (`name == name.lower()`)
2. Only lowercase letters, numbers, and hyphens: `^[a-z0-9-]+$`
3. Cannot start or end with a hyphen
4. No consecutive hyphens (`--`)
5. Length: 1 to 64 characters
6. Must be unique (case-insensitive check across all existing skills)

**Normalization** (`SkillLoader.normalize_name()`): converts arbitrary strings to valid skill names by lowercasing, replacing spaces with hyphens, removing invalid characters, collapsing consecutive hyphens, and trimming. Falls back to `"skill"` if the result is empty.

**Valid examples:** `article-summary`, `code-review`, `product-qa`, `layer`, `my-skill-v2`

**Invalid examples:** `Article-Summary` (uppercase), `-my-skill` (leading hyphen), `my--skill` (consecutive hyphens), `my skill` (space)

---

## 5. Template Syntax

### 5.1 Placeholder Format

The Markdown body uses `{{variable_name}}` placeholders. Variable names in placeholders can contain letters (a-z, A-Z), numbers (0-9), underscores, and hyphens: `[a-zA-Z0-9_-]+`.

```markdown
Please summarize the following article in a {{style}} tone:

{{article}}
```

### 5.2 Substitution Behavior

Variable substitution is performed by `SkillExecutor.substitute_variables()` using a **single-pass** regex replacement. No recursive expansion occurs -- a substituted value containing `{{...}}` will **not** be expanded further.

**Resolution priority** for each declared input:

1. Value from `provided_inputs` (user-supplied at execution time)
2. `default` value from the input definition
3. Empty string `""`

Undeclared placeholders (not in any input's `name`) are replaced with an empty string.

### 5.3 Placeholder Validation

On **create** and **update** operations, the loader validates that every `{{placeholder}}` in the prompt body has a corresponding entry in the `inputs` array. Undeclared placeholders cause a `SkillValidationError` with a message listing the offending names.

This validation uses the pattern `\{\{(\w+)\}\}` (word characters only: `[a-zA-Z0-9_]`). Note: this is slightly more restrictive than the runtime substitution pattern which also allows hyphens.

---

## 6. Knowledge Base Integration

When a skill has a `knowledge_base` field set to a valid knowledge base ID or name, the executor performs RAG (Retrieval-Augmented Generation) before calling the LLM:

1. The first 500 characters of the **substituted prompt** are used as the search query.
2. The RAG pipeline searches the specified knowledge base with `top_k=5`.
3. The top 3 results are formatted and injected into the system prompt as numbered context blocks.
4. All retrieved results are emitted as a `citation` SSE event with source metadata.
5. If retrieval fails, execution continues without RAG context (graceful degradation).

The system prompt when RAG is active:

```
You are a helpful AI assistant.

Answer the user's request based on the provided context. If the context doesn't contain relevant information, say so clearly.

Context:
[1] <text from result 1>

[2] <text from result 2>

[3] <text from result 3>
```

---

## 7. Invocation Methods

### 7.1 Direct API Execution

**Endpoint:** `POST /api/v1/skills/{name}/run`

**Rate limit:** 10 requests per minute per user.

**Request body:**

```json
{
  "inputs": {
    "article": "The full text of the article...",
    "style": "academic"
  }
}
```

**Response:** SSE stream (`text/event-stream`). See Section 8 for event format.

**Authentication:** Requires a valid JWT token (`get_current_user` dependency).

### 7.2 Chat `@skill` Invocation

In the chat interface, users can invoke a skill by prefixing their message with `@skill-name`:

```
@article-summary This is a long article that needs to be summarized...
```

**Parsing** (`chat.py:parse_at_skill`): Uses the regex `^@([a-z0-9-]+)\s+(.+)$` with `re.DOTALL` to extract the skill name and the remaining text.

**Input mapping**: The remaining text after `@skill-name ` is mapped to:

1. The first **required** input (scanning `inputs` in order), or
2. The first input (if none are required), or
3. Discarded (if the skill has no inputs)

The skill is then executed via `SkillExecutor.execute()` and the SSE stream is forwarded to the chat response. The final output is saved to the session history.

**Timeout:** 180 seconds for the entire skill execution.

### 7.3 Workflow Skill Node

Skills can be used as nodes in visual workflows. There are two integration points:

#### Dedicated Skill Node (`execute_skill_node`)

A standalone node type `"skill"` that executes a skill with input mappings from upstream nodes.

**Node data structure:**

```json
{
  "skillName": "article-summary",
  "inputMappings": {
    "article": "upstream-node-id",
    "style": "concise"
  }
}
```

`inputMappings` maps skill input names to either:
- An upstream node ID (the output of that node is used as the value)
- A template expression (resolved via `ctx.resolve_template`)
- A direct string value

If no `inputMappings` are provided but the skill has inputs, the upstream node's output is mapped to the first required input (or the first input if none are required).

#### LLM Node with Skill Loading (`execute_llm_node`)

An LLM node can optionally reference a skill via the `skillName` data field. When set:
- The skill's prompt (Markdown body) replaces the node's `systemPrompt`.
- The skill's `model.temperature` overrides the node's temperature setting.
- The skill is used as a prompt template within the LLM node's execution flow.

---

## 8. SSE Event Protocol

All skill execution streams (direct API, chat, workflow) emit the same SSE event types. Each event is formatted as:

```
event: <type>\ndata: <json>\n\n
```

### Event Types

| Event | Purpose | Key Data Fields |
|-------|---------|-----------------|
| `thought` | Execution progress updates | `type` (validation/substitution/retrieval/generation/skill), `status` (start/complete/error), `message` |
| `token` | LLM-generated content chunk | `content` (string) |
| `citation` | Source references from RAG retrieval | `sources` (array of `{doc_id, chunk_index, score, text}`) |
| `error` | Error during execution | `message` (string) |
| `done` | Completion marker | `status` ("success" or "error"), `message` |

### Execution Event Sequence

A successful execution with knowledge base produces this event sequence:

```
1. thought {type: "validation", status: "start"}
2. thought {type: "validation", status: "complete", message: "All required inputs provided"}
3. thought {type: "substitution", status: "start"}
4. thought {type: "substitution", status: "complete", message: "Variables substituted"}
5. thought {type: "retrieval", status: "start", kb_id: "..."}
6. thought {type: "retrieval", status: "searching", kb_id: "...", query: "..."}
7. thought {type: "retrieval", status: "complete", kb_id: "...", results_count: N, top_results: [...]}
8. citation {sources: [...]}
9. thought {type: "generation", status: "start"}
10. token {content: "..."}  (repeated for each chunk)
11. done {status: "success", message: "Skill execution completed successfully"}
```

Without a knowledge base, steps 5-8 are skipped.

---

## 9. CRUD Operations

### 9.1 Create Skill

**Endpoint:** `POST /api/v1/skills`

**Request:**

```json
{
  "name": "article-summary",
  "content": "---\nname: article-summary\ndescription: Summarize articles\ninputs:\n  - name: article\n    label: Article\n    type: textarea\n    required: true\n---\n\nSummarize:\n\n{{article}}"
}
```

**Behavior:**

1. Validates name format (see Section 4).
2. Validates file size (< 50 KB).
3. Checks name uniqueness (case-insensitive).
4. Parses frontmatter and body.
5. Validates frontmatter `name` matches request `name` (if frontmatter has `name`).
6. Validates all `{{placeholders}}` are declared in `inputs`.
7. Injects `user_id` into frontmatter if provided and not already present.
8. Creates directory `data/skills/{name}/` and writes `SKILL.md`.
9. Returns `SkillDetail`.

**Response:** `201 Created` with full `SkillDetail`.

### 9.2 Read Skill

**Endpoint:** `GET /api/v1/skills/{name}`

**Behavior:** Reads and parses `SKILL.md` with FileLock protection. Validates that frontmatter exists and that the frontmatter `name` (if present) matches the directory name.

**Response:** `200 OK` with `SkillDetail`.

### 9.3 List Skills

**Endpoint:** `GET /api/v1/skills`

**Behavior:** Scans all subdirectories under `data/skills/`, attempts to parse each `SKILL.md`. Invalid skills are silently skipped. Results sorted by `updated_at` descending.

**Access control:**
- Admin users see all skills.
- Regular users see only skills where `user_id` matches their own ID. Skills without a `user_id` are hidden from non-admin users.

**Response:** `200 OK` with `SkillListResponse` containing `skills` array and `total` count.

### 9.4 Update Skill

**Endpoint:** `PUT /api/v1/skills/{name}`

**Request:**

```json
{
  "content": "---\nname: article-summary\n..."
}
```

**Behavior:** Validates size, parses content, ensures frontmatter `name` matches path `{name}` (renaming via update is not allowed), validates placeholders, writes file with FileLock.

**Response:** `200 OK` with updated `SkillDetail`.

### 9.5 Delete Skill

**Endpoint:** `DELETE /api/v1/skills/{name}`

**Behavior:** Verifies skill exists, acquires and releases FileLock, removes the lock file, then deletes the entire skill directory via `shutil.rmtree`.

**Response:** `204 No Content`.

### Error Responses

| Condition | HTTP Status |
|-----------|------------|
| Invalid name format, missing required input, parse error | `400 Bad Request` |
| Skill not found | `404 Not Found` |
| Name already exists / conflicts | `409 Conflict` |
| Internal error | `500 Internal Server Error` |

Error body format:

```json
{
  "detail": {
    "field": "name",
    "message": "Skill name must be lowercase"
  }
}
```

---

## 10. Security

- **Path traversal protection**: The loader resolves the skill file path and verifies it is within the `skills_dir` using `Path.resolve()` and `relative_to()`.
- **FileLock**: All file reads and writes use `filelock.FileLock` to prevent concurrent corruption.
- **Authentication**: All API endpoints require a valid JWT token.
- **Rate limiting**: The `/run` endpoint is rate-limited to 10 requests per minute.
- **Input size**: SKILL.md content is capped at 50 KB. Input field values have individual max-length constraints (e.g., `default` max 1024 chars).

---

## 11. Examples

### 11.1 Article Summary (with inputs and model config)

```markdown
---
name: article-summary
description: Compress long articles into structured key points.
inputs:
  - name: article
    label: Article Content
    type: textarea
    required: true
    description: The full text of the article to summarize
  - name: style
    label: Summary Style
    type: text
    required: false
    default: concise and professional
model:
  temperature: 0.3
  max_tokens: 1000
---

Please summarize the following article in a {{style}} tone:

{{article}}

## Output Requirements

- Extract 3-5 core points
- Summarize each point in one sentence
- Retain key data and citations
```

### 11.2 Code Review (multiple optional inputs)

```markdown
---
name: code-review
description: Review code quality and suggest improvements. Supports multiple languages.
inputs:
  - name: code
    label: Code
    type: textarea
    required: true
  - name: language
    label: Programming Language
    type: text
    default: auto-detect
  - name: focus
    label: Review Focus
    type: text
    default: security, performance, readability
model:
  temperature: 0.2
  max_tokens: 2000
---

Please review the following {{language}} code, focusing on {{focus}}:

```
{{code}}
```

## Review Guidelines

1. Identify specific issues with explanations and risk assessments
2. Provide improvement suggestions with example code
3. Acknowledge strengths if the code is well-written
```

### 11.3 Knowledge-Base-Powered Q&A

```markdown
---
name: product-qa
description: Answer user questions based on the product knowledge base.
inputs:
  - name: question
    label: User Question
    type: text
    required: true
knowledge_base: product-docs
model:
  temperature: 0.5
  max_tokens: 1500
---

User question: {{question}}

Answer the above question based on the product documentation in the knowledge base.

## Answer Guidelines

- Cite document content accurately
- If the knowledge base does not contain relevant information, state this clearly
- Provide links to related documents when available
```

### 11.4 Minimal Skill (no inputs)

```markdown
---
name: daily-standup
description: Generate a daily standup report template.
model:
  temperature: 0.8
---

Generate a daily standup report template with the following sections:

1. What I accomplished yesterday
2. What I plan to do today
3. Any blockers or concerns

Keep it concise and professional.
```

---

## 12. Comparison with Design Document

The existing `docs/skill-system-design.md` is the original design specification written before implementation. This document (`skill-spec.md`) describes the **actual implemented behavior** as of the current codebase. Key differences from the design doc:

- The design doc references `compatibility` and `allowed-tools` standard fields -- these are **not** implemented in the parser or models.
- The design doc shows `SkillExecutor.__init__` accepting `rag_pipeline` and `llm_client` parameters -- the actual implementation uses a parameter-less constructor with lazy-loaded globals.
- The design doc shows workflow skill node data using `input_mapping` (snake_case) -- the actual implementation uses `inputMappings` (camelCase) to match frontend conventions.
- The skill files are stored under `backend/data/skills/` (configured via `app.core.paths.SKILLS_DIR`), not a top-level `/skills/` directory.
- The `model` field in frontmatter must be a `dict` type; if it is a string, it is silently ignored by `_build_skill_detail`.
