# CredDedupe

Small helper tool to clean up Proton Pass CSV exports by merging duplicate
entries while trying to preserve as much information as possible.

The input is a Proton Pass CSV with the following columns:

`type,name,url,email,username,password,note,totp,createTime,modifyTime,vault`

The output is a CSV that keeps only the columns required for re‑import:

`name,url,email,username,password,note,totp,vault`

> ⚠️ **Warning – passwords and sensitive data**
>
> This tool operates on password manager exports. Always work on copies of your
> data, never the only original. Review results carefully before importing them
> anywhere.

> ⚠️ **No affiliation with Proton**
>
> This project and its author are **not affiliated with, endorsed by, or
> sponsored by Proton AG, Proton Pass, or any related company or product**.
> The name “CredDedupe” and references to “Proton Pass” are used only to
> describe that the tool operates on CSV exports produced by the Proton Pass
> application.

> ⚠️ **AI‑assisted project**
>
> Significant parts of this project were generated with the help of an AI
> assistant. The logic has not been audited by security professionals. Use at
> your own risk.

## License and responsibility

This project is released under the [MIT License](LICENSE).

The MIT License explicitly provides the software **“as is”**, without any
express or implied warranties, and limits the liability of the authors and
copyright holders. By using this project, you agree that:

- You are solely responsible for backing up your data.
- You are solely responsible for verifying that the output is correct.
- The authors, contributors, and maintainers are **not responsible** for any
  data loss, corruption, incorrect deduplication, security issues, or other
  problems arising from use or misuse of this tool.

## Installation

These instructions assume you already have Python 3.9+ installed.

### 1. Clone the repository

```bash
git clone https://github.com/taggedzi/creddedupe.git
cd creddedupe
```

### 2. Create and activate a virtual environment

On macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

You should now see `(.venv)` in your shell prompt.

### 3. Install the package

```bash
pip install --upgrade pip
pip install .
```

This will install `creddedupe` and its dependencies (including PyQt6).

## Usage

You can use either the CLI or the Qt6 GUI.

### CLI usage

After installation, from anywhere:

```bash
creddedupe-cli path/to/input.csv -o path/to/cleaned.csv
```

If you are running from the project directory without installing, use:

```bash
python -m cred_dedupe.core path/to/input.csv -o path/to/cleaned.csv
```

Key options:

- `-o / --output` – path for the output CSV  
  (default: `<input>_deduped.csv` in the same directory).
- `--allow-different-passwords` – allow merging entries even when passwords
  differ (more aggressive; may merge accounts across password changes).
- `--no-email-username-equivalence` – by default, the tool treats email and
  username as interchangeable login identifiers; this flag disables that.

### GUI usage

After installation:

```bash
creddedupe
```

Or from the project directory without installing:

```bash
python -m cred_dedupe.gui
```

In the GUI you can:

- Pick an input CSV (or drag & drop it onto the window).
- Choose an output CSV path (suggested automatically as `<input>_deduped.csv`).
- Decide whether to only merge entries that share the same password
  (safer, enabled by default).
- Decide whether email and username should be treated as equivalent
  login identifiers.
- Run the deduplication and see a short summary of what was done.

## How the deduplication works

This section is intentionally detailed so you can understand the logic and
decide whether it fits your needs. When in doubt, inspect the output CSV
manually before importing it anywhere.

### Input and parsing

- Expects all of the Proton Pass columns:  
  `type,name,url,email,username,password,note,totp,createTime,modifyTime,vault`.
- Internally, each row is converted into an `Entry` object that also stores:
  - `canonical_domain`: derived from `url` using standard URL parsing, with
    scheme added if missing, lower‑cased, and `www.` stripped.
  - `login_id`: a normalized identifier built from `username` and optionally
    `email`, lower‑cased.

### Grouping potential duplicates

Each `Entry` is assigned to a group using:

- `domain_or_name`: the canonical domain from `url`; if there is no URL,
  the normalized `name` is used instead.
- `login_id`: based on `username` or (by default) `username`/`email`
  equivalence.
- `password`: included in the grouping key only when the “strict passwords”
  option is enabled.

