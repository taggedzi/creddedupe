# Testing cred_dedupe

This project uses `pytest` for its test suite. The tests cover:

- Provider plugins (import/export mapping for Proton Pass, LastPass, Bitwarden, and several other providers/browsers).
- Detection logic (`detect_provider`) for provider header matching.
- Core deduplication logic (exact vs near duplicates, CSV round-trips).
- CLI and build helpers (including core CLI entrypoints and Windows build script).
- CLI merge helpers for near-duplicate groups.
- A basic smoke test that the Qt GUI module (`cred_dedupe.gui_app`) imports successfully.

## Running tests

From the project root:

```bash
pytest
```

If you are using a virtual environment, ensure it is activated and the project is installed in editable mode, for example:

```bash
pip install -e .[dev]
pytest
```

The `pytest.ini` file in the project root configures pytest to look for tests in the `tests/` directory.

