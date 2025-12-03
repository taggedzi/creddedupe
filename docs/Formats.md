# Data Format Information

> ⚠️ All of these can change silently between versions. For each plugin you write, I’d strongly suggest:
>
> * Detecting the manager type from the header row, **not** hard-coding column *order* only.
> * Keeping a few small “golden” sample CSVs in your repo and a test that confirms your parser still matches them.

---

## 1. LastPass

**Export CSV (vault data)**
Multiple sources (LastPass docs + migrations to Bitwarden/Keychain/etc.) agree the header row is: ([LastPass Support][1])

```text
url,username,password,totp,extra,name,grouping,fav
```

* `url` – site URL (for secure notes it’s often `http://sn`).
* `username` – login identifier.
* `password` – password.
* `totp` – TOTP seed (optional).
* `extra` – notes / additional fields.
* `name` – human-readable entry title.
* `grouping` – folder path/tag.
* `fav` – `0` / `1` for favorite.

**Generic CSV import format**

Official help: “Import data into LastPass using a generic CSV file.” ([LastPass Support][2])

* Uses the same columns as above, in that order.
* For import, **minimum required for a login** is effectively:

  * `url`, `username`, `password` (and optionally `name` so the entry isn’t just the URL).
* `extra`, `grouping`, `fav`, `totp` are optional but recognized.

**Docs / links (plain URLs):**

* `https://support.lastpass.com/help/how-do-i-import-stored-data-into-lastpass-using-a-generic-csv-file`
* `https://bitwarden.com/help/import-from-lastpass/` (shows LastPass CSV example)

---

## 2. Bitwarden

Bitwarden **explicitly documents** its CSV format for custom import, which is identical to its export format. ([Bitwarden][3])

**Individual vault CSV header:**

```text
folder,favorite,type,name,notes,fields,reprompt,login_uri,login_username,login_password,login_totp
```

* `folder` – folder name.
* `favorite` – `0` / `1`.
* `type` – `login` or `note`.
* `name` – item title.
* `notes` – note text.
* `fields` – serialized custom fields.
* `reprompt` – 0/1/… (re-prompt behavior).
* `login_uri` – URL (or domain).
* `login_username`
* `login_password`
* `login_totp` – TOTP seed.

**Minimum required values for import (per doc):** ([Bitwarden][3])

For each object, you must at least specify:

* `type` and `name`, **and** for logins, the login fields:

> “In order for the Bitwarden .csv importer to function properly, you are only required to have the following values for any given object…” and then shows that a login requires `type=login` + a `name`, with other fields allowed to be blank.

Realistically, to get a working login you need:

* `type=login`
* `name`
* `login_username`
* `login_password`
* (optionally `login_uri` if you care about URL matching)

**Docs / links:**

* `https://bitwarden.com/help/condition-bitwarden-import/`

---

## 3. Dashlane

Dashlane’s documentation points you to a downloadable CSV **template** for import and says to paste data into matching columns. ([Dashlane][4])

We don’t get the column list from that page directly, but a Microsoft Answers thread shows the **export** CSV header from Dashlane: ([Microsoft Learn][5])

**Export CSV header (logins):**

```text
"Name","Website URL","Username","Email","Secondary Login","Password","Comment"
```

* `Name` – entry title.
* `Website URL` – URL.
* `Username` – usually primary login id.
* `Email` – separate email field.
* `Secondary Login` – extra login id.
* `Password`
* `Comment` – notes.

**Dashlane CSV template (import)**

Based on the official “Import my data using the Dashlane CSV template” article: ([Dashlane][4])

* There is a **`Type`** column where you put `Login` or `Secure Note` for every row.
* There is a **`collections`** column; “extra columns from the exported CSV [go] after the `collections` column… and will be imported to the login’s Note section.”

So the **core Dashlane template columns, in order, are roughly:**

```text
Type,Name,Website URL,Username,Email,Secondary Login,Password,Comment,collections
[+ any extra columns after collections]
```

Because Dashlane does not print this as text anywhere (the template is a downloadable CSV), I’d treat this as **strongly inferred, not canonical**. For your plugin, I’d:

* Map by header **names**, not by position.
* Require at least:

  * `Type = Login`
  * `Name`
  * `Website URL`
  * `Password`
  * and either `Username` or `Email`.

**Docs / links:**

* `https://support.dashlane.com/hc/en-us/articles/12843960410898-Import-my-data-using-the-Dashlane-CSV-template`

---

## 4. RoboForm

RoboForm has good info for **import** format, and the community has shown current **export** headers.

