import sys
import pprint
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTreeWidget, QTreeWidgetItem, QTextEdit, QTableWidget, QTableWidgetItem,
    QSplitter, QFileDialog, QLineEdit, QMenuBar, QMenu, QMessageBox
)
from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtGui import QAction, QPainter  
from PySide6.QtCore import Qt
from nptdms import TdmsFile

class TDMSViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TDMS Viewer (PySide6)")
        self.resize(1000, 700)

        self.page_size = 1000
        self.current_page = 0
        self.current_channel = None
        self.tdms_file = None

        self.init_ui()

    def init_ui(self):
        # Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open TDMS File", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        hbox = QHBoxLayout(central_widget)

        # Left panel (Tree + Properties)
        left_panel = QVBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("TDMS Structure")
        self.tree.itemClicked.connect(self.on_item_clicked)
        left_panel.addWidget(self.tree)

        self.prop_view = QTextEdit()
        self.prop_view.setReadOnly(True)
        left_panel.addWidget(QLabel("Properties:"))
        left_panel.addWidget(self.prop_view)

        # Right panel (Table + Chart)
        right_panel = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Index", "Value"])
        right_panel.addWidget(self.table)

        self.chart = QChart()
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        right_panel.addWidget(self.chart_view)

        # Navigation panel
        nav_panel = QHBoxLayout()
        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedWidth(40)
        self.prev_btn.clicked.connect(self.prev_page)
        nav_panel.addWidget(self.prev_btn)

        self.page_label = QLabel("Page 1")
        nav_panel.addWidget(self.page_label)

        self.page_input = QLineEdit()
        self.page_input.setFixedWidth(50)
        nav_panel.addWidget(self.page_input)

        self.go_btn = QPushButton("Go")
        self.go_btn.setFixedWidth(50)
        self.go_btn.clicked.connect(self.jump_to_page)
        nav_panel.addWidget(self.go_btn)

        self.next_btn = QPushButton(">")
        self.next_btn.setFixedWidth(40)
        self.next_btn.clicked.connect(self.next_page)
        nav_panel.addWidget(self.next_btn)

        right_panel.addLayout(nav_panel)

        # Split panels
        splitter = QSplitter()
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 3)

        hbox.addWidget(splitter)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open TDMS File", "", "TDMS Files (*.tdms)")
        if not file_path:
            return

        try:
            self.tdms_file = TdmsFile.read(file_path)
            self.tree.clear()
            self.table.clearContents()
            self.table.setRowCount(0)
            self.prop_view.clear()
            self.chart.removeAllSeries()
            self.build_tree(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open TDMS file:\n{str(e)}")

    def build_tree(self, filepath):
        file_item = QTreeWidgetItem([filepath])
        self.tree.addTopLevelItem(file_item)

        for group in self.tdms_file.groups():
            group_item = QTreeWidgetItem([group.name])
            file_item.addChild(group_item)
            for channel in group.channels():
                channel_item = QTreeWidgetItem([channel.name])
                group_item.addChild(channel_item)
        self.tree.expandAll()

    def on_item_clicked(self, item):
        self.prop_view.clear()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.chart.removeAllSeries()

        parent = item.parent()
        if parent is None:
            # File
            props = {
                "File": item.text(0),
                "Groups": len(self.tdms_file.groups()),
                "Total Channels": sum(len(g.channels()) for g in self.tdms_file.groups())
            }
        elif parent.parent() is None:
            # Group
            group_name = item.text(0)
            group = self.tdms_file[group_name]
            props = {
                "Group": group.name,
                "Channels": len(group.channels()),
                "Properties": dict(group.properties)
            }
        else:
            # Channel
            group_name = parent.text(0)
            channel_name = item.text(0)
            self.current_channel = self.tdms_file[group_name][channel_name]
            self.current_page = 0
            self.load_page()
            props = {
                "Channel": channel_name,
                "Data type": str(self.current_channel.data_type),
                "Length": len(self.current_channel),
                "Properties": dict(self.current_channel.properties)
            }
        self.prop_view.setPlainText(pprint.pformat(props, indent=2))

    def load_page(self):
        if self.current_channel is None:
            return

        total_length = len(self.current_channel)
        start = self.current_page * self.page_size
        end = min(start + self.page_size, total_length)

        self.table.setRowCount(end - start)
        preview = self.current_channel[start:end]

        series = QLineSeries()
        for i, val in enumerate(preview, start=start):
            self.table.setItem(i - start, 0, QTableWidgetItem(str(i)))
            self.table.setItem(i - start, 1, QTableWidgetItem(str(val)))
            series.append(i, float(val))

        self.chart.removeAllSeries()
        self.chart.addSeries(series)
        self.chart.createDefaultAxes()
        self.chart.setTitle(f"Page {self.current_page + 1}")

        total_pages = (total_length + self.page_size - 1) // self.page_size
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page()

    def next_page(self):
        if not self.current_channel:
            return
        total_pages = (len(self.current_channel) + self.page_size - 1) // self.page_size
        if self.current_page + 1 < total_pages:
            self.current_page += 1
            self.load_page()

    def jump_to_page(self):
        if not self.current_channel:
            QMessageBox.information(self, "No Channel", "Select a channel first.")
            return

        try:
            page = int(self.page_input.text()) - 1
            total_pages = (len(self.current_channel) + self.page_size - 1) // self.page_size
            if 0 <= page < total_pages:
                self.current_page = page
                self.load_page()
            else:
                QMessageBox.warning(self, "Out of Range", f"Enter a page between 1 and {total_pages}")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Enter a valid integer.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = TDMSViewer()
    viewer.show()
    sys.exit(app.exec())
