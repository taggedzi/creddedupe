from __future__ import annotations

from cred_dedupe.cli_merge import _compute_password_matches
from cred_dedupe.model import ItemType, VaultItem


def _make_item(internal_id: str | None, password: str | None) -> VaultItem:
    return VaultItem(
        item_type=ItemType.LOGIN,
        internal_id=internal_id,
        password=password or "",
    )


def test_compute_password_matches_basic() -> None:
    item1 = _make_item("a", "secret1")
    item2 = _make_item("b", "secret2")
    item3 = _make_item("c", "secret1")

    group = [item1, item2, item3]

    matches = _compute_password_matches(group)

    assert matches["a"] == ["c"]
    assert matches["c"] == ["a"]
    assert matches["b"] == []


def test_compute_password_matches_ignores_missing_ids_and_empty_passwords() -> None:
    with_id = _make_item("x", "")
    without_id = _make_item(None, "secret")

    group = [with_id, without_id]

    matches = _compute_password_matches(group)

    # Item with empty password is tracked by its internal_id but has no peers.
    assert matches["x"] == []

