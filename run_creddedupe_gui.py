from __future__ import annotations

"""
Small wrapper script used as the PyInstaller entrypoint for the GUI build.

The Windows executable produced by ``nox -s build_win`` (or by running
``creddedupe-build-win`` directly) starts from this module, which in turn
launches the real Qt6 GUI defined in ``cred_dedupe.gui``.
"""

from cred_dedupe.gui import main


if __name__ == "__main__":
    main()
