# SPDX-License-Identifier: MIT

"""
Convenience launcher for the Qt6 GUI.
Running this file is equivalent to:

    python -m cred_dedupe.gui

or the installed entry point:

    creddedupe
"""

from __future__ import annotations

from cred_dedupe.gui import main


if __name__ == "__main__":
    main()
