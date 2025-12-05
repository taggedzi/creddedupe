# **CredDedupe**

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-Alpha-orange)
<!-- ![Build](https://img.shields.io/github/actions/workflow/status/taggedzi/creddedupe/tests.yml?label=Tests) -->
![Issues](https://img.shields.io/github/issues/taggedzi/creddedupe)
![Last Commit](https://img.shields.io/github/last-commit/taggedzi/creddedupe)
![Downloads](https://img.shields.io/github/downloads/taggedzi/creddedupe/total)

*A multi-provider credential deduplication and cleanup tool with CLI and Qt6 GUI interfaces.*

---

## 📌 Overview

Password managers and browsers often export CSV files containing:

* Duplicate entries (sometimes from repeated imports)
* Slight variations of the same credential
* Provider-specific field formats
* Missing or inconsistent metadata

**CredDedupe** solves these problems by:

* Importing CSV exports from multiple providers
* Normalizing entries into a canonical schema
* Automatically detecting exact duplicates
* Grouping **near-duplicates** for human review
* Allowing you to choose how duplicates are resolved
* Re-exporting a clean CSV compatible with the provider you choose
* Offering both:

  * **CLI:** `creddedupe-cli`
  * **Qt6 GUI:** `creddedupe-gui`

Ideal for users who are:

* Switching password managers
* Merging multiple devices or accounts
* Cleaning years of accumulated entries
* Translating between CSV formats

---

## 🚫 What CredDedupe Does *NOT* Do

To avoid misunderstandings:

* ❌ Does **not** upload or transmit credentials
* ❌ Does **not** encrypt CSV files (CSV is plaintext by definition)
* ❌ Does **not** replace your password manager
* ❌ Does **not** modify existing password vaults
* ❌ Does **not** guarantee compatibility with every provider (experimental software)

All processing happens **locally** and **only** on exported CSV files.

---

## ⚠️ Security Notice

> **CSV exports contain plaintext passwords, TOTP secrets, and sensitive metadata. Treat them as highly confidential.**

CredDedupe processes all data locally and never uploads or transmits your credentials.

By using CredDedupe, you accept responsibility for:

* Secure handling and deletion of CSV files
* Protecting your system environment
* Validating output before re-importing into any password manager

CredDedupe and its author(s) assume **no liability** for data loss, exposure, incorrect merges, corrupted files, or any resulting harm.

> CredDedupe is **not affiliated with any password manager**, including Proton Pass, Bitwarden, LastPass, Dashlane, Apple, Mozilla, Google, Microsoft, NordPass, RoboForm, or others.

---

## ✨ Features

### ✔ Multi-provider CSV import

Supports (where formats are documented):

* Proton Pass
* LastPass
* Bitwarden
* Dashlane
* RoboForm
* NordPass
* Apple Passwords
* Kaspersky
* Firefox
* Chromium-based browsers (Chrome, Edge, Brave, Opera)

CredDedupe is an independent open-source project. It is not affiliated with, endorsed by, or sponsored by any password manager or browser vendor, including but not limited to: Proton Pass, Bitwarden, LastPass, Dashlane, NordPass, 1Password, RoboForm, Apple Passwords, Firefox, Chrome/Chromium-based browsers, Microsoft Edge, or Opera.

All trademarks, product names, and brand names are the property of their respective owners.

### ✔ Unified canonical schema

Normalized fields:

* Title
* Username
* Password (masked)
* Primary URL
* Notes
* Folder / Tags
* TOTP
* Timestamps

### ✔ Automatic provider detection

Based on header fingerprints.

### ✔ Dedupe engine

* Removes exact duplicates automatically
* Groups near-duplicates by username + normalized URL
* Highlights differences (timestamps, notes, folder, etc.)
* All sensitive fields masked

### ✔ Interactive decision tools

**CLI & GUI options**:

* Keep one
* Keep newest/best
* Keep all
* Skip group

### ✔ Safe output formats

Re-export to any supported provider schema.

### ✔ Experimental Windows GUI builds

Portable, no installation required.

#### 🖼️ Screenshots

After selecting a CSV to de-duplicate, it auto guesses at the provider, but can still be manually overriden

![CSV Selected - Provider Selection](/docs/images/CredDedupe-GUI-Select-Provider.png)

It Automatically removes entries that are EXACT duplicates, and then presents GROUPS of entires that are ALMOST identical.
To move forward select each of the groups and direct the application as to what actions to take.

![Near Match Entry](/docs/images/CredDedupe-GUI-Show-NearMatch.png)

Here are the actions you can take, and it will give you as much information as possible without exposing passwords.

![Near Match Selection Process](/docs/images/CredDedupe-GUI-Output-Options.png)

---

## 🧱 Requirements

### For CLI/GUI from source

* Python **3.10+**
* Dependencies installed automatically:

  * PyQt6
  * PyInstaller (only for building binaries)
  * Standard Python libraries

### For GUI binary

* Windows 10 or 11
* No Python installation required, if binary release is available.

---

## 📥 Downloading CredDedupe

### 🟣 Windows GUI Binary (Recommended)

Download from:

**[https://github.com/taggedzi/creddedupe/releases](https://github.com/taggedzi/creddedupe/releases)**

Files:

* `creddedupe-gui-<version>-win64.zip`
* Optional `.sha256.txt` checksum

Extract and run — portable, no registry changes.

---

### 🟢 Install From Source

```sh
git clone https://github.com/taggedzi/creddedupe
cd creddedupe
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install -e .[dev]
```

Run tools:

```sh
creddedupe-cli --help
creddedupe-gui
```

---

## 🖥️ CLI Usage Examples

### Deduplicate a Proton Pass export

```sh
creddedupe-cli cred_export.csv
```

### Auto-merge near duplicates

```sh
creddedupe-cli cred.csv --auto-merge-near-duplicates
```

### Force provider format

```sh
creddedupe-cli cred.csv --provider lastpass
```

### Convert LastPass → Bitwarden

```sh
creddedupe-cli lp.csv -o bw.csv --provider lastpass
```

---

## 🪟 GUI Overview

1. Open CSV File
2. Automatic Provider Detection (overridable)
3. Review summary
4. Resolve near-duplicate groups
5. Export cleaned CSV

Passwords and TOTP fields are always masked.

---

## 🔌 Creating a Provider Plugin

Plugins live at:

```
src/cred_dedupe/plugins/
```

Implement:

* Provider metadata
* `import_row()` → convert CSV → VaultItem
* `export_row()` → convert VaultItem → CSV
* Register plugin
* Provide test fixtures

Document new formats in `Formats.md`.

---

## 🧪 Tests

Includes:

* Plugin import/export tests
* Detection tests
* Dedupe logic tests
* CLI end-to-end tests
* Basic GUI smoke tests

Run:

```sh
pytest
```

---

## 🧷 Versioning

* Pre-release versions use PEP 440 (e.g., `0.1.0a2`)
* Git tags follow: `v0.1.0a2`
* GitHub releases marked *Experimental*

---

## 📄 License & Legal

CredDedupe is licensed under the **MIT License**.
Full text is in `LICENSE`.

This software is provided **“AS IS”**, without warranty, and the author(s) assume **no liability** for:

* Data loss
* Incorrect merges
* Export issues
* Credential exposure
* Any resulting damages

See the full MIT license for details.

For a full list of third-party licenses, credits, and AI-assist disclosures, see  
➡️ **[docs/attributions.md](docs/ATTRIBUTIONS.md)**

---

## 🤖 Acknowledgments & Use of AI Tools

Parts of this project — including documentation, testing scaffolds, and code generation — were developed with help from **ChatGPT** and other AI-assisted tools.
All final architectural decisions and integrations were performed by the project author.
All included dependencies retain their own licenses.

Qt®, PyQt6®, Python®, PyInstaller®, and other referenced tools are trademarks of their respective owners and are not affiliated with this project.

---

## 🆘 Issues & Feedback

Submit issues at:
**[https://github.com/taggedzi/creddedupe/issues](https://github.com/taggedzi/creddedupe/issues)**
