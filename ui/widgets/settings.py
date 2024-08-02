from PySide2.QtWidgets import QVBoxLayout, QCheckBox, QGroupBox

from ...modules.settings_preset_template import SettingsPresetTemplate

class SettingsWidget(QGroupBox):

    def __init__(self, parent=None):

        super(SettingsWidget, self).__init__(parent)

        self.main_layout = QVBoxLayout()
        self.setTitle("Settings")
        self.setLayout(self.main_layout)
        
        self.color_variation_checkbox = QCheckBox("Color variation")
        self.ao_checkbox = QCheckBox("AO")
        self.translucency_checkbox = QCheckBox("Translucency")
        self.opacity_checkbox = QCheckBox("Opacity")
        self.metalness_checkbox = QCheckBox("Metalness")
        self.displacement_checkbox = QCheckBox("Displacement")

        self.main_layout.addWidget(self.color_variation_checkbox)
        self.main_layout.addWidget(self.ao_checkbox)
        self.main_layout.addWidget(self.translucency_checkbox)
        self.main_layout.addWidget(self.opacity_checkbox)
        self.main_layout.addWidget(self.metalness_checkbox)
        self.main_layout.addWidget(self.displacement_checkbox)

    @property
    def settings(self):
        return SettingsPresetTemplate(
            self.color_variation_checkbox.isChecked(),
            self.ao_checkbox.isChecked(),
            self.translucency_checkbox.isChecked(),
            self.opacity_checkbox.isChecked(),
            self.metalness_checkbox.isChecked(),
            self.displacement_checkbox.isChecked()
        )

    def update_settings(self, preset: SettingsPresetTemplate):
        self.color_variation_checkbox.setChecked(preset.color_variation)
        self.ao_checkbox.setChecked(preset.ao)
        self.translucency_checkbox.setChecked(preset.translucency)
        self.opacity_checkbox.setChecked(preset.opacity)
        self.metalness_checkbox.setChecked(preset.metalness)
        self.displacement_checkbox.setChecked(preset.displacement)