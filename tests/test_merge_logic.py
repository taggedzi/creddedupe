from __future__ import annotations

from cred_dedupe.merge import MERGEABLE_FIELDS, merge_items
from cred_dedupe.model import ItemType, VaultItem


def _base_items() -> tuple[VaultItem, VaultItem]:
    a = VaultItem(
        item_type=ItemType.LOGIN,
        title="A",
        username="user_a",
        password="pass_a",
        primary_url="https://example.com/a",
        notes="note_a",
        folder="FolderA",
        favorite=False,
        totp_uri=None,
        totp_secret=None,
        tags=["tag1"],
        extra={"k1": "v1"},
    )
    b = VaultItem(
        item_type=ItemType.LOGIN,
        title="B",
        username="user_b",
        password="pass_b",
        primary_url="https://example.com/b",
        notes="note_b",
        folder="FolderB",
        favorite=True,
        totp_uri="otpauth://example",
        totp_secret="SECRET",
        tags=["tag2"],
        extra={"k2": "v2"},
    )
    return a, b


def test_merge_items_respects_decisions_and_merges_tags_and_extra() -> None:
    a, b = _base_items()

    decisions = {
        "title": {"source": "b", "value": None},
        "username": {"source": "a", "value": None},
        "password": {"source": "custom", "value": "merged_pass"},
        # primary_url not specified -> stays from a
        "notes": {"source": "b", "value": None},
        "folder": {"source": "a", "value": None},
        "favorite": {"source": "b", "value": None},
        "totp_uri": {"source": "b", "value": None},
        "totp_secret": {"source": "b", "value": None},
    }

    merged = merge_items(a, b, decisions)

    assert merged.title == "B"
    assert merged.username == "user_a"
    assert merged.password == "merged_pass"
    assert merged.primary_url == "https://example.com/a"
    assert merged.notes == "note_b"
    assert merged.folder == "FolderA"
    assert merged.favorite is True
    assert merged.totp_uri == "otpauth://example"
    assert merged.totp_secret == "SECRET"

    # Tags from both items.
    assert set(merged.tags) == {"tag1", "tag2"}
    # Extra merged with b overriding on conflicts.
    assert merged.extra["k1"] == "v1"
    assert merged.extra["k2"] == "v2"

