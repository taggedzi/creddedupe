from __future__ import annotations

"""
Legacy/alternate launcher kept for convenience. This mirrors ``run_creddedupe_gui``
and simply starts the Qt6 GUI from ``cred_dedupe.gui``.
"""

from cred_dedupe.gui import main


if __name__ == "__main__":
    main()
