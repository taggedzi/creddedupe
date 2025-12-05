from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from . import __version__ as APP_VERSION
from .changelog import ChangeLog, log_discard_manual, log_manual_merge, log_removed_exact, save_changelog, sha256_file
from .cli import _ensure_internal_ids, _export_items_to_csv
from .cli_merge import recompute_final_items, score_vault_item
from .core import SECURITY_WARNING
from .dedupe import DedupeResult, dedupe_items
from .detection import DetectionResult, detect_provider
from .model import VaultItem
from .plugins import ProviderFormat, get_registry, register_all_plugins


APP_NAME = "CredDedupe"
APP_REPO_URL = "https://github.com/taggedzi/creddedupe"


def _mask_secret(value: str | None) -> str:
    if not value:
        return "(empty)"
    return f"******** (len={len(value)})"


def _format_timestamp(epoch_ms: int | None) -> str:
    if not epoch_ms:
        return "(unknown)"
    try:
        from datetime import datetime, timezone

        dt = datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return "(unknown)"


def _compute_password_matches(group: List[VaultItem]) -> Dict[int, List[int]]:
    """
    For a group of VaultItem, compute which entries share the same password.

    Returns:
        index -> list of other indices in the group that have
                 the exact same password (excluding self).
    """
    from collections import defaultdict

    pw_to_indices: Dict[Optional[str], List[int]] = defaultdict(list)
    for idx, item in enumerate(group):
        pw = item.password or None
        pw_to_indices[pw].append(idx)

    matches: Dict[int, List[int]] = {}
    for idx, item in enumerate(group):
        pw = item.password or None
        indices = [i for i in pw_to_indices.get(pw, []) if i != idx]
        matches[idx] = indices
    return matches


def _safe_display_notes(notes: Optional[str], max_len: int = 60) -> str:
    if not notes:
        return "(empty)"
    stripped = notes.strip()
    if len(stripped) <= max_len:
        return stripped
    return stripped[: max_len - 3] + "..."


class GroupDecisionType(str, Enum):
    KEEP_ONE_SELECTED = "keep_one_selected"
    KEEP_BEST = "keep_best"
    KEEP_ALL = "keep_all"
    SKIP = "skip"


@dataclass
class GroupDecision:
    decision_type: GroupDecisionType
    selected_index: Optional[int] = None  # 0-based index in group


class ProviderSelectionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        headers: List[str],
        detection: DetectionResult,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Provider")
        self._chosen: Optional[ProviderFormat] = None

        layout = QtWidgets.QVBoxLayout(self)

        info = QtWidgets.QLabel(self)
        if detection.provider is ProviderFormat.UNKNOWN:
            info.setText(
                "Unable to confidently detect provider from CSV headers.\n"
                "Please choose the correct provider format."
            )
        else:
            info.setText(
                f"Detected provider: {detection.provider.value} "
                f"(confidence {detection.confidence:.2f}).\n"
                "You can keep this choice or select a different provider."
            )
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addWidget(QtWidgets.QLabel("Provider:", self))
        self.combo = QtWidgets.QComboBox(self)
        for fmt in ProviderFormat:
            if fmt is ProviderFormat.UNKNOWN:
                continue
            self.combo.addItem(fmt.value, fmt)
        layout.addWidget(self.combo)

        # Pre-select detected provider when possible.
        if detection.provider is not ProviderFormat.UNKNOWN:
            idx = self.combo.findData(detection.provider)
            if idx >= 0:
                self.combo.setCurrentIndex(idx)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_provider(self) -> Optional[ProviderFormat]:
        return self._chosen

    def accept(self) -> None:  # type: ignore[override]
        data = self.combo.currentData()
        if not isinstance(data, ProviderFormat):
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid selection",
                "Please choose a valid provider.",
            )
            return
        self._chosen = data
        super().accept()


class GroupResolutionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        group_index: int,
        group: List[VaultItem],
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Resolve Near-Duplicate Group #{group_index}")
        self._group = group
        self.decision: Optional[GroupDecision] = None

        layout = QtWidgets.QVBoxLayout(self)

        if not group:
            label = QtWidgets.QLabel("This group is empty.", self)
            layout.addWidget(label)
            buttons = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.StandardButton.Close,
                parent=self,
            )
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)
            return

        example = group[0]
        site = example.primary_url or "(no URL)"
        username = example.username or "(no username)"

        site_label = QtWidgets.QLabel(f"Site: {site}", self)
        user_label = QtWidgets.QLabel(f"Username: {username}", self)
        layout.addWidget(site_label)
        layout.addWidget(user_label)

        layout.addSpacing(8)

        best_item = max(group, key=score_vault_item)
        pw_matches = _compute_password_matches(group)

        table = QtWidgets.QTableWidget(self)
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["#", "Title", "Password", "Notes", "First created", "Last changed"]
        )
        table.setRowCount(len(group))
        table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )

        for idx, item in enumerate(group):
            is_best = item is best_item
            title = item.title or "(no title)"
            if is_best:
                title = f"{title} [RECOMMENDED]"

            pw = item.password or ""
            pw_display = _mask_secret(pw)
            same_indices = pw_matches.get(idx, [])
            if pw:
                if same_indices:
                    # Convert to 1-based indices for display.
                    entries = ",".join(str(i + 1) for i in sorted(same_indices))
                    pw_display = (
                        f"{pw_display}  [same password as entries {entries}]"
                    )
                else:
                    pw_display = (
                        f"{pw_display}  [unique password in this group]"
                    )
            else:
                pw_display = "Password: (empty)"

            notes_preview = _safe_display_notes(item.notes)

            created_str = _format_timestamp(item.created_at)
            updated_str = _format_timestamp(item.updated_at)

            row_values = [
                str(idx + 1),
                title,
                pw_display,
                notes_preview,
                created_str,
                updated_str,
            ]
            for col, text in enumerate(row_values):
                item_widget = QtWidgets.QTableWidgetItem(text)
                if col == 0:
                    item_widget.setFlags(
                        item_widget.flags()
                        & ~QtCore.Qt.ItemFlag.ItemIsEditable
                    )
                table.setItem(idx, col, item_widget)

        table.resizeColumnsToContents()
        layout.addWidget(table)
        self._table = table

        layout.addSpacing(8)

        # Decision controls.
        self.keep_selected_radio = QtWidgets.QRadioButton(
            "Same account – keep the entry I selected", self
        )
        self.keep_best_radio = QtWidgets.QRadioButton(
            "Same account – keep the BEST/NEWEST entry", self
        )
        self.keep_all_radio = QtWidgets.QRadioButton(
            "Different accounts – keep ALL entries", self
        )
        self.skip_radio = QtWidgets.QRadioButton(
            "Skip this group for now", self
        )

        # Default: keep best/newest.
        self.keep_best_radio.setChecked(True)

        layout.addWidget(self.keep_selected_radio)
        layout.addWidget(self.keep_best_radio)
        layout.addWidget(self.keep_all_radio)
        layout.addWidget(self.skip_radio)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _selected_row_index(self) -> Optional[int]:
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            return None
        return indexes[0].row()

    def _on_accept(self) -> None:
        if self.keep_selected_radio.isChecked():
            idx = self._selected_row_index()
            if idx is None:
                QtWidgets.QMessageBox.warning(
                    self,
                    "No entry selected",
                    "Please select an entry in the table.",
                )
                return
            self.decision = GroupDecision(
                decision_type=GroupDecisionType.KEEP_ONE_SELECTED,
                selected_index=idx,
            )
        elif self.keep_best_radio.isChecked():
            self.decision = GroupDecision(
                decision_type=GroupDecisionType.KEEP_BEST
            )
        elif self.keep_all_radio.isChecked():
            self.decision = GroupDecision(
                decision_type=GroupDecisionType.KEEP_ALL
            )
        else:
            self.decision = GroupDecision(
                decision_type=GroupDecisionType.SKIP
            )
        self.accept()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} GUI")
        self.resize(900, 600)

        # Backend state.
        register_all_plugins()
        self.registry = get_registry()
        self.items_original: List[VaultItem] = []
        self.dedupe_result: Optional[DedupeResult] = None
        self.merged_items: List[VaultItem] = []
        self.discarded_items: List[VaultItem] = []
        self.final_items: List[VaultItem] = []
        self.input_path: Optional[Path] = None
        self.input_provider: Optional[ProviderFormat] = None
        self.output_provider: Optional[ProviderFormat] = None
        self.group_status: Dict[int, str] = {}

        self._create_actions_and_menu()
        self._create_central_widgets()
        self._show_security_warning()

    def _create_actions_and_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        help_menu = menubar.addMenu("&Help")

        self.action_open = QtGui.QAction("Open CSV…", self)
        self.action_open.triggered.connect(self.on_open_csv)
        file_menu.addAction(self.action_open)

        self.action_export = QtGui.QAction("Export CSV…", self)
        self.action_export.setEnabled(False)
        self.action_export.triggered.connect(self.on_export_csv)
        file_menu.addAction(self.action_export)

        file_menu.addSeparator()

        action_quit = QtGui.QAction("Quit", self)
        action_quit.triggered.connect(self.close)
        file_menu.addAction(action_quit)

        action_about = QtGui.QAction("&About", self)
        action_about.triggered.connect(self._show_about_dialog)
        help_menu.addAction(action_about)

    def _create_central_widgets(self) -> None:
        tabs = QtWidgets.QTabWidget(self)
        self.setCentralWidget(tabs)

        summary_tab = QtWidgets.QWidget(self)
        tabs.addTab(summary_tab, "Summary")

        layout = QtWidgets.QVBoxLayout(summary_tab)

        self.info_label = QtWidgets.QLabel("No CSV file loaded.", summary_tab)
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.stats_label = QtWidgets.QLabel("", summary_tab)
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)

        self.groups_table = QtWidgets.QTableWidget(summary_tab)
        self.groups_table.setColumnCount(5)
        self.groups_table.setHorizontalHeaderLabels(
            ["Group", "Site", "Username", "# Entries", "Status"]
        )
        self.groups_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.groups_table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.groups_table.itemSelectionChanged.connect(
            self._on_group_selection_changed
        )
        layout.addWidget(self.groups_table)

        button_layout = QtWidgets.QHBoxLayout()
        self.resolve_button = QtWidgets.QPushButton(
            "Resolve Selected Group…", summary_tab
        )
        self.resolve_button.setEnabled(False)
        self.resolve_button.clicked.connect(self.on_resolve_selected_group)
        button_layout.addStretch(1)
        button_layout.addWidget(self.resolve_button)
        layout.addLayout(button_layout)

    def _show_about_dialog(self) -> None:
        qt_version = QtCore.QT_VERSION_STR
        py_version = sys.version.split()[0]

        text = (
            f"{APP_NAME}\n"
            f"Version: {APP_VERSION}\n"
            f"Python: {py_version}\n"
            f"Qt: {qt_version}\n\n"
            f"Project repository:\n{APP_REPO_URL}\n\n"
            "This project and its author are not affiliated with, "
            "endorsed by, or sponsored by any password or credential storage"
            "application.\n\n"
            "This application uses Qt 6 (https://www.qt.io).\n"
            "Qt and the Qt logo are trademarks of The Qt Company Ltd\n"
            "and/or its subsidiaries. Qt is available under the terms\n"
            "of the LGPLv3 and GPLv3 licenses; see\n"
            "https://www.qt.io/licensing for details.\n\n"
            "This tool is provided \"as is\" under the MIT License. "
            "Use at your own risk; always back up your data and "
            "verify the output before importing it into any system."
        )

        QtWidgets.QMessageBox.about(self, f"About {APP_NAME}", text)

    def _show_security_warning(self) -> None:
        QtWidgets.QMessageBox.warning(
            self,
            "Security warning",
            SECURITY_WARNING.strip(),
        )

    def _on_group_selection_changed(self) -> None:
        has_selection = bool(self.groups_table.selectionModel().selectedRows())
        self.resolve_button.setEnabled(
            has_selection and bool(self.dedupe_result)
        )

    def on_open_csv(self) -> None:
        path_str, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open credential CSV",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not path_str:
            return
        self._load_csv(Path(path_str))

    def _load_csv(self, path: Path) -> None:
        if not path.is_file():
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid file",
                f"The selected file does not exist:\n{path}",
            )
            return

        # Detect provider from headers.
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            headers: List[str] = reader.fieldnames or []

        detection = detect_provider(headers, self.registry)

        dlg = ProviderSelectionDialog(headers, detection, self)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        provider = dlg.selected_provider()
        if provider is None:
            return

        plugin = self.registry.get(provider)

        items: List[VaultItem] = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append(plugin.import_row(row))

        _ensure_internal_ids(items)

        result = dedupe_items(items)

        self.input_path = path
        self.input_provider = provider
        self.items_original = items
        self.dedupe_result = result
        self.merged_items = []
        self.discarded_items = []
        self.final_items = []
        self.group_status = {
            idx: "Pending"
            for idx, group in enumerate(result.near_duplicate_groups, start=1)
            if group
        }

        self._refresh_summary()
        self.action_export.setEnabled(True)

    def _refresh_summary(self) -> None:
        if not self.dedupe_result:
            self.info_label.setText("No CSV file loaded.")
            self.stats_label.setText("")
            self.groups_table.setRowCount(0)
            self.resolve_button.setEnabled(False)
            return

        total_imported = len(self.dedupe_result.kept) + len(
            self.dedupe_result.removed_exact
        )
        near_groups = len(self.dedupe_result.near_duplicate_groups)
        self.info_label.setText(
            f"Input file: {self.input_path!s}\n"
            f"Provider: {self.input_provider.value if self.input_provider else 'unknown'}"
        )
        self.stats_label.setText(
            f"Imported items: {total_imported}\n"
            f"Exact duplicates auto-removed: {len(self.dedupe_result.removed_exact)}\n"
            f"Near-duplicate groups: {near_groups}"
        )

        groups = self.dedupe_result.near_duplicate_groups
        self.groups_table.setRowCount(len(groups))
        for row, group in enumerate(groups):
            idx = row + 1
            if not group:
                continue
            first = group[0]
            site = first.primary_url or ""
            username = first.username or ""
            entries = len(group)
            status = self.group_status.get(idx, "Pending")

            values = [str(idx), site, username, str(entries), status]
            for col, text in enumerate(values):
                item = QtWidgets.QTableWidgetItem(text)
                item.setFlags(
                    item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
                )
                self.groups_table.setItem(row, col, item)

        self.groups_table.resizeColumnsToContents()

    def _selected_group_row(self) -> Optional[int]:
        indexes = self.groups_table.selectionModel().selectedRows()
        if not indexes:
            return None
        return indexes[0].row()

    def on_resolve_selected_group(self) -> None:
        row = self._selected_group_row()
        if row is None or not self.dedupe_result:
            return
        group_index = row + 1
        self._resolve_group(group_index, row)

    def _resolve_group(self, group_index: int, row: int) -> None:
        if not self.dedupe_result:
            return
        groups = self.dedupe_result.near_duplicate_groups
        if group_index < 1 or group_index > len(groups):
            return
        group = groups[group_index - 1]
        if not group:
            return

        dlg = GroupResolutionDialog(group_index, group, self)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted or dlg.decision is None:
            # Treat cancel as skip.
            self.group_status[group_index] = "Skipped"
            self._update_group_status_row(row, group_index)
            return

        decision = dlg.decision

        if decision.decision_type is GroupDecisionType.KEEP_ONE_SELECTED:
            assert decision.selected_index is not None
            keep_idx = decision.selected_index
            survivor = group[keep_idx]
        elif decision.decision_type is GroupDecisionType.KEEP_BEST:
            survivor = max(group, key=score_vault_item)
        elif decision.decision_type is GroupDecisionType.KEEP_ALL:
            self.group_status[group_index] = "Kept all"
            self._update_group_status_row(row, group_index)
            # No merges/discards; nothing to recompute yet.
            return
        else:  # SKIP
            self.group_status[group_index] = "Skipped"
            self._update_group_status_row(row, group_index)
            return

        losers = [item for item in group if item is not survivor]

        # Attach metadata for recomputation and optional changelog.
        survivor_extra = dict(survivor.extra or {})
        survivor_extra.setdefault("dedupe_group_index", str(group_index))
        src_ids: List[str] = []
        for item in group:
            if item.internal_id:
                src_ids.append(item.internal_id)
        if src_ids:
            survivor_extra.setdefault(
                "dedupe_merged_from_internal_ids",
                ",".join(src_ids),
            )
        survivor.extra = survivor_extra

        self.merged_items.append(survivor)

        for victim in losers:
            victim_extra = dict(victim.extra or {})
            victim_extra.setdefault(
                "dedupe_manual_discard_group_index",
                str(group_index),
            )
            victim.extra = victim_extra
            self.discarded_items.append(victim)

        self.group_status[group_index] = "Resolved"
        self._update_group_status_row(row, group_index)
        self._update_final_items()

    def _update_group_status_row(self, row: int, group_index: int) -> None:
        status = self.group_status.get(group_index, "Pending")
        item = self.groups_table.item(row, 4)
        if item is not None:
            item.setText(status)

    def _update_final_items(self) -> None:
        if not self.dedupe_result:
            self.final_items = []
            return
        self.final_items = recompute_final_items(
            self.dedupe_result.kept,
            self.merged_items,
            self.discarded_items,
        )

    def on_export_csv(self) -> None:
        if not self.dedupe_result:
            QtWidgets.QMessageBox.warning(
                self,
                "Nothing to export",
                "Please open a CSV file and run deduplication first.",
            )
            return

        if not self.final_items:
            self._update_final_items()

        provider = self.input_provider or ProviderFormat.PROTONPASS

        # Choose output provider.
        provider_dialog = QtWidgets.QDialog(self)
        provider_dialog.setWindowTitle("Choose output provider")
        vbox = QtWidgets.QVBoxLayout(provider_dialog)
        vbox.addWidget(QtWidgets.QLabel("Output provider:", provider_dialog))
        combo = QtWidgets.QComboBox(provider_dialog)
        for fmt in ProviderFormat:
            if fmt is ProviderFormat.UNKNOWN:
                continue
            combo.addItem(fmt.value, fmt)
        idx = combo.findData(provider)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        vbox.addWidget(combo)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            parent=provider_dialog,
        )
        buttons.accepted.connect(provider_dialog.accept)
        buttons.rejected.connect(provider_dialog.reject)
        vbox.addWidget(buttons)

        if provider_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        chosen_provider = combo.currentData()
        if not isinstance(chosen_provider, ProviderFormat):
            return

        self.output_provider = chosen_provider

        # Choose output path.
        default_dir = str(self.input_path.parent) if self.input_path else ""
        default_name = ""
        if self.input_path:
            default_name = (
                self.input_path.with_name(
                    self.input_path.stem + "_deduped" + self.input_path.suffix
                ).name
            )

        out_path_str, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save cleaned CSV",
            str(Path(default_dir) / default_name) if default_name else default_dir,
            "CSV Files (*.csv);;All Files (*)",
        )
        if not out_path_str:
            return

        output_path = Path(out_path_str).expanduser().resolve()

        try:
            _export_items_to_csv(self.final_items, output_path, chosen_provider)
        except Exception as exc:  # pragma: no cover - GUI-only path
            QtWidgets.QMessageBox.critical(
                self,
                "Export error",
                f"Failed to export CSV:\n{exc}",
            )
            return

        # Build a minimal changelog for GUI exports to match CLI behavior.
        change_log = ChangeLog(
            original_file=str(self.input_path or ""),
            output_file=str(output_path),
            original_hash_sha256="",
            output_hash_sha256="",
        )

        # Exact-duplicate removals.
        for idx, group in enumerate(self.dedupe_result.exact_groups):
            if not group or len(group) < 2:
                continue
            kept = group[0]
            removed = group[1:]
            kept_id = kept.internal_id or ""
            removed_ids = [item.internal_id or "" for item in removed]
            log_removed_exact(change_log, idx, kept_id, removed_ids)

        # Manual merges (metadata recorded by GUI decisions).
        for merged in self.merged_items:
            meta = merged.extra or {}
            group_index_str = meta.get("dedupe_group_index")
            merged_from_ids_str = meta.get("dedupe_merged_from_internal_ids", "")
            if not group_index_str:
                continue
            try:
                group_index = int(group_index_str)
            except ValueError:
                continue

            merged_from_ids = [
                x for x in merged_from_ids_str.split(",") if x
            ] or [merged.internal_id or ""]
            kept_id = merged.internal_id or ""
            log_manual_merge(
                change_log,
                group_index=group_index,
                kept_id=kept_id,
                merged_from_ids=merged_from_ids,
            )

        # Manual discards.
        grouped_discards: Dict[int, List[str]] = {}
        for item in self.discarded_items:
            meta = item.extra or {}
            group_index_str = meta.get("dedupe_manual_discard_group_index")
            if not group_index_str:
                continue
            try:
                gid = int(group_index_str)
            except ValueError:
                continue
            grouped_discards.setdefault(gid, []).append(
                item.internal_id or ""
            )

        for gid, ids in grouped_discards.items():
            if ids:
                log_discard_manual(change_log, group_index=gid, discarded_ids=ids)

        # Populate file hashes and write the changelog file alongside the CSV.
        try:
            change_log.original_hash_sha256 = (
                sha256_file(self.input_path) if self.input_path else ""
            )
            change_log.output_hash_sha256 = sha256_file(output_path)
            changelog_path = output_path.with_suffix(output_path.suffix + ".log.json")
            save_changelog(change_log, changelog_path)
        except Exception:
            # Non-fatal; proceed without changelog.
            pass

        QtWidgets.QMessageBox.information(
            self,
            "Export complete",
            (
                f"Exported {len(self.final_items)} items to:\n{output_path}\n\n"
                "Warning: The output CSV contains plaintext credentials. "
                "Store it securely and delete it when finished."
            ),
        )


def run_gui() -> None:
    app = QtWidgets.QApplication(sys.argv)

    # Try to set a custom window icon if the .ico file is present.
    pkg_dir = Path(__file__).resolve().parent
    icon_candidates = [
        pkg_dir / "assets" / "creddedupe.ico",
    ]

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:  # pragma: no cover - frozen-only path
        icon_candidates.append(
            Path(meipass) / "cred_dedupe" / "assets" / "creddedupe.ico"
        )

    for icon_path in icon_candidates:
        if icon_path.is_file():
            app.setWindowIcon(QtGui.QIcon(str(icon_path)))
            break

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


__all__ = ["run_gui", "MainWindow"]
