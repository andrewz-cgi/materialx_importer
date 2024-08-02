from PySide2.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel, QComboBox

class MaterialInfoWidget(QWidget):

    def __init__(self, parent=None):

        super(MaterialInfoWidget, self).__init__(parent)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.material_name_lineEdit = QLineEdit()
        self.material_name_lineEdit.setPlaceholderText("Material name")
        self.main_layout.addWidget(self.material_name_lineEdit)

        context_label = QLabel("Context:")
        self.main_layout.addWidget(context_label)

        self.context_box = QComboBox()
        self.context_box.addItem("mat")
        self.context_box.addItem("obj")
        self.context_box.addItem("stage")
        self.main_layout.addWidget(self.context_box)

    @property
    def material_name(self):
        return self.material_name_lineEdit.text()
    
    @property
    def context(self):
        return self.context_box.currentText()
