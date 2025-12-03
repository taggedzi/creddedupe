# Todo

- Create a pluggin system so that support for other application (input/ouput) can be added in the future without major software updates. This should simply account for the fields that are exported, and the required fields to then import by the target software.
  - Use this [Cononical Internal Schema](docs/Cononical%20Internal%20Schema.md)

- Add support for following password manager exports/imports -> Documentatoin found [here](docs/Formats.md)
  - Proton Pass (csv) -> Currently implemented as only system.
  - Lastpass (csv)
  - Bitwarden (csv)
  - Dashlane (csv)
  - Roboform (csv)
  - NordPass (csv)
  - Apple Passwords (csv)
  - Kaspersky (txt)?
  - Web Browser Exports/Imports Safari, Brave, Firefox, Chrome, Edge, Opera?

Here is a clean, Codex-friendly TODO entry that captures the decision:

---

### **TODO: Implement automatic CSV provider detection with user override**

**Goal:** When a user loads a CSV file, the system should automatically identify the originating password manager or browser format based on the header row, but still allow the user to manually override the detected provider.

**Requirements:**

* Create a `detect_provider(header_columns)` function that:

  * Normalizes headers (lowercase, trim spaces, remove punctuation).
  * Compares them against known provider “fingerprints” (required + optional columns).
  * Returns `(provider_type, confidence_score, explanation)`.

* If multiple providers match, classify as **ambiguous** and default to a “Browser (Chromium-family)” group or show the top candidates.

* In the UI:

  * Display the detected provider as the default selection in a dropdown.
  * Allow the user to manually change the provider before import.
  * If detection is `UNKNOWN` or confidence is low, require manual selection.

**Deliverables:**

* Provider enum (e.g., `ProviderFormat`).
* Header fingerprint definitions for all supported providers.
* Detection logic with a scoring system.
* UI integration to present detection results and selection override.


- Add new GUI/CLI interface that displays entries that appear to be similar but not exact, force the user to chose action to merge entries and select which one is the "master" for conflicts, OR delete one of the entries OR allow manual edit of fields for entry.  This GUI should display BOTH entries AND the final merge results in a visually clear way to make it over abundantly clear what is happening, giving user warnings about ANY data that might be deleted or lost before it happens. It should function very much like a visual diff process showing the original entry, the alternate entry and allow field by field selection of what changes to apply OR selection of entire entry for merge/delete/select as master.  

- Generate report of each action taken (like a commit log) so that given the original csv and the changelog, a record of what happen could be reconstructed. The change log should not contain any sensitive or credential information, possibly only referencing row numbers so as to not emmit any data like websites, usernames, passwords, notes etc. Present the change log to the user on completion and allow saving.  Save a cryptologically secure hash with the commit log so that it can be confirmed with the correct csv if reconstruction is needed.

- ONLY Automatically delete an entry IF every relivant field is identical.  If the only difference is the time an entry was saved, but all credential information is identical for all intents and purposes it is identical. IF any of the credential fields are different present the user with the merge/delete GUI/CLI window proposed.

- Due to the fact that users already have the password fields as plain text on a file system. Follow best security practices for handeling credential information that is already plain text.

- Warn user clearly of the risk of data loss, the risks of having credentials in plain text files, the transporting, storage, etc of such activities. Have them ask their system admin, or software provider for directions, actions, or plans about how to manage such data. This applicationly deals with plain text data and providing tools that help the user de-duplicate that data. We are not responsible for how these files get used, generated, stored, transmitted, etc. We just facilitate the user in deduplicating a csv file.
