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

---

If you'd like, I can also generate the exact code template for the detection engine.
