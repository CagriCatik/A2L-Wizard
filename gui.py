import os
import sys
import pandas as pd

from typing import Dict, Any, Set, List
from PySide6.QtCore import Qt, QPoint, QSettings, QTimer
from PySide6.QtGui import (QAction, QIcon, QPalette, 
                           QColor, QClipboard, QKeySequence, 
                           QGuiApplication)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, 
    QFileDialog, QMessageBox,
    QVBoxLayout, QLabel, QLineEdit, 
    QComboBox, QTreeWidget, QTreeWidgetItem, 
    QHeaderView, QStatusBar, QMenu, QToolBar
)


from data_utils import load_data, search_parameters

APP_ORG = "CagriCatik"
APP_NAME = "A2L-Wizard"

def apply_fusion_dark(app: QApplication, enabled: bool) -> None:
    if not enabled:
        app.setStyle("Fusion")
        app.setPalette(app.style().standardPalette())
        return
    app.setStyle("Fusion")
    palette = QPalette()
    base = QColor(40, 40, 40)
    alt_base = QColor(49, 49, 49)
    window = QColor(53, 53, 53)
    text = QColor(220, 220, 220)
    disabled_text = QColor(127, 127, 127)
    highlight = QColor(42, 130, 218)
    palette.setColor(QPalette.Window, window)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, base)
    palette.setColor(QPalette.AlternateBase, alt_base)
    palette.setColor(QPalette.ToolTipBase, text)
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    palette.setColor(QPalette.Button, window)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, highlight)
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

