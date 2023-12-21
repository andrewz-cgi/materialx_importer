from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtUiTools import *
from PySide2.QtWidgets import *

import hou, json, os

from ..modules.settings_preset_template import SettingsPresetTemplate
from ..modules import texture_importer as importer

class MaterialxImporterUI(QMainWindow):

    def __init__(self, parent=None, debug=True):

        self.debug = debug

        super(MaterialxImporterUI, self).__init__(parent)
    
        self.setWindowTitle("MaterialX importer 0.1")
        self.setGeometry(100, 100, 400, 300)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(400, 350)

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        folder_layout = QHBoxLayout()
        self.texture_folder = QLineEdit()
        self.texture_folder.setPlaceholderText("Select texture folder ...")
        folder_layout.addWidget(self.texture_folder)
        texture_folder_btn = QPushButton("Texture folder")
        texture_folder_btn.clicked.connect(self.on_select_texture_folder)
        folder_layout.addWidget(texture_folder_btn)
        main_layout.addLayout(folder_layout)

        settings_box = QGroupBox("Settings")
        settings_box_layout = QVBoxLayout()
        self.color_variation_checkbox = QCheckBox("Color variation")
        self.ao_checkbox = QCheckBox("AO")
        self.translucency_checkbox = QCheckBox("Translucency")
        self.opacity_checkbox = QCheckBox("Opacity")
        self.metalness_checkbox = QCheckBox("Metalness")
        self.displacement_checkbox = QCheckBox("Displacement")
        settings_box_layout.addWidget(self.color_variation_checkbox)
        settings_box_layout.addWidget(self.ao_checkbox)
        settings_box_layout.addWidget(self.translucency_checkbox)
        settings_box_layout.addWidget(self.opacity_checkbox)
        settings_box_layout.addWidget(self.metalness_checkbox)
        settings_box_layout.addWidget(self.displacement_checkbox)
        settings_box.setLayout(settings_box_layout)
        main_layout.addWidget(settings_box)

        self.material_name = QLineEdit()
        self.material_name.setPlaceholderText("Material name")
        main_layout.addWidget(self.material_name)
        self.context_box = QComboBox()
        self.context_box.addItem("mat")
        self.context_box.addItem("obj")
        self.context_box.addItem("stage")
        main_layout.addWidget(self.context_box)
        self.create_btn = QPushButton("Create MaterialX")
        self.create_btn.clicked.connect(self.on_create_materialx)
        main_layout.addWidget(self.create_btn)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Menu bar
        self.menubar = QMenuBar(self)
        self.menubar.setGeometry(QRect(0, 0, 505, 21))
        self.menuOptions = QMenu(self.menubar)
        self.menuOptions.setTitle('Preset')
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

    def on_select_texture_folder(self):

        folder_path = hou.ui.selectFile(hou.getenv("HOME"), title="Asset Folder", file_type=hou.fileType.Directory)

        if folder_path:
            self.texture_folder.setText(folder_path)

    def on_create_materialx(self):

        if not self.texture_folder.text() or not self.material_name.text():
            if self.debug: print("Select texture folder and material name")
            return


        context_test = self.context_box.currentText()
        context = hou.node("/mat")

        if context_test == "obj":
            obj: hou.Node = hou.node("/obj")
            context: hou.ShopNode = obj.node("materialx_collection")
            if context is None:
                context = obj.createNode("matnet", "materialx_collection")
        elif context_test == "stage":
            stage: hou.Node = hou.node("/stage")
            context: hou.ShopNode = stage.node("materialx_collection")
            if context is None:
                context = stage.createNode("materiallibrary", "materialx_collection")
                context.parm("matpathprefix").set("/materialx_collection/")
                context.parm("genpreviewshaders").set(0)

        mat_subnet: hou.VopNode = context.createNode("subnet", self.material_name.text() + "_MAT")

        for node in mat_subnet.children():
            node.destroy()

        files = importer.list_files_with_extensions(hou.expandString(self.texture_folder.text()))

        base_color = importer.filter_maps(files, importer.TEXTURE_DICT.get("BASE_COLOR"), "Base Color")

        roughness = importer.filter_maps(files, importer.TEXTURE_DICT.get("ROUGHNESS"), "Roughness")

        normal = importer.filter_maps(files, importer.TEXTURE_DICT.get("NORMAL"), "Normal")

        metalness = None
        if self.metalness_checkbox.isChecked():
            metalness = importer.filter_maps(files, importer.TEXTURE_DICT.get("METALNESS"), "Metalness")

        ao = None
        if self.ao_checkbox.isChecked():
            ao = importer.filter_maps(files, importer.TEXTURE_DICT.get("AO"), "Ambient Occlusion")

        translucency = None
        if self.translucency_checkbox.isChecked():
            translucency = importer.filter_maps(files, importer.TEXTURE_DICT.get("TRANSLUCENCY"), "Translucency")

        opacity = None
        if self.opacity_checkbox.isChecked():
            opacity = importer.filter_maps(files, importer.TEXTURE_DICT.get("OPACITY"), "Opacity")

        displacement = None
        if self.displacement_checkbox.isChecked():
            displacement = importer.filter_maps(files, importer.TEXTURE_DICT.get("DISPLACEMENT"), "Displacement")

        importer.create_materialx_network(mat_subnet, base_color, roughness, normal, ao=ao, displacement=displacement, metalness=metalness, 
            translucency_texture=translucency,
            translucency=self.translucency_checkbox.isChecked(), 
            opacity_texture=opacity, 
            opacity=self.opacity_checkbox.isChecked(), 
            color_variation=self.color_variation_checkbox.isChecked())

        mat_subnet.setMaterialFlag(True)
        mat_subnet.layoutChildren()

        context.layoutChildren()

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

        self.update_settings(preset)

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
        self.update_settings(SettingsPresetTemplate())

    def on_help(self):
        pass

    def update_settings(self, preset: SettingsPresetTemplate):
        self.color_variation_checkbox.setChecked(preset.color_variation)
        self.ao_checkbox.setChecked(preset.ao)
        self.translucency_checkbox.setChecked(preset.translucency)
        self.opacity_checkbox.setChecked(preset.opacity)
        self.metalness_checkbox.setChecked(preset.metalness)
        self.displacement_checkbox.setChecked(preset.displacement)

def preset_validation(preset):
    return True