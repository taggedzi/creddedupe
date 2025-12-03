Here’s a focused TODO entry just for implementing the individual plugins, assuming the architecture + canonical schema already exist and the format details live in `docs/Formats.md`:

---

### TODO: Implement provider plugins for all documented CSV formats

**Goal:** Create concrete provider plugins for each supported password manager/browser CSV format that map to/from the canonical `VaultItem` schema, using `docs/Formats.md` as the source of truth.

**Prerequisites:**

* Canonical `VaultItem` schema is defined.
* Plugin base class + registry are implemented (e.g., `BaseProviderPlugin`, `ProviderRegistry`).
* CSV format details are documented in `docs/Formats.md`.

**Tasks:**

1. **Implement plugins for each provider**

   * Create one plugin class per format, e.g.:

     * `ProtonPassPlugin`
     * `LastPassPlugin`
     * `BitwardenPlugin`
     * `DashlanePlugin`
     * `RoboFormPlugin`
     * `NordPassPlugin`
     * `ApplePasswordsPlugin` (covers Apple Passwords / Safari)
     * `KasperskyPlugin` (import schema for CSV)
     * `FirefoxPlugin`
     * `ChromiumBrowserPlugin` (Chrome, Edge, Brave, Opera)
   * For each plugin, implement:

     * `provider_type` (enum value)
     * `import_row(row: dict[str, str]) -> VaultItem`
     * `export_row(item: VaultItem) -> dict[str, str]`
     * Any provider-specific header/column metadata needed (required/optional columns, aliases, column order).

2. **Use `docs/Formats.md` as the mapping reference**

   * For each plugin:

     * Map provider-specific column names to canonical fields (`title`, `username`, `password`, `primary_url`, `notes`, `folder`, `favorite`, `totp_*`, timestamps, etc.).
     * Ensure any unmapped or provider-specific fields are stored in `VaultItem.extra`.

3. **Register all plugins**

   * Register each plugin with the central `ProviderRegistry` so they can be:

     * Used by the auto-detection logic.
     * Selected explicitly by the user.

4. **Add unit tests for each plugin**

   * For each provider:

     * Create a small sample CSV row (or rows) based on `docs/Formats.md`.
     * Test `import_row` → verify the resulting `VaultItem` fields.
     * Test `export_row` → verify the generated dict matches expected provider header/values.
     * (If feasible) test simple round-trip: `row → VaultItem → row'` with expected equivalence.

**Definition of done:**

* All listed providers have fully implemented plugins.
* Plugins are registered and discoverable via the registry.
* All plugin tests pass and basic round-trip behavior works for each format.

---
