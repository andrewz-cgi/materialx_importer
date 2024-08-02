from PySide2.QtWidgets import QWidget, QVBoxLayout, QTableView
from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtCore import Qt


DEFAULT_TEXTURE_DICTIONARY = {
    "BASE_COLOR": ["diffuse", "diff", "base-color", "basecolor", "base_color", "albedo", "color"],
    "ROUGHNESS": ["roughness", "gloss", "glossiness"],
    "NORMAL": ["normal", "bumb"],
    "AO": ["ao", "ambient_occlusion", "ambient-occlusion", "ambient_occlusion", "ambientocclusion"],
    "DISPLACEMENT": ["displacement", "height"],
    "TRANSLUCENCY": ["translucency", "transparency", "transmission", "reflaction"],
    "OPACITY": ["opacity", "alpha"],
    "METALNESS": ["metallic", "metalness", "metallicity", "metal"]
}

class DictionaryWidget(QWidget):

    def __init__(self, parent=None, debug=True):

        super(DictionaryWidget, self).__init__(parent)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.table_model = QStandardItemModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)

        row = 0
        vertical_header_labels = []
        for key, items in DEFAULT_TEXTURE_DICTIONARY.items():
            vertical_header_labels.append(key)
            item = QStandardItem(','.join(items))
            self.table_model.setItem(row, 0, item)
            row += 1
        self.table_model.setVerticalHeaderLabels(vertical_header_labels)
        self.table_view.resizeColumnToContents(0)
        main_layout.addWidget(self.table_view)