### Import CSV format (into RoboForm)

Official import article: ([help.roboform.com][6])

RoboForm expects these fields **in this order**:

```text
Name,URL,Login,Pwd,Note,Folder
```

* `Name` – login title.
* `URL` – sign-in page.
* `Login` – username.
* `Pwd` – password.
* `Note` – notes (optional).
* `Folder` – destination folder (optional).

These are required for a “properly formatted” CSV import.

### Export CSV format (from RoboForm)

A Bitwarden migration thread shows a current RoboForm export header line: ([Bitwarden Community Forums][7])

```text
Name,URL,MatchUrl,Login,Password,Note,Folder,RfFieldsV2
```

So for your plugin:

* **Import to RoboForm**: generate the **simpler 6-column format** (`Name,URL,Login,Pwd,Note,Folder`), leaving unused fields blank as needed.
* **Export from RoboForm**: expect the richer 8-column format as above and ignore `MatchUrl` and `RfFieldsV2` if you don’t care.

**Docs / links:**

* `https://help.roboform.com/hc/en-us/articles/4423305900685-How-to-Import-from-a-CSV`
* `https://help.roboform.com/hc/en-us/articles/230425008-How-to-export-your-RoboForm-logins-into-a-CSV-file`

---

## 5. NordPass

NordPass publishes a **CSV template** for imports; NordPass confirms that you must convert Kaspersky/text exports into this template for CSV import. ([support.nordpass.com][8])

The template header is:

```text
name,url,username,password,note,cardholdername,cardnumber,cvc,expirydate,zipcode,folder,full_name,phone_number,email,address1,address2,city,country,state
```

For **website logins**, the relevant subset is:

* `name`
* `url`
* `username`
* `password`
* `note` (optional)
* `folder` (optional)

Cards and identities use the remaining fields.

**Minimum required for login import (practically):**

* `name`
* `url`
* `username`
* `password`

NordPass’ help around this template: ([support.nordpass.com][9])

**Docs / links:**

* `https://support.nordpass.com/hc/en-us/articles/360013931137-How-to-organize-CSV-file-for-import-to-NordPass` (linked from their Kaspersky and generic CSV guides)
* Template direct: the `nordpass-template.csv` referenced by that article

---

## 6. Apple Passwords / Safari (Apple ecosystem)

This is the new **Apple Passwords** app on macOS/iOS, plus Safari’s password export/import. Apple doesn’t fully spell out the schema, but Apple discussions, third-party docs, and export samples all show the same header. ([WebNots][10])

**CSV header (current Apple Passwords / Safari):**

```text
Title,URL,Username,Password,Notes,OTPAuth
```

* `Title` – entry name.
* `URL`
* `Username`
* `Password`
* `Notes` – optional.
* `OTPAuth` – otpauth:// URI for TOTP (optional).

Safari/Passwords both export CSV in this format and expect **the same** for import.

**Minimum for import:**

* You must include **all header labels** exactly as shown.
* At minimum, for a usable login:

  * `Title`, `URL`, `Username`, `Password` should be non-empty.

This is confirmed by Apple support threads and migration guides (1Password, Dropbox, etc.), where the fix for import errors is “add the header row `Title,URL,Username,Password,Notes,OTPAuth` and map your data to those columns.” ([Apple Support Community][11])

**Docs / links:**

* Apple: `https://support.apple.com/guide/iphone/import-passwords-iph984b8ac1f/ios`
* Safari passwords/help articles e.g. WebNots and others:

  * `https://www.webnots.com/how-to-import-export-and-manage-passwords-in-safari-mac/`

---

## 7. Kaspersky Password Manager

Kaspersky is a bit annoying:

* **Export**: current versions export either:

  * An **encrypted EDB** backup; or
  * A **plain text file** (for printing) — *not* CSV. ([Kaspersky Support][12])
* **Import**: they **do** support importing from CSV, but the CSV is expected to be in the format exported by other managers (LastPass, NordPass template, etc.). ([Kaspersky Support][13])

A Kaspersky forum thread in Russian gives a “formal structure for import via CSV” as: ([Kaspersky Support Forum][14])

```text
"Account","Login","Password","Url"
```

So for **Kaspersky CSV import** you can assume:

* Header row (case-sensitive as shown): `Account,Login,Password,Url`
* Minimum required:

  * `Account` – name/title.
  * `Login` – username.
  * `Password`
  * `Url`

Because Kaspersky **does not** export CSV, your de-duper plugin will only need to:

* **Export to Kaspersky** as that 4-column CSV if you want to support import into KPM.
* **Import from Kaspersky** will likely have to parse their plain-text export, **not** CSV, unless the user already converted it via some external tooling.

**Docs / links:**

* `https://support.kaspersky.com/kpm/win9.2/en-US/130515.htm` (import/export overview)
* Community note about the CSV structure:

  * `https://forum.kaspersky.com/topic/kaspersky-pasword-manager-проблемы-импорта-23152/`

---

## 8. Browser CSV formats

### 8.1 Chrome / Google Password Manager

Officially, Chrome/Google Password Manager export passwords as CSV with this header: ([Stack Overflow][15])

```text
name,url,username,password
```

Some variants (Google Password Manager) add `note` at the end:

```text
name,url,username,password,note
```

* `name` – title (often host or site name).
* `url`
* `username`
* `password`
* `note` – optional.

Chrome’s import expects **at least** these four columns; extra columns are ignored.

**Docs / links:**

* `https://support.google.com/chrome/answer/95606?hl=en` (general passwords help)
* Example article: `https://www.webnots.com/how-to-import-and-export-passwords-in-chrome/`

### 8.2 Microsoft Edge (Chromium)

Edge uses **the same CSV schema** as Chrome for importing and exporting passwords. A Microsoft Q&A answer shows a script that exports to CSV and remarks: “Exports everything into a CSV in the format Edge can re-import: `name,url,username,password`.” ([Microsoft Learn][16])

So:

```text
name,url,username,password
```

Minimum required: all four.

### 8.3 Brave

Brave is also Chromium-based and uses the same schema. Multiple Brave community threads and migration guides treat `name,url,username,password` as the canonical format. ([forum.vivaldi.net][17])

Assume:

```text
name,url,username,password
```

### 8.4 Opera

Opera’s password export/import is also Chromium-style.

A user report on Opera 50:

> “It only saves `name,url,username,password` as [the] first cell in the spreadsheet.” ([Opera forums][18])

So export header and import schema:

```text
name,url,username,password
```

Same minimum requirements.

### 8.5 Firefox

Firefox’s password manager (`about:logins`) exports CSV with a richer schema (including metadata). Commonly documented header: ([winaero.com][19])

```text
url,username,password,httpRealm,formActionOrigin,guid,timeCreated,timeLastUsed,timePasswordChanged
```

* `url` – origin where the login applies.
* `username`
* `password`
* `httpRealm` – for HTTP auth.
* `formActionOrigin` – where the form posts.
* `guid` – internal UUID.
* `time*` – timestamps (epoch ms).

For **import**, Firefox only really needs the first three (`url`,`username`,`password`); other fields are optional.

---

### 8.6 Safari / Apple Passwords (as browser)

This is the same CSV format described in section 6:

```text
Title,URL,Username,Password,Notes,OTPAuth
```

Safari exports passwords from iCloud Keychain in this format and expects identical columns for import. ([WebNots][10])

Minimum for import: non-empty `Title`, `URL`, `Username`, `Password`.

---

## 9. Apple Passwords (stand-alone app) vs Safari

On macOS Sequoia and iOS 18, Apple introduces **Passwords.app**, but under the hood, the CSV format remains the same:

```text
Title,URL,Username,Password,Notes,OTPAuth
```

Apple discussions and external blogs explicitly state that this is the format the Passwords app both exports and expects for import. ([Apple Support Community][11])

So you can treat Safari and Apple Passwords as a **single plugin** in your app.

---

## 10. Summary: practical minimums for each plugin

Here’s a compact checklist of the **minimum fields you should assume are required** to generate an import-able CSV for each system:

* **LastPass**

  * Required: `url`, `username`, `password`
  * Recommended: also `name`
  * Header: `url,username,password,totp,extra,name,grouping,fav`

* **Bitwarden (individual CSV)**

  * Required: `type=login`, `name`
  * For working login: add `login_uri`, `login_username`, `login_password`
  * Header: `folder,favorite,type,name,notes,fields,reprompt,login_uri,login_username,login_password,login_totp`

* **Dashlane**

  * Required (practical): `Type=Login`, `Name`, `Website URL`, `Password`, plus `Username` or `Email`
  * Template core: `Type,Name,Website URL,Username,Email,Secondary Login,Password,Comment,collections`

* **RoboForm**

  * Import header: `Name,URL,Login,Pwd,Note,Folder`
  * Required: `Name`, `URL`, `Login`, `Pwd` (others optional)
  * Export header you’ll see: `Name,URL,MatchUrl,Login,Password,Note,Folder,RfFieldsV2`

* **NordPass**

  * Header: `name,url,username,password,note,cardholdername,cardnumber,cvc,expirydate,zipcode,folder,full_name,phone_number,email,address1,address2,city,country,state`
  * Required for a basic login: `name`, `url`, `username`, `password`

* **Apple Passwords / Safari**

  * Header: `Title,URL,Username,Password,Notes,OTPAuth`
  * Required for login: `Title`, `URL`, `Username`, `Password`

* **Kaspersky Password Manager (CSV import)**

  * Header: `Account,Login,Password,Url`
  * Required: all four (this is the whole schema)

* **Chrome / Edge / Brave / Opera**

  * Header: `name,url,username,password` (optionally `note` in some Google contexts)
  * Required: all four fields for import

* **Firefox**

  * Header: `url,username,password,httpRealm,formActionOrigin,guid,timeCreated,timeLastUsed,timePasswordChanged`
  * Required: `url`, `username`, `password` (others optional)

---

[1]: https://support.lastpass.com/s/question/0D5TP0000055sm60AA/exported-data-csv-is-empty?language=en_US&utm_source=chatgpt.com "exported data, CSV is empty"
[2]: https://support.lastpass.com/help/how-do-i-import-stored-data-into-lastpass-using-a-generic-csv-file?utm_source=chatgpt.com "Import data into LastPass using a generic CSV file"
[3]: https://bitwarden.com/help/condition-bitwarden-import/ "Import from a Custom File | Bitwarden"
[4]: https://support.dashlane.com/hc/en-us/articles/12843960410898-Import-my-data-using-the-Dashlane-CSV-template "Import my data using the Dashlane CSV template – Dashlane"
[5]: https://learn.microsoft.com/en-us/answers/questions/5117326/excel-keeps-removing-all-quote-marks-in-my-csv-fil?utm_source=chatgpt.com "Excel keeps removing all quote marks in my csv file"
[6]: https://help.roboform.com/hc/en-us/articles/4423305900685-How-to-Import-from-a-CSV?utm_source=chatgpt.com "How to Import from a CSV"
[7]: https://community.bitwarden.com/t/import-from-roboform-unsuccessful/85050?utm_source=chatgpt.com "Import from Roboform unsuccessful - Password Manager"
[8]: https://support.nordpass.com/hc/en-us/articles/360013931117-How-to-export-passwords-from-Kaspersky-Password-Manager?utm_source=chatgpt.com "How to export passwords from Kaspersky ..."
[9]: https://support.nordpass.com/hc/en-us/articles/360002377217-How-to-organize-CSV-file-for-import-to-NordPass "How to organize CSV file for import to NordPass – NordPass"
[10]: https://www.webnots.com/how-to-import-export-and-manage-passwords-in-safari-mac/?utm_source=chatgpt.com "How to Import, Export and Manage Passwords in Safari Mac?"
[11]: https://discussions.apple.com/thread/255759674?utm_source=chatgpt.com "How to fix password import errors on Appl…"
[12]: https://support.kaspersky.com/kpc/1.0/en-us/232804.htm?utm_source=chatgpt.com "How to import and export data"
[13]: https://support.kaspersky.com/kpm/win9.2/en-US/130515.htm?utm_source=chatgpt.com "Import and export data"
[14]: https://forum.kaspersky.com/topic/kaspersky-pasword-manager-%D0%BF%D1%80%D0%BE%D0%B1%D0%BB%D0%B5%D0%BC%D1%8B-%D0%B8%D0%BC%D0%BF%D0%BE%D1%80%D1%82%D0%B0-23152/?utm_source=chatgpt.com "Kaspersky pasword manager проблемы импорта"
[15]: https://stackoverflow.com/questions/56917140/chrome-password-manager-how-to-add-password-manually?utm_source=chatgpt.com "Chrome Password Manager: How to add ..."
[16]: https://learn.microsoft.com/en-us/answers/questions/5520908/all-of-my-edge-passwords-have-disappeared?utm_source=chatgpt.com "All of my edge passwords have disappeared."
[17]: https://forum.vivaldi.net/topic/109369/cant-import-passwords?utm_source=chatgpt.com "cant import passwords - Vivaldi Forum"
[18]: https://forums.opera.com/topic/24549/help-please-opera-50-does-not-export-passwords?utm_source=chatgpt.com "Help, please: Opera 50 does not export passwords."
[19]: https://winaero.com/export-saved-logins-and-passwords-to-csv-file-in-firefox/?utm_source=chatgpt.com "Export Saved Logins and Passwords to CSV File in Firefox"
