# Draft: OpenCode LSP config

## Requirements (confirmed)
- Generate an opencode.json snippet to force LSP to use the updated Bun PATH.
- Target Windows; user selected option 1 (set PATH via LSP env).

## Technical Decisions
- Provide JSON snippet using `lsp` -> per-server `env.PATH` entries.
- Cover TypeScript/Vue/Eslint/Oxlint servers used by this repo.

## Research Findings
- LSP configuration supports `env` per server (opencode LSP docs).
- No repo-local harness docs to compare; unrelated to LSP fix.

## Open Questions
- None.

## Scope Boundaries
- INCLUDE: config snippet and usage guidance.
- EXCLUDE: editing opencode.json directly (user will apply).