So, by default, two rows are considered potential duplicates if:

- They share the same canonical domain (or name when URL is missing).
- They share the same login identifier (username/email).
- They use the same password.

If the “allow different passwords” option is enabled, the password is not part
of the grouping key, which means entries can be merged across password changes.

Rows that lack both a usable domain/name and a login ID are kept separate to
avoid risky merges.

### Choosing the “best” entry

For each group of potential duplicates, the tool picks a preferred entry using:

1. The newest `modifyTime` (tries numeric epoch timestamps or common
   ISO‑style formats).
2. The number of non‑empty important fields (`url`, `email`, `username`,
   `password`, `note`, `totp`).

This preferred entry provides the main fields in the merged result.

### Merging data from duplicates

For each group, the tool:

- Collects all distinct values of:
  - Names, URLs, emails, usernames, passwords, TOTP secrets, and vault names.
- Keeps the preferred entry’s values as the primary ones.
- Adds any alternative values into the `note` field under a separate section:

  ```text
  Merged from duplicates:
  - Alternative names: ...
  - Alternative URLs: ...
  - Alternative emails: ...
  - Alternative usernames: ...
  - Alternative passwords: ...
  - Alternative TOTP secrets: ...
  - Original vaults: ...
  ```

- Also concatenates all distinct original notes (`note`) from the grouped
  entries, separated by blank lines.

This way, the output keeps a single row per merged set of duplicates while
preserving as much information as possible in the `note` field.

### Output format

The output CSV contains only:

```text
name,url,email,username,password,note,totp,vault
```

This format is typically suitable for re‑import into Proton Pass or other
password managers that accept CSV imports with these columns.

## Safety tips

- Always make a backup of your original Proton Pass export before running this
  tool.
- Prefer running in the default (strict password) mode first and review the
  results.
- If you change the settings (for example, allow different passwords), compare
  the results to the strict mode output.
- Consider testing with a small subset of your data to verify that the
  behavior matches your expectations.

## Building a Windows binary (local)

You can build a standalone Windows executable using [PyInstaller](https://pyinstaller.org/).
These steps are intended to be run **locally**; once built, you can manually
attach the resulting `.exe` to a GitHub release.

### Quick build using the dev extra

1. Ensure you are in your project directory and your virtual environment is active:

   ```powershell
   cd path\to\creddedupe
   .venv\Scripts\Activate.ps1
   ```

2. Install the project in editable mode with the `dev` extras (includes PyInstaller):

   ```powershell
   pip install -e .[dev]
   ```

3. Run the helper build command:

   ```powershell
   creddedupe-build-win
   ```

   This wraps PyInstaller with sensible defaults:
   - GUI-only binary (`--windowed`).
   - Name: `CredDedupe`.
   - Entry script: `run_creddedupe_gui.py` (which imports `cred_dedupe.gui`).
   - Icon: `src\cred_dedupe\assets\creddedupe.ico` (if present).

4. After a successful build, the main executable will be in:

   ```text
   dist\CredDedupe\CredDedupe.exe
   ```

5. Test the executable locally by running `CredDedupe.exe`, and if you are
   satisfied, you can zip the `dist\CredDedupe\` directory or just the `.exe`
   and upload it as an asset to your GitHub release.

### Manual PyInstaller command (optional)

If you prefer to run PyInstaller yourself, you can still use:

```powershell
pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name CredDedupe ^
  --icon src\cred_dedupe\assets\creddedupe.ico ^
  run_creddedupe_gui.py
```

## Development with Nox

This project includes a simple [Nox](https://nox.thea.codes/) configuration
for common development tasks.

Install the dev dependencies (includes Nox and PyInstaller):

```powershell
pip install -e .[dev]
```

Then you can run:

- `nox -s tests` – placeholder for the future test suite.
- `nox -s lint` – runs Ruff linting over the project.
- `nox -s lint_fix` – runs Ruff with `--fix` to automatically apply safe fixes.
- `nox -s build_win` – installs `.[dev]` into an isolated env and runs the
  Windows binary build (`creddedupe-build-win`).

You can extend `noxfile.py` over time to wire in your actual tests and
linting tools as the project grows.
