from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtUiTools import *
from PySide2.QtWidgets import *

import hou, json

from ..modules.settings_preset_template import SettingsPresetTemplate
from ..modules import texture_importer as importer

from .widgets.texture_folder import TextureFolderWidget
from .widgets.settings import SettingsWidget
from .widgets.material_info import MaterialInfoWidget
from .widgets.preview_object import PreviewObjectWidget
from .dictionary.dictionary_widget import DictionaryWidget

from .. import materialx_importer

class MaterialxImporterUI(QMainWindow):

    def __init__(self, parent=None, debug=True):

        self.debug = debug

        super(MaterialxImporterUI, self).__init__(parent)
    
        self.setWindowTitle("MaterialX importer 0.1")
        self.setGeometry(100, 100, 400, 300)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(400, 375)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Texture folder widget
        self.textured_folder_wdgt =  TextureFolderWidget()
        main_layout.addWidget(self.textured_folder_wdgt)

        # Settings widget
        self.settings_wdgt = SettingsWidget()
        main_layout.addWidget(self.settings_wdgt)
 
        # Material information widget
        self.material_info_wdgt = MaterialInfoWidget()
        main_layout.addWidget(self.material_info_wdgt)

        # Preview object widget
        self.preview_object_wdgt = PreviewObjectWidget()
        main_layout.addWidget(self.preview_object_wdgt)

        # Button layout layout
        self.create_btn = QPushButton("Create MaterialX")
        self.create_btn.clicked.connect(self.on_create_materialx)
        main_layout.addWidget(self.create_btn)

        # Menu bar
        self.menubar = QMenuBar(self)
        self.menubar.setGeometry(QRect(0, 0, 505, 21))
        self.menuOptions = QMenu(self.menubar)
        self.menuOptions.setTitle('Preset settings')
        self.menuAbout = QMenu(self.menubar)
        self.menuAbout.setTitle('About')
        self.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)
        self.load_preset_action = QAction(self)
        self.load_preset_action.setText('Load...')
        self.load_preset_action.triggered.connect(self.on_load_preset)
        self.save_preset_action = QAction(self)
        self.save_preset_action.setText('Save...')
        self.save_preset_action.triggered.connect(self.on_save_preset)
        self.separator_action = QAction(self)
        self.separator_action.setSeparator(True)
        self.reset_preset_action = QAction(self)
        self.reset_preset_action.setText('Reset')
        self.reset_preset_action.triggered.connect(self.on_reset_settings)
        self.actionDocumentation = QAction(self)
        self.actionDocumentation.triggered.connect(self.on_help)
        self.actionDocumentation.setText('Help..')
        self.menuOptions.addAction(self.load_preset_action)
        self.menuOptions.addAction(self.save_preset_action)
        self.menuOptions.addAction(self.separator_action)
        self.menuOptions.addAction(self.reset_preset_action)
        self.menuAbout.addAction(self.actionDocumentation)
        self.menubar.addAction(self.menuOptions.menuAction())
        self.menubar.addAction(self.menuAbout.menuAction())

    def on_create_materialx(self):

        if not self.textured_folder_wdgt.texture_folder_path:
            hou.ui.displayMessage('Select a texture folder path', severity=hou.severityType.Error, title="Texture folder path error")

        if not self.material_info_wdgt.material_name:
            hou.ui.displayMessage('Specify a material name', severity=hou.severityType.Error, title="Material name error")           

        material_import_library: hou.Node = materialx_importer.get_materialx_import_library(self.material_info_wdgt.context)
        material_full_name = materialx_importer.get_material_full_name(self.material_info_wdgt.material_name)

        if material_import_library.node(material_full_name):
            if not self.material_overwrite(f'Material named {material_full_name} already exist in the context, do you want do replace it?'):
                return
            else:
                material_import_library.node(material_full_name).destroy()

        materialx_importer.import_materialx(self.textured_folder_wdgt.texture_folder_path, material_full_name, material_import_library, self.settings_wdgt.settings)

    def material_overwrite(self, message):
        result = hou.ui.readInput(message, buttons=("OK", "Cancel"))
        if result[0] == 0:  # "OK" button pressed
            return True
        else:
            return False

    def on_load_preset(self):
        if self.debug: print("Loafing an existing")

        houdini_version = hou.applicationVersion()
        preset_path = hou.expandString(hou.ui.selectFile(hou.getenv("HOME") + "/houdini{}.{}/scripts/materialx_importer/presets".format(houdini_version[0], houdini_version[1]), title="Select Preset", chooser_mode=hou.fileChooserMode.Read))
        if not preset_path: return

        if not preset_validation(preset_path):
            hou.ui.displayMessage("File\n {}\n it's not a valid preset".format(preset_path), severity=hou.severityType.Error, title="Preset load error")
            return
        
        with open(preset_path) as raw_data:
            preset_data = json.load(raw_data)

        preset = SettingsPresetTemplate(
            color_variation=preset_data['color_variation'],
            ao=preset_data['ao'],
            translucency=preset_data['translucency'],
            opacity=preset_data['opacity'],
            displacement=preset_data['displacement'],
            metalness=preset_data['metalness']
        )

        self.settings_wdgt.update_settings(preset)

    def on_save_preset(self):

        if self.debug: print("---- Saving new preset ----")

        houdini_version = hou.applicationVersion()
        save_path = hou.expandString(hou.ui.selectFile(hou.getenv("HOME") + "/houdini{}.{}/scripts/materialx_importer/presets".format(houdini_version[0], houdini_version[1]), title="Save new preset", chooser_mode=hou.fileChooserMode.Write))
        if not save_path: return

        if not save_path.endswith(".json"):
            if self.debug: print("• Added json ext to save path")
            save_path += ".json"

        raw_preset = {}
        raw_preset['color_variation'] = self.color_variation_checkbox.isChecked()
        raw_preset['ao'] = self.ao_checkbox.isChecked()
        raw_preset['translucency'] = self.translucency_checkbox.isChecked()
        raw_preset['opacity'] = self.opacity_checkbox.isChecked()
        raw_preset['metalness'] = self.metalness_checkbox.isChecked()
        raw_preset['displacement'] = self.displacement_checkbox.isChecked()

        with open(save_path, 'w') as json_file:
            json.dump(raw_preset, json_file, indent=2)

        if self.debug: print("• Preset saved")

    def on_reset_settings(self):
        if self.debug: print("on_reset_settings do default")
        self.settings_wdgt.update_settings(SettingsPresetTemplate())

    def on_help(self):
        pass
    
def preset_validation(preset):
    return True