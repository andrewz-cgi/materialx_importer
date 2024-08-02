from PySide2.QtWidgets import QMainWindow, QListView, QVBoxLayout, QWidget, QLabel, QTableView, QPushButton
from PySide2.QtGui import QStandardItemModel, QStandardItem
import sys


class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create a central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a table model and set the data
        self.table_model = QStandardItemModel()  # 0 rows, 2 columns

        data = {"Item 1": "Value 1",
                "Item 2": "Value 2",
                "Item 3": "Value 3",
                "Item 4": "Value 4",
                "Item 5": "Value 5"}

        row = 0
        for value, key in enumerate(data):
            item = QStandardItem(value)
            self.table_model.setItem(row, 0, item)
            row += 1

        # Create a QTableView and set the model
        self.table_view = QTableView(central_widget)
        self.table_view.setModel(self.table_model)

        # Create a header label
        header_label = QLabel("Header")
        #self.table_view.horizontalHeader().setVisible(False)

        vertical_header_labels = ["Row 1", "Row 2", "Row 3", "Row 4", "Row 5"]
        self.table_model.setVerticalHeaderLabels(vertical_header_labels)
        self.table_model.setHorizontalHeaderLabels("ciao")

        # Create a button for adding a new column
        add_column_button = QPushButton("Add Column")
        add_column_button.clicked.connect(self.add_column)

        # Create a layout, add the header, QTableView, and the button to it
        layout = QVBoxLayout(central_widget)
        layout.addWidget(header_label)
        layout.addWidget(self.table_view)
        layout.addWidget(add_column_button)

    def add_column(self):
        column_count = self.table_model.columnCount()
        new_column_name = f"Column {column_count + 1}"
        self.table_model.setHorizontalHeaderLabels(
            self.table_model.horizontalHeaderLabels() + [new_column_name]
        )
win = MyMainWindow()
win.show()