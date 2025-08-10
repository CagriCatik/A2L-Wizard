# gui.py
import os
import sys
from typing import Dict, Any, Set
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QStatusBar, QPushButton, QMenu
)

import pandas as pd
from data_utils import load_data, search_parameters

class A2LSearchWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('A2L Wizard')
        # set icon from static folder
        icon_path = os.path.join(os.path.dirname(__file__), "static", "wizard.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1400, 700)
        self.param_dict: Dict[str, Dict[str, Any]] = {}
        self.columns = [
            'Type', 'Name', 'Comment', 'Value', 'Data_Type', 'Conversion',
            'Measurement_Params', 'ECU_Address', 'Symbol_Link', 'Details'
        ]
        self._init_menu()
        self._init_ui()

    def _init_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        file_menu.addAction('Load .a2l File…', self.load_file)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)
        help_menu = menubar.addMenu('Help')
        help_menu.addAction('About', self.show_about)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        ctrl = QHBoxLayout()
        self.file_label = QLabel('No file loaded')
        ctrl.addWidget(self.file_label)

        load_btn = QPushButton('Load .a2l')
        load_btn.clicked.connect(self.load_file)
        ctrl.addWidget(load_btn)

        export_btn = QPushButton('Export Filtered')
        export_btn.clicked.connect(self.export_to_excel)
        ctrl.addWidget(export_btn)

        ctrl.addSpacing(20)
        ctrl.addWidget(QLabel('Type:'))
        self.type_combo = QComboBox()
        for t in ['All', 'Characteristic', 'Measurement', 'MeasurementArray']:
            self.type_combo.addItem(t)
        self.type_combo.currentTextChanged.connect(self.search)
        ctrl.addWidget(self.type_combo)

        ctrl.addSpacing(20)
        ctrl.addWidget(QLabel('Module:'))
        self.module_combo = QComboBox()
        self.module_combo.setMinimumWidth(160)
        self.module_combo.addItem('All')
        self.module_combo.currentTextChanged.connect(self.search)
        ctrl.addWidget(self.module_combo)

        ctrl.addSpacing(20)
        ctrl.addWidget(QLabel('Search:'))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.search)
        ctrl.addWidget(self.search_input)

        layout.addLayout(ctrl)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(self.columns))
        self.tree.setHeaderLabels(self.columns)
        header = self.tree.header()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultSectionSize(140)
        # enable header context menu
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.show_column_menu)
        layout.addWidget(self.tree)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def update_module_filter(self):
        modules: Set[str] = set()
        for det in self.param_dict.values():
            link = det.get('Symbol_Link', '')
            parts = link.split('_')
            if len(parts) >= 2:
                modules.add(parts[1])
        self.module_combo.blockSignals(True)
        self.module_combo.clear()
        self.module_combo.addItem('All')
        for m in sorted(modules):
            self.module_combo.addItem(m)
        self.module_combo.blockSignals(False)

    def load_file(self):
        # reset last_results when loading new file
        self.last_results = {}
        path, _ = QFileDialog.getOpenFileName(
            self, 'Open .a2l File', '', 'A2L Files (*.a2l)'
        )
        if not path:
            return
        try:
            self.param_dict = load_data(path)
            self.file_label.setText(os.path.basename(path))
            self.update_module_filter()
            self.search_input.clear()
            self.search_input.setFocus()
            self.search()
            self.status.showMessage(f'Loaded {len(self.param_dict)} items')
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def search(self):
        # perform search and store filtered results for export
        q = self.search_input.text().strip()
        tf = self.type_combo.currentText()
        mf = self.module_combo.currentText()
        results = self.param_dict
        if tf != 'All':
            results = {n: d for n, d in results.items() if d.get('Type') == tf}
        if mf != 'All':
            filtered = {}
            for n, d in results.items():
                link = d.get('Symbol_Link', '')
                parts = link.split('_') if link else []
                if mf in parts:
                    filtered[n] = d
            results = filtered
        if q:
            results = search_parameters(results, q)
        # store last results
        self.last_results = results
        self._populate_tree(results)

        q = self.search_input.text().strip()
        tf = self.type_combo.currentText()
        mf = self.module_combo.currentText()
        results = self.param_dict
        if tf != 'All':
            results = {n: d for n, d in results.items() if d.get('Type') == tf}
        if mf != 'All':
            filtered = {}
            for n, d in results.items():
                link = d.get('Symbol_Link', '')
                parts = link.split('_') if link else []
                if mf in parts:
                    filtered[n] = d
            results = filtered
        if q:
            results = search_parameters(results, q)
        self._populate_tree(results)

    def _populate_tree(self, items: Dict[str, Dict[str, Any]]):
        self.tree.clear()
        for det in items.values():
            row = [str(det.get(col, '')) for col in self.columns]
            self.tree.addTopLevelItem(QTreeWidgetItem(row))
        self.status.showMessage(f'{len(items)} displayed')

    def show_column_menu(self, pos):
        menu = QMenu()
        header = self.tree.header()
        for idx, name in enumerate(self.columns):
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(not header.isSectionHidden(idx))
            action.toggled.connect(lambda checked, i=idx: header.setSectionHidden(i, not checked))
            menu.addAction(action)
        menu.exec_(self.tree.header().mapToGlobal(pos))

    def export_to_excel(self):
        """Export the current filtered results to an Excel file."""
        if not hasattr(self, 'last_results') or not self.last_results:
            QMessageBox.warning(self, 'Export', 'No data to export. Perform a search first.')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save Filtered Data', '', 'Excel Files (*.xlsx)'
        )
        if not path:
            return
        try:
            df = pd.DataFrame(list(self.last_results.values()))
            df.to_excel(path, index=False)
            self.status.showMessage(f'Exported {len(self.last_results)} items to {path}')
        except Exception as e:
            QMessageBox.critical(self, 'Export Error', str(e))

    def show_about(self):
        QMessageBox.information(self, 'About', 'A2L-Wizard - fully .a2l functionality')