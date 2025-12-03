### **TODO: Implement Plugin System for Format Conversion (Import → Canonical → Export)**

**Goal:** Build a modular plugin architecture that can define how each password manager/browser CSV format is parsed into the canonical `VaultItem` schema, and how `VaultItem` objects are exported back into specific provider formats. Here is the [Cononical Internal Schema](docs/Cononical%20Internal%20Schema.md) to use.

**Requirements:**

1. **Create a Provider Plugin Interface**

   * Define a base class (e.g., `BaseProviderPlugin`) specifying:

     * `provider_type` (enum value).
     * `can_parse(header_columns: list[str]) -> bool` (optional for detection).
     * `import_row(row: dict[str, str]) -> VaultItem`
     * `export_row(item: VaultItem) -> dict[str, str]`
     * Optional: `required_columns`, `optional_columns`, header aliases, ordering rules.

2. **Implement Plugin Registry**

   * Create a registry (e.g., `ProviderRegistry`) to:

     * Register provider plugins.
     * Fetch the plugin by provider type.
     * List available providers.
     * Support automatic lookup for import based on header detection.

3. **Create Individual Plugins for Each Provider**

   * Providers include: ProtonPass, LastPass, Bitwarden, Dashlane, RoboForm, NordPass, Apple Passwords/Safari, Kaspersky, Firefox, Chromium-based browsers.
   * Each plugin maps provider-specific CSV columns → `VaultItem`, and vice-versa.

4. **Implement Canonical Conversion Pipeline**

   * Import flow:
     **CSV → detected provider plugin → list[VaultItem] → internal dedupe/processing**
   * Export flow:
     **list[VaultItem] → selected provider plugin → provider-specific CSV**

5. **Ensure Round-Trip Capability**

   * A CSV exported through a plugin should produce valid `VaultItem` entries when re-imported.
   * Add tests for each plugin verifying:

     * Header recognition
     * Row parsing
     * Accurate export formatting

6. **Error Handling Requirements**

   * Missing required fields should produce clear exceptions.
   * Extra or unknown fields should be preserved in `VaultItem.extra` when appropriate.

7. **Extensibility**

   * New providers should be addable without modifying core logic—only the registry and plugin module should change.

**Deliverables:**

* Plugin base class and registry system.
* Plugins for all target providers.
* Unit tests for import and export workflows.
* Documentation describing how to add new provider plugins.
