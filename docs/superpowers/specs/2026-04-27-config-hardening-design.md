# InboxReport Config Hardening Design

## Summary

InboxReport currently works as a minimal prototype, but startup behavior is brittle and the configuration story is inconsistent. The first upgrade slice will harden configuration parsing, normalize file-path defaults, improve user-facing runtime errors, and align documentation with the actual runtime model.

This is intentionally a narrow change. The Gmail fetch flow, digest prompt, and model interaction stay materially the same in this pass.

## Problem Statement

The current application has four operational weaknesses:

1. Configuration is parsed ad hoc inside `main.py` and `gmail_client.py`, so invalid or missing values fail late and inconsistently.
2. Runtime defaults do not match the documented setup. `README.md` and `.env.example` assume a `data/` directory pattern, while `gmail_client.py` defaults to `credentials.json` and `token.json` in the working directory.
3. File output behavior is brittle. `main.py` writes the digest directly and does not create parent directories for the output path.
4. Generated and secret-adjacent files are easy to leave untracked or accidentally stage because the repository does not have a standard `.gitignore`.

## Goals

- Centralize environment parsing and validation in one module.
- Introduce a coherent path model built around a single `DATA_DIR` setting.
- Make local and Docker usage work from the same config shape.
- Fail early with readable error messages and non-zero exit codes.
- Add tests that lock in config derivation and startup error behavior.
- Align `README.md` and `.env.example` with the implemented runtime behavior.

## Non-Goals

- No change to digest content strategy or prompt wording.
- No change to Gmail query behavior beyond using validated config values.
- No body extraction, label analysis, retries, structured logging, or scheduling work.
- No broad architecture rewrite into service classes or package layout changes.

## Proposed Design

### 1. Add a validated config module

Create `config.py` as the single place that translates environment variables into a validated application configuration object.

The module will expose:

- `AppConfig`: a small dataclass containing all runtime settings.
- `ConfigError`: an exception for invalid or missing configuration.
- `load_config(env=None)`: reads environment values, validates them, and returns `AppConfig`.

`load_config()` will validate:

- `OPENAI_API_KEY` is present and non-empty.
- `MAX_EMAILS` is a positive integer.
- `OAUTH_PORT` is a valid integer port.
- Explicit path overrides are non-empty when provided.

### 2. Normalize file-path defaults around `DATA_DIR`

The runtime path model will use `DATA_DIR` as the base path for generated and credential-backed files.

Default path behavior:

- `DATA_DIR`: defaults to `data`
- `GOOGLE_CREDENTIALS_FILE`: defaults to `<DATA_DIR>/credentials.json`
- `GOOGLE_TOKEN_FILE`: defaults to `<DATA_DIR>/token.json`
- `OUTPUT_FILE`: defaults to `<DATA_DIR>/daily_digest.md`

Override precedence:

1. Explicit file path env vars win.
2. Otherwise, derive the file path from `DATA_DIR`.
3. Otherwise, use the hardcoded default `data`.

This keeps local runs simple and also works in Docker if the container mounts a host directory at `/app/data`.

### 3. Make the runtime wire through validated config

`main.py` will:

- call `load_dotenv()`
- call `load_config()`
- create the parent directory for the configured output path
- pass validated values into the Gmail and summarizer layers
- print the digest only after the full flow succeeds

`gmail_client.py` will stop reading auth file locations and OAuth settings from the environment during normal execution. `get_gmail_service()` will accept explicit settings from `AppConfig`, and `main.py` will pass those values directly.

`summarizer.py` will continue to own digest generation, but `main.py` will pass the selected model explicitly instead of relying on another implicit env read.

### 4. Improve user-facing runtime errors

Startup and runtime failures will become readable without exposing a traceback for expected operator errors.

`main.py` will return a non-zero exit code and print a concise stderr message for:

- invalid or missing configuration
- missing Google OAuth client file
- Gmail setup or fetch failures
- digest generation failures
- digest file write failures

This pass will not add structured logging. Plain stderr messages are sufficient.

### 5. Add repository hygiene for generated files

Add a `.gitignore` that covers:

- `.env`
- `__pycache__/`
- `*.pyc`
- `data/`

The goal is to keep generated digests, OAuth tokens, and local Python cache files out of normal git workflows.

## File-Level Changes

- Create `config.py`
- Create `test_config.py`
- Create `test_main.py`
- Modify `main.py`
- Modify `gmail_client.py` to accept explicit config inputs
- Create `.gitignore`
- Modify `.env.example`
- Modify `README.md`

## Testing Strategy

The change will be developed with test-first coverage for new behavior.

### Config tests

Add tests for:

- required `OPENAI_API_KEY`
- default derivation from `DATA_DIR`
- explicit file path overrides
- invalid `MAX_EMAILS`
- invalid `OAUTH_PORT`

### Main-flow tests

Add tests for:

- output parent directory creation before digest write
- readable failure on config validation errors
- readable failure on Gmail setup or fetch errors
- readable failure on digest generation errors

### Existing test stability

The current extraction and summarizer behavior must remain unchanged. Existing tests stay green, and any test edits are limited to mechanical call-site updates caused by explicit parameter passing.

## Compatibility Notes

- Existing users who already set `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_TOKEN_FILE`, or `OUTPUT_FILE` will keep working because explicit overrides remain supported.
- Users following the documented `data/` flow will now match the runtime defaults instead of depending on `.env.example` to fix the mismatch.
- Docker instructions will shift to mounting the host `data/` directory into `/app/data` so the same relative defaults work inside and outside the container.

## Risks and Mitigations

- Risk: changing path defaults could surprise users who relied on the old working-directory defaults.
  Mitigation: explicit env overrides remain valid, and documentation will call out the new default path model.

- Risk: broad exception handling could hide programming mistakes.
  Mitigation: only expected application-boundary failures are caught and rendered as user-facing messages; tests exercise those boundaries.

- Risk: changing `get_gmail_service()` signatures could break tests or future callers.
  Mitigation: keep the function interface small and preserve compatibility where it costs little.

## Success Criteria

This slice is complete when:

- all runtime settings are loaded through `config.py`
- config errors fail early with readable messages
- local and Docker docs describe the same path model
- the app creates required output directories
- automated tests cover the new config and startup behavior
