# Contributing

## Setup

Python 3.11 or 3.12. Create a venv, then install the package and the dev extra:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Tests

```bash
make test
```

That runs `python3 -m pytest -q`. Lint is `make lint` (`ruff check` only; this repo does not run `ruff format`). CI runs ruff on 3.12 and the test suite on 3.11 and 3.12.

## Adding a rule type

1. Add a value to `RuleType` in `src/rivulet_dispatch/rules.py`.
2. Handle it in `rule_matches`. An invalid regex is already treated as no-match; keep that contract.
3. If the type is special-cased (`always` is a human-turn rule; `mention_only` never matches via dispatch), update `engine.py`.
4. Add tests under `tests/`. Cover a match, a miss, and any `speaker_id` or orchestrator-lock interaction.
5. The CLI already maps `rule_type` through `RuleType(...)`. Add an `examples/` fixture if people need to try the new type from the command line.

Do not add runtime dependencies or a vendor SDK. This library stays zero-deps.

Open a pull request against `main`. Keep secrets and `/mnt/defiant` paths out of the tree.
