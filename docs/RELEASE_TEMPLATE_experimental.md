# cred_dedupe v0.1.0-experimental

> ⚠ **Experimental Release**
>
> This is an early, experimental build of the cred_dedupe tool.
> It is intended for experienced users who are comfortable with test software
> and handling plaintext credential exports.

## What’s included

- **GUI application** `creddedupe-gui` for Windows (x64)
  - Import CSV exports from:
    - Proton Pass, LastPass, Bitwarden, and more
  - Detects provider format automatically where possible
  - Runs deduplication:
    - Removes exact duplicates
    - Groups near-duplicates (same site + username, different details)
  - Lets you resolve each group with options:
    1. Keep one selected entry
    2. Keep the best / newest entry
    3. Keep all entries
    4. Skip this group
  - Exports a cleaned CSV in the chosen format

## Downloads

- `creddedupe-gui-0.1.0-experimental-win64.zip`
- `creddedupe-gui-0.1.0-experimental-win64.zip.sha256.txt`

Verify the SHA-256 checksum before running the executable.

## Security Notes

- This tool reads and writes **plaintext CSV files** containing your credentials.
- It does **not** upload any data to remote servers, but:
  - You are responsible for where these CSV files are stored.
  - You should delete the CSV exports when you are done.
- The GUI and CLI never display your passwords or TOTP secrets in cleartext;
  they are only shown in masked form.

## Known Limitations

- Currently tested primarily on:
  - Windows 10/11 (x64)
- Other platforms require running from source.
- The GUI is still under active development; expect rough edges.

## Feedback

If you hit a bug or a confusing behavior:

1. Open an issue on the GitHub repo.
2. Include:
   - OS version
   - Provider format (e.g., Proton, LastPass, Bitwarden, browser)
   - A sanitized or minimal example CSV if possible
   - What you expected vs what happened

This will help stabilize the tool before any broader release.

