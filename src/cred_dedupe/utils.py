from __future__ import annotations

import time
from typing import Optional
from urllib.parse import urlparse


def now_epoch_ms() -> int:
    """Return current time in UTC as epoch milliseconds."""
    return int(time.time() * 1000)


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Normalize a URL for comparison and dedupe purposes.

    - If ``url`` is None or empty, return as-is.
    - Lowercase scheme and hostname.
    - Strip a trailing slash from the path (except for bare ``"/"``).
    - Preserve path and query if present.
    """
    if not url:
        return url

    parsed = urlparse(url)
    if not parsed.scheme and not parsed.netloc:
        # Not a full URL; treat as a domain-ish string and just normalize case.
        return url.strip().lower()

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or ""
    if path.endswith("/") and path != "/":
        path = path[:-1]

    normalized = f"{scheme}://{netloc}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized


def clone_with_updates(item, **fields):
    """Return a shallow copy of ``item`` (a dataclass) with some fields updated.

    This is a thin wrapper around :func:`dataclasses.replace` to keep call
    sites simple and explicit without importing :mod:`dataclasses` everywhere.
    """
    from dataclasses import replace

    return replace(item, **fields)


__all__ = ["now_epoch_ms", "normalize_url", "clone_with_updates"]

