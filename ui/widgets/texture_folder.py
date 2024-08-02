from PySide2.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
import hou

class TextureFolderWidget(QWidget):

    def __init__(self, parent=None):

        super(TextureFolderWidget, self).__init__(parent)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.texture_folder = QLineEdit()
        self.texture_folder.setPlaceholderText("Textures folder ...")
        self.main_layout.addWidget(self.texture_folder)

        texture_folder_btn = QPushButton("Load textures folder")
        texture_folder_btn.clicked.connect(self.on_select_texture_folder)
        self.main_layout.addWidget(texture_folder_btn)

    @property
    def texture_folder_path(self) -> str:
        path = self.texture_folder.text()
        if path:
            path = hou.expandString(self.texture_folder.text())
        return path

    def on_select_texture_folder(self):

        folder_path = hou.ui.selectFile(hou.getenv("HOME"), title="Asset Folder", file_type=hou.fileType.Directory)

        if folder_path:
            self.texture_folder.setText(folder_path)