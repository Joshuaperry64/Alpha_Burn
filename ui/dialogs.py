from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, 
    QCheckBox, QLabel, QDialogButtonBox
)
from PyQt6.QtCore import QSettings

class AdvancedBurnSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Burn Settings")
        self.settings = QSettings("AlphaBurn", "Settings")
        layout = QVBoxLayout(self)

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Burn Speed:"))
        self.burn_speed_selector = QComboBox()
        self.burn_speed_selector.addItems(["Max", "48x", "32x", "24x", "16x", "8x", "4x"])
        self.burn_speed_selector.setToolTip("Select the desired write speed. 'Max' is usually the best option.")
        current_speed = self.settings.value("burn_speed", "Max")
        self.burn_speed_selector.setCurrentText(current_speed)
        speed_layout.addWidget(self.burn_speed_selector)
        layout.addLayout(speed_layout)

        self.burn_proof_checkbox = QCheckBox("Enable Burn-Proof")
        self.burn_proof_checkbox.setToolTip("Prevents buffer underrun errors, which can ruin a disc.")
        self.burn_proof_checkbox.setChecked(self.settings.value("burn_proof", True, type=bool))
        layout.addWidget(self.burn_proof_checkbox)

        self.test_mode_checkbox = QCheckBox("Enable Test Mode")
        self.test_mode_checkbox.setToolTip("Simulates the burn process without actually writing data to the disc.")
        self.test_mode_checkbox.setChecked(self.settings.value("test_mode", False, type=bool))
        layout.addWidget(self.test_mode_checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        self.settings.setValue("burn_speed", self.burn_speed_selector.currentText())
        self.settings.setValue("burn_proof", self.burn_proof_checkbox.isChecked())
        self.settings.setValue("test_mode", self.test_mode_checkbox.isChecked())
        super().accept()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = QSettings("AlphaBurn", "Settings")
        layout = QVBoxLayout(self)
        
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("Gemini AI API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setToolTip("Your Google AI Studio API Key for Gemini.")
        self.api_key_input.setText(self.settings.value("gemini_api_key", ""))
        api_layout.addWidget(self.api_key_input)
        layout.addLayout(api_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        self.settings.setValue("gemini_api_key", self.api_key_input.text())
        super().accept()
