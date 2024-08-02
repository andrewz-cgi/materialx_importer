from PySide2.QtWidgets import QWidget, QHBoxLayout, QCheckBox

class PreviewObjectWidget(QWidget):

    def __init__(self, parent=None):

        super(PreviewObjectWidget, self).__init__(parent)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.create_preview_checkbox = QCheckBox("Create preview object")
        self.main_layout.addWidget(self.create_preview_checkbox)

    @property
    def create_preview(self):
        return self.create_preview_checkbox.isChecked()