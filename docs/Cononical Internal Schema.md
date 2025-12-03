# Cononical Internal Schema

This was user requested and then assembled by OpenAI ChatGPT 5.1. Then user reviewed.

---

## 1. Conceptual canonical schema

Think of each row as a generic **vault item**, but you’ll use mostly `login` items for now.

### Core identity & type

* `item_type` – `"login" | "note" | "card" | "identity" | "other"`

  * Covers Bitwarden types, Dashlane types, NordPass identities/cards, etc.
* `source` – string like `"protonpass"`, `"lastpass"`, `"bitwarden"`, `"firefox"`, etc.
* `source_id` – provider’s internal id/guid if present (`guid` in Firefox, etc.).
* `internal_id` – your own UUID if you like (not strictly required but handy).

### Human-facing info

* `title` – item name:

  * `name` (LastPass, Bitwarden, NordPass), `Name` (Dashlane, RoboForm), `Title` (Apple), etc.
* `username` – primary login identifier:

  * `username`, `login_username`, `Login`, `Login`, `Username`, etc.
* `password` – the password.

### URL / domain

* `primary_url` – main login URL (or origin).

  * `url`/`Website URL`/`login_uri`/`URL`/`Url`.
* `secondary_urls` – list of additional URLs/URIs:

  * e.g. multiple `login_uri` entries in Bitwarden, Dashlane secondary URL, Chrome “additional sites” later, etc.
* (optional derived) `normalized_domain` – you can compute this from `primary_url` and not store it, but it’s great for dedupe.

### Notes & freeform

* `notes` – merged notes/comments:

  * `extra` (LastPass), `notes` (Bitwarden), `Comment` (Dashlane), `Note` (RoboForm), `note` (NordPass), `Notes` (Apple), etc.

### Organization & flags

* `folder` – primary folder / path string:

  * `grouping` (LastPass), `folder` (Bitwarden, NordPass), `Folder` (RoboForm), etc.
* `tags` – extra labels if you want (some systems don’t support them natively, but you can map multi-folder paths, categories, etc. into here).
* `favorite` – bool:

  * `fav` (LastPass), `favorite` (Bitwarden), `is_favorite` equivalents elsewhere.

### OTP / TOTP

* `totp_uri` – full `otpauth://` URI when available:

  * `OTPAuth` (Apple Passwords), NordPass/Bitwarden when they export it in URI form, etc.
* `totp_secret` – raw secret if that’s all you have:

  * `totp` (LastPass), `login_totp` (Bitwarden), etc.

### Timestamps (optional but nice)

Recommended canonical format: Epoch (ms) internally + convert to ISO only when exporting.

Internally all records should be kept as Epoch times (ms). When exporting ISO should be the preffered format UNLESS the target application requires Epoc.

* `created_at` – epoch ms or ISO string.

  * `timeCreated` (Firefox), etc.
* `updated_at` – last modified / last used.

  * `timePasswordChanged` / `timeLastUsed` (Firefox), etc.

### Provider-specific / future-proofing

* `extra` – `dict[str, str]` for **anything you don’t want to lose**, but don’t need for dedupe/import:

  * `httpRealm`, `formActionOrigin`, `MatchUrl`, `RfFieldsV2`, custom fields, etc.

---

## 2. Python `dataclass` for internal use

Here’s a concrete version you can literally paste into your project:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict


class ItemType(str, Enum):
    LOGIN = "login"
    NOTE = "note"
    CARD = "card"
    IDENTITY = "identity"
    OTHER = "other"


@dataclass
class VaultItem:
    # Identity / provenance
    item_type: ItemType = ItemType.LOGIN
    internal_id: Optional[str] = None       # your own UUID or similar
    source: Optional[str] = None            # "protonpass", "lastpass", "bitwarden", "firefox", etc.
    source_id: Optional[str] = None         # provider GUID / id if available

    # Core login fields
    title: str = ""
    username: str = ""
    password: str = ""

    # URL / site info
    primary_url: Optional[str] = None
    secondary_urls: List[str] = field(default_factory=list)

    # Human notes / description
    notes: str = ""

    # Organization / flags
    folder: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    favorite: bool = False

    # OTP / 2FA
    totp_uri: Optional[str] = None          # full otpauth:// URI if available
    totp_secret: Optional[str] = None       # raw shared secret if that’s all we have

    # Timestamps (epoch ms or ISO8601; pick one convention project-wide)
    created_at: Optional[int]  # epoch ms
    updated_at: Optional[int]  # epoch ms

    # Catch-all for provider-specific data
    extra: Dict[str, str] = field(default_factory=dict)
```

### Justifications

* **Covers every column** listed:

  * `name`, `url`, `username`, `password`, `extra/notes`, `folder/grouping`, `fav/favorite`, `totp/OTPAuth`, provider `guid`/`id`, etc.
* You can write one plugin per provider doing:

  * **Import**: (CSV row → `VaultItem`)
  * **Export**: (`VaultItem` → provider-specific row)
* Dedupe logic can work entirely on `VaultItem`:

  * e.g. `(normalized_domain, username, password)` as a strong key candidate, plus fuzzy variants.

---

## 3. Optional: canonical internal CSV layout

An **internal, provider-agnostic CSV** format for debugging or user-facing “generic” exports:

```text
internal_id,
source,source_id,
item_type,
title,username,password,
primary_url,secondary_urls,
notes,
folder,tags,favorite,
totp_uri,totp_secret,
created_at,updated_at,
extra_json
```

* `secondary_urls` – pipe- or semicolon-separated URL list.
* `tags` – pipe-separated tags.
* `extra_json` – JSON-encoded `extra` dict.

This gives:

* A simple intermediary format if you ever want “import/export generic CSV”.
* A way to add regression-test fixtures: an internal-CSV file that you can round-trip through each plugin.
