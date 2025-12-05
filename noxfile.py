# SPDX-License-Identifier: MIT

from __future__ import annotations

import nox

"""
Nox sessions for development tasks.

Usage examples (from the project root, with your venv active):

    nox -s tests
    nox -s lint
    nox -s build_win

For now, tests and lint sessions are placeholders that you can extend once
you add a test suite or linting tools.
"""


@nox.session
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    session.install("-e", ".[dev]")
    session.run("pytest", *session.posargs)


@nox.session
def lint(session: nox.Session) -> None:
    """Run Ruff linting over the codebase."""
    session.install("-e", ".[dev]")
    session.run("ruff", "check", ".")


@nox.session
def lint_fix(session: nox.Session) -> None:
    """Run Ruff with --fix to automatically apply safe fixes."""
    session.install("-e", ".[dev]")
    session.run("ruff", "check", ".", "--fix")


@nox.session
def build_win(session: nox.Session) -> None:
    """
    Build a Windows GUI executable using the helper script.

    Equivalent to:
        pip install -e .[dev]
        creddedupe-build-win
    """
    session.install("-e", ".[dev]")
    session.run("creddedupe-build-win")
