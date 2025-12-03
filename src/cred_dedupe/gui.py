from __future__ import annotations

import sys
from pathlib import Path

from PyQt6 import QtCore, QtWidgets, QtGui

from . import __version__ as APP_VERSION
from .core import DedupeConfig, dedupe_csv_file


APP_NAME = "CredDedupe"
APP_REPO_URL = "https://github.com/taggedzi/creddedupe"


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(600, 200)
        self.setAcceptDrops(True)

        self._create_menus()

        central = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(central)
        self.setCentralWidget(central)

        # Input file selector.
        input_layout = QtWidgets.QHBoxLayout()
        input_label = QtWidgets.QLabel("Input CSV:")
        self.input_line = QtWidgets.QLineEdit()
        self.input_line.setReadOnly(True)
        input_button = QtWidgets.QPushButton("Browse…")
        input_button.clicked.connect(self._choose_input_file)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(input_button)
        layout.addLayout(input_layout)

        # Output file selector.
        output_layout = QtWidgets.QHBoxLayout()
        output_label = QtWidgets.QLabel("Output CSV:")
        self.output_line = QtWidgets.QLineEdit()
        output_button = QtWidgets.QPushButton("Browse…")
        output_button.clicked.connect(self._choose_output_file)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_line)
        output_layout.addWidget(output_button)
        layout.addLayout(output_layout)

        # Options.
        self.strict_password_checkbox = QtWidgets.QCheckBox(
            "Only merge entries when passwords match (safer)"
        )
        self.strict_password_checkbox.setChecked(True)

        self.email_username_checkbox = QtWidgets.QCheckBox(
            "Treat email and username as equivalent login identifiers"
        )
        self.email_username_checkbox.setChecked(True)

        layout.addWidget(self.strict_password_checkbox)
        layout.addWidget(self.email_username_checkbox)

        # Status and run button.
        bottom_layout = QtWidgets.QHBoxLayout()
        self.status_label = QtWidgets.QLabel("Ready.")
        self.status_label.setWordWrap(True)
        run_button = QtWidgets.QPushButton("Run Deduplication")
        run_button.clicked.connect(self._run_dedupe)
        bottom_layout.addWidget(self.status_label, 1)
        bottom_layout.addWidget(run_button, 0)
        layout.addLayout(bottom_layout)

        # Hint about drag & drop.
        hint_label = QtWidgets.QLabel(
            "Tip: You can drag & drop a CSV file anywhere onto this window to "
            "set it as the input."
        )
        font = hint_label.font()
        font.setPointSize(font.pointSize() - 1)
        hint_label.setFont(font)
        hint_label.setStyleSheet("color: gray;")
        layout.addWidget(hint_label)

    def _create_menus(self) -> None:
        menubar = self.menuBar()
        help_menu = menubar.addMenu("&Help")

        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self._show_about_dialog)

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

    # Drag & drop support.
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".csv"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if local_path.lower().endswith(".csv"):
                self.input_line.setText(local_path)
                self._suggest_output_path()
                break

    def _choose_input_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Credential CSV",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if path:
            self.input_line.setText(path)
            self._suggest_output_path()

    def _choose_output_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Choose output CSV",
            self.output_line.text() or "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if path:
            self.output_line.setText(path)

    def _suggest_output_path(self) -> None:
        input_text = self.input_line.text().strip()
        if not input_text:
            return
        in_path = Path(input_text)
        suggested = in_path.with_name(in_path.stem + "_deduped" + in_path.suffix)
        if not self.output_line.text().strip():
            self.output_line.setText(str(suggested))

    def _run_dedupe(self) -> None:
        input_text = self.input_line.text().strip()
        output_text = self.output_line.text().strip()

        if not input_text:
            QtWidgets.QMessageBox.warning(
                self,
                "Missing input",
                "Please select an input CSV file.",
            )
            return

        input_path = Path(input_text)
        if not input_path.is_file():
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid input",
                f"The input file does not exist:\n{input_path}",
            )
            return

        if not output_text:
            self._suggest_output_path()
            output_text = self.output_line.text().strip()

        if not output_text:
            QtWidgets.QMessageBox.warning(
                self,
                "Missing output",
                "Please choose an output CSV file.",
            )
            return

        output_path = Path(output_text)

        cfg = DedupeConfig(
            strict_password_match=self.strict_password_checkbox.isChecked(),
            treat_email_username_equivalent=self.email_username_checkbox.isChecked(),
        )

        self.status_label.setText("Running deduplication…")
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            stats = dedupe_csv_file(input_path, output_path, cfg)
        except Exception as exc:  # pragma: no cover - GUI-only path
            QtWidgets.QApplication.restoreOverrideCursor()
            self.status_label.setText("Error.")
            QtWidgets.QMessageBox.critical(
                self,
                "Error during deduplication",
                f"An error occurred:\n{exc}",
            )
            return
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        self.status_label.setText(
            f"Done. {stats.input_count} → {stats.output_count} entries "
            f"({stats.merged_groups} groups merged)."
        )
        QtWidgets.QMessageBox.information(
            self,
            "Deduplication complete",
            (
                f"Processed {stats.input_count} rows → {stats.output_count} rows.\n"
                f"Merged groups: {stats.merged_groups}\n"
                f"Rows kept separate due to missing identifiers: {stats.skipped_rows}\n\n"
                f"Output written to:\n{output_path}"
            ),
        )


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)

    # Try to set a custom window icon if the .ico file is present.
    pkg_dir = Path(__file__).resolve().parent
    icon_candidates = [
        pkg_dir / "assets" / "creddedupe.ico",
    ]

    # In a frozen (PyInstaller) build, data files are unpacked under
    # sys._MEIPASS; we arrange the icon to live at
    # <_MEIPASS>/cred_dedupe/assets/creddedupe.ico.
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


if __name__ == "__main__":  # pragma: no cover - GUI entrypoint
    main()
