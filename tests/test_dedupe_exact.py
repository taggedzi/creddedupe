from __future__ import annotations

from cred_dedupe.dedupe import (
    EXACT_DUPLICATE_FIELDS,
    dedupe_items,
    is_exact_duplicate,
)
from cred_dedupe.model import ItemType, VaultItem


def _make_item(**overrides) -> VaultItem:
    base = VaultItem(
        item_type=ItemType.LOGIN,
        title="Example",
        username="user",
        password="secret",
        primary_url="https://example.com/login",
        notes="note",
        folder="Personal",
        favorite=True,
        totp_uri=None,
        totp_secret=None,
    )
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


def test_is_exact_duplicate_ignores_timestamps_and_extra() -> None:
    a = _make_item()
    b = _make_item(created_at=1234567890, updated_at=1234567899, extra={"k": "v"})

    # All fields in EXACT_DUPLICATE_FIELDS are identical.
    for field_name in EXACT_DUPLICATE_FIELDS:
        assert getattr(a, field_name) == getattr(b, field_name)

    assert is_exact_duplicate(a, b) is True


def test_is_exact_duplicate_detects_difference_in_core_fields() -> None:
    a = _make_item()
    b = _make_item(password="different")
    assert is_exact_duplicate(a, b) is False


def test_dedupe_items_removes_exact_duplicates_only() -> None:
    # Two exact duplicates and one distinct item.
    a1 = _make_item()
    a2 = _make_item()
    b = _make_item(password="different")

    result = dedupe_items([a1, a2, b])

    # One of the duplicates should be kept, the other removed_exact.
    assert len(result.kept) == 2
    assert len(result.removed_exact) == 1
    assert any(is_exact_duplicate(result.kept[0], result.kept[1]) is False for _ in [0])
    assert len(result.exact_groups) == 1


def test_dedupe_items_near_duplicates_grouped_but_not_removed() -> None:
    # Same URL and username but different notes -> near duplicates.
    i1 = _make_item(notes="one")
    i2 = _make_item(notes="two")

    result = dedupe_items([i1, i2])

    assert result.removed_exact == []
    assert len(result.kept) == 2
    assert len(result.near_duplicate_groups) == 1
    group = result.near_duplicate_groups[0]
    assert set(group) == {i1, i2}