class A2LSearchWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Settings first
        self.settings = QSettings(APP_ORG, APP_NAME)

        # Theme before building widgets
        apply_fusion_dark(QApplication.instance(), self.settings.value("ui/dark", False, type=bool))

        # Data fields
        self.param_dict: Dict[str, Dict[str, Any]] = {}
        self.last_results: Dict[str, Dict[str, Any]] = {}
        self.columns: List[str] = [
            "Type", "Name", "Comment", "Value", "Data_Type", "Conversion",
            "Measurement_Params", "ECU_Address", "Symbol_Link", "Details",
        ]

        # Window
        self.setWindowTitle("A2L Wizard")
        icon_path = os.path.join(os.path.dirname(__file__), "static", "wizard.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1400, 800)

        # Build UI
        self._init_menu()
        self._init_toolbar()
        self._init_ui()

        # Restore state after widgets exist
        self._restore_state()

        # Debounced search timer
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(200)
        self.search_timer.timeout.connect(self._do_search)

    # ---------- UI ----------
    def _init_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        act_open = QAction("Load .a2l File...", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self.load_file)
        file_menu.addAction(act_open)

        self.act_export = QAction("Export Filtered", self)
        self.act_export.setShortcut(QKeySequence("Ctrl+E"))
        self.act_export.triggered.connect(self.export_to_excel)
        self.act_export.setEnabled(False)
        file_menu.addAction(self.act_export)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        view_menu = menubar.addMenu("View")
        self.act_dark = QAction("Dark Mode", self, checkable=True)
        self.act_dark.setChecked(self.settings.value("ui/dark", False, type=bool))
        self.act_dark.toggled.connect(self._toggle_dark)
        view_menu.addAction(self.act_dark)

        self.act_compact = QAction("Compact Rows", self, checkable=True)
        self.act_compact.setChecked(self.settings.value("ui/compact", False, type=bool))
        self.act_compact.toggled.connect(self._apply_row_height)
        view_menu.addAction(self.act_compact)

        view_menu.addSeparator()
        reset_cols = QAction("Reset Column Widths", self)
        reset_cols.triggered.connect(self._reset_column_widths)
        view_menu.addAction(reset_cols)

        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)

    def _init_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setObjectName("MainToolbar")  # required for saveState/restoreState
        tb.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, tb)

        btn_open = QAction(QIcon.fromTheme("document-open"), "Load .a2l", self)
        btn_open.triggered.connect(self.load_file)
        tb.addAction(btn_open)

        btn_export = QAction(QIcon.fromTheme("document-save"), "Export", self)
        btn_export.triggered.connect(self.export_to_excel)
        tb.addAction(btn_export)

        tb.addSeparator()

        tb.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        for t in ["All", "Characteristic", "Measurement", "MeasurementArray"]:
            self.type_combo.addItem(t)
        self.type_combo.currentTextChanged.connect(self._schedule_search)
        tb.addWidget(self.type_combo)

        tb.addSeparator()
        tb.addWidget(QLabel("Module:"))
        self.module_combo = QComboBox()
        self.module_combo.setMinimumWidth(160)
        self.module_combo.addItem("All")
        self.module_combo.currentTextChanged.connect(self._schedule_search)
        tb.addWidget(self.module_combo)

        tb.addSeparator()
        tb.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setPlaceholderText("Name, comment, address, ...")
        self.search_input.textChanged.connect(self._schedule_search)
        tb.addWidget(self.search_input)

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.tree = QTreeWidget()
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree.setColumnCount(len(self.columns))
        self.tree.setHeaderLabels(self.columns)

        header = self.tree.header()
        header.setSortIndicatorShown(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultSectionSize(160)
        header.setStretchLastSection(True)
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.show_column_menu)

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._row_context_menu)

        layout.addWidget(self.tree)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.lbl_count = QLabel("0 displayed")
        self.status.addPermanentWidget(self.lbl_count)

        self._apply_row_height(self.settings.value("ui/compact", False, type=bool))

    # ---------- Persistence ----------
    def _restore_state(self) -> None:
        geo = self.settings.value("ui/geometry")
        if geo:
            self.restoreGeometry(geo)
        winstate = self.settings.value("ui/window_state")
        if winstate:
            self.restoreState(winstate)
        header_state = self.settings.value("ui/header")
        if header_state:
            self.tree.header().restoreState(header_state)
        hidden = self.settings.value("ui/hidden_cols", [])
        if hidden:
            for i in hidden:
                try:
                    self.tree.header().setSectionHidden(int(i), True)
                except Exception:
                    pass

    def _save_state(self) -> None:
        self.settings.setValue("ui/geometry", self.saveGeometry())
        self.settings.setValue("ui/window_state", self.saveState())
        self.settings.setValue("ui/header", self.tree.header().saveState())
        hidden = [i for i in range(len(self.columns)) if self.tree.header().isSectionHidden(i)]
        self.settings.setValue("ui/hidden_cols", hidden)

    # ---------- Actions ----------
    def _toggle_dark(self, enabled: bool) -> None:
        apply_fusion_dark(QApplication.instance(), enabled)
        self.settings.setValue("ui/dark", enabled)

    def _apply_row_height(self, enabled: bool) -> None:
        compact = enabled if isinstance(enabled, bool) else self.act_compact.isChecked()
        self.tree.setStyleSheet("QTreeWidget::item { height: %dpx; }" % (18 if compact else 24))
        self.settings.setValue("ui/compact", compact)

    def _reset_column_widths(self) -> None:
        header = self.tree.header()
        header.resizeSections(QHeaderView.ResizeToContents)
        for i in range(header.count()):
            if header.sectionSize(i) > 450:
                header.resizeSection(i, 300)

    # ---------- Filters / parsing ----------
    def update_module_filter(self) -> None:
        modules: Set[str] = set()
        for det in self.param_dict.values():
            link = det.get("Symbol_Link", "")
            parts = link.split("_")
            if len(parts) >= 2:
                modules.add(parts[1])
        self.module_combo.blockSignals(True)
        self.module_combo.clear()
        self.module_combo.addItem("All")
        for m in sorted(modules):
            self.module_combo.addItem(m)
        self.module_combo.blockSignals(False)

    # ---------- File ops ----------
    def load_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open .a2l File", "", "A2L Files (*.a2l)")
        if not path:
            return
        try:
            self.param_dict = load_data(path)
            self.file_label_text(os.path.basename(path))
            self.update_module_filter()
            self.search_input.clear()
            self.search_input.setFocus()
            self._do_search()
            self.status.showMessage(f"Loaded {len(self.param_dict)} items")
            self.act_export.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def export_to_excel(self) -> None:
        if not self.last_results:
            QMessageBox.warning(self, "Export", "No data to export. Perform a search first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Filtered Data", "", "Excel Files (*.xlsx)")
        if not path:
            return
        try:
            df = pd.DataFrame(list(self.last_results.values()))
            df.to_excel(path, index=False)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(self.last_results)} items to:\n{path}"
            )
            self.status.showMessage(f"Exported {len(self.last_results)} items to {path}")

            self.status.showMessage(f"Exported {len(self.last_results)} items to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    # ---------- Search ----------
    def _schedule_search(self) -> None:
        self.search_timer.start()

    def _do_search(self) -> None:
        q = self.search_input.text().strip()
        tf = self.type_combo.currentText()
        mf = self.module_combo.currentText()

        results = self.param_dict
        if tf != "All":
            results = {n: d for n, d in results.items() if d.get("Type") == tf}
        if mf != "All":
            filtered: Dict[str, Dict[str, Any]] = {}
            for n, d in results.items():
                link = d.get("Symbol_Link", "")
                parts = link.split("_") if link else []
                if mf in parts:
                    filtered[n] = d
            results = filtered
        if q:
            results = search_parameters(results, q)

        self.last_results = results
        self._populate_tree(results)

    def _populate_tree(self, items: Dict[str, Dict[str, Any]]) -> None:
        self.tree.clear()
        add_item = self.tree.addTopLevelItem
        for det in items.values():
            row = [str(det.get(col, "")) for col in self.columns]
            add_item(QTreeWidgetItem(row))
        self.lbl_count.setText(f"{len(items)} displayed")

    # ---------- Menus ----------
    def show_column_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        header = self.tree.header()
        for idx, name in enumerate(self.columns):
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(not header.isSectionHidden(idx))
            action.toggled.connect(lambda checked, i=idx: header.setSectionHidden(i, not checked))
            menu.addAction(action)
        menu.exec(self.tree.header().mapToGlobal(pos))

    def _row_context_menu(self, pos: QPoint) -> None:
        item = self.tree.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        act_copy_cell = QAction("Copy Cell", self)
        act_copy_row = QAction("Copy Row (TSV)", self)
        act_export_sel = QAction("Export Selected...", self)
        act_copy_cell.triggered.connect(lambda: self._copy_cell(item))
        act_copy_row.triggered.connect(self._copy_row(item))
        act_export_sel.triggered.connect(self._export_selected)
        menu.addAction(act_copy_cell)
        menu.addAction(act_copy_row)
        menu.addSeparator()
        menu.addAction(act_export_sel)
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _copy_cell(self, item: QTreeWidgetItem) -> None:
        col = self.tree.currentColumn()
        text = item.text(col)
        QGuiApplication.clipboard().setText(text, QClipboard.Clipboard)
        self.status.showMessage("Cell copied")

    def _copy_row(self, item: QTreeWidgetItem):
        def _handler():
            parts = [item.text(i) for i in range(self.tree.columnCount())]
            QGuiApplication.clipboard().setText("\t".join(parts), QClipboard.Clipboard)
            self.status.showMessage("Row copied")
        return _handler

    def _export_selected(self) -> None:
        items = self.tree.selectedItems()
        if not items:
            QMessageBox.information(self, "Export", "No rows selected.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Selected Rows", "", "Excel Files (*.xlsx)")
        if not path:
            return
        try:
            rows = [{self.columns[i]: it.text(i) for i in range(len(self.columns))} for it in items]
            pd.DataFrame(rows).to_excel(path, index=False)
            self.status.showMessage(f"Exported {len(rows)} selected rows to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    # ---------- Misc ----------
    def file_label_text(self, text: str) -> None:
        self.setWindowTitle(f"A2L Wizard - {text}")
        self.status.showMessage(text)

    def show_about(self) -> None:
        QMessageBox.information(self, "About", "This is a fucking awesome intuitive A2L Parameter Search GUI\nYou dont need any more info or help 😈")

    # ---------- Qt events ----------
    def closeEvent(self, event) -> None:
        self._save_state()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_fusion_dark(app, QSettings(APP_ORG, APP_NAME).value("ui/dark", False, type=bool))
    win = A2LSearchWindow()
    win.show()
    sys.exit(app.exec())
