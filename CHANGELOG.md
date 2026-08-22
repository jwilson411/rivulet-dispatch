# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `dispatch_sync` helper for CLI scripts and notebooks
- Example team fixtures: `team-no-assistant.json` and `team-mention-only.json`
- Empty `py.typed` marker so type checkers treat the install as typed
- Ruff lint-only CI job (`ruff check`; no format)
- Python 3.11 and 3.12 test matrix
- CONTRIBUTING.md
- SECURITY.md (GitHub private advisory; library has no network and no secrets)

### Tests

- Priority ordering: two keyword rules on one agent, per-agent first-match break, multi-mention
- Invalid regex on one agent does not fail the rest of the roster

## [0.1.0] - 2026-08-19

### Added

- Initial extract of the Rivulets routing core as a standalone MIT library
- Mentions, deterministic rules (keyword, regex, semantic substring, `always`), optional injected LLM fallback
- Orchestrator lock and loop guards
- Zero runtime dependencies
- CLI (`rivulet-dispatch`) and `examples/team.json`

[Unreleased]: https://github.com/jwilson411/rivulet-dispatch/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jwilson411/rivulet-dispatch/releases/tag/v0.1.0
