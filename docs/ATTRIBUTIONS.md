# Attributions & Acknowledgments

*CredDedupe — Credential Deduplication & CSV Normalization Tool*

This document provides formal attribution, credit, and disclosure for third-party technologies, libraries, licenses, and AI-assisted development used in the creation of this project.

---

## 📘 1. Project License

CredDedupe is released under the **MIT License** (see `LICENSE` file):

The MIT License governs all original source code in this repository.

---

## 🤖 2. AI-Assisted Development Disclosure

Parts of this project were developed with the assistance of AI tools such as **ChatGPT (OpenAI)** and **GitHub Copilot / Codex**.
AI assistance contributed to:

* Brainstorming and refining the canonical data schema
* Reviewing or suggesting documentation
* Drafting boilerplate or repetitive code patterns
* Providing research summaries for CSV provider formats
* Suggesting architectural patterns for the plugin system
* Drafting test plans
* Code commentary, refactoring tips, and UX prototypes

All AI-generated or AI-influenced code was **reviewed, validated, and modified** by the project author.
Final design decisions, code integration, security considerations, and all acceptance criteria were performed by a human.

This project retains full original ownership by the author(s), and no AI system holds copyright or authorship over the resulting work.

---

## 🧱 3. Third-Party Libraries and Dependencies

CredDedupe relies on the following open-source libraries and tools.
Each dependency retains its own license, copyright, and attribution
requirements.

Where possible, library names are followed by their SPDX license identifier for clarity.

### Python Language & Standard Library

* Python © Python Software Foundation
* License: **Python Software License** (`PSF-2.0`)
* Website: [https://www.python.org/](https://www.python.org/)

### PyQt6 / Qt6 Framework

* © The Qt Company Ltd.
* License: **LGPL-3.0**, **GPL-3.0**, or commercial license
* PyQt6 is provided under the **GPL / Riverbank Computing license terms**
* Website: [https://www.qt.io/](https://www.qt.io/)
* Note: CredDedupe is *not* affiliated with, endorsed by, or sponsored by The Qt Company.

### PyInstaller

* © PyInstaller Development Team
* License: **GPL-2.0-with-pyinstaller-exception**
* Website: [https://www.pyinstaller.org/](https://www.pyinstaller.org/)

### pytest (for tests)

* License: **MIT**
* Website: [https://docs.pytest.org/](https://docs.pytest.org/)

### Other Python dependencies

Additional libraries included via `pyproject.toml` or runtime imports fall under their respective OSI-approved licenses.
Each dependency may include embedded license metadata within its distribution or Python package metadata.

---

## 🔌 4. CSV Provider Research Sources

CSV formats for password managers and browsers referenced in this project were derived from:

* Public documentation from vendors where available
* Empirically derived understanding of exported CSV files
* Community knowledge
* Test fixtures and sample exports (sanitized or user-provided)

No proprietary SDKs, private APIs, or confidential materials were used.

Providers referenced include (but are not limited to):

* Proton Pass
* LastPass
* Bitwarden
* Dashlane
* RoboForm
* NordPass
* Apple Passwords
* Kaspersky Password Manager
* Firefox
* Chrome / Chromium-based browsers (Edge, Brave, Opera)

All trademarks belong to their respective owners.
CredDedupe makes **no claim of affiliation or endorsement** by any of these vendors.

---

## 🪪 5. Trademark Notice

All product names, company names, and logos mentioned in this repository are the property of their respective trademark owners.
Their use herein is for identification, compatibility explanation, and interoperability purposes only.

CredDedupe is an independent open-source project and has **no affiliation with**:

* Proton Technologies AG
* LastPass (LogMeIn / GoTo)
* Bitwarden Inc.
* Dashlane Inc.
* Siber Systems (RoboForm)
* NordPass (Nord Security)
* Apple Inc.
* Kaspersky Lab
* Mozilla Foundation
* Google LLC
* Microsoft Corporation
* Opera Software

---

## 🧭 6. Community Contributions

This project may include community-contributed code or documentation.
Contributors affirm that their submissions:

* Originate from their own work
* Do not violate employer or third-party rights
* Are submitted under the project’s MIT License

Where applicable, contributor acknowledgments appear in:

* `CONTRIBUTORS.md` (if present)
* GitHub’s contributor listings

---

## 📄 7. Notice Regarding Experimental Software

CredDedupe is currently released as **alpha-quality software**.
As permitted by the MIT License:

* It is provided *“as-is”*, without warranty
* It may contain defects
* It is intended for testing, feedback, and early evaluation only
* Users are solely responsible for safeguarding sensitive credential exports

---

## 🎉 8. Thank You

Thank you to:

* The open-source maintainers whose work makes this project possible
* Testers who provide feedback, sample exports, and bug reports
* The broader password-management and infosec communities for inspiration

Your contributions help improve the safety, reliability, and usability of this tool.
