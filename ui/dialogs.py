from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QComboBox, 
    QCheckBox, QLabel, QDialogButtonBox
)
import config
import database

class EditSongDialog(QDialog):
    """A dialog for manually editing a song's metadata."""
    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Metadata")
        # Apply futuristic stylesheet if not already set by parent
        if not self.styleSheet():
            import os
            qss_path = os.path.join(os.path.dirname(__file__), 'alphaburn_theme.qss')
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        self.filepath = filepath
        song_data = database.get_song_by_filepath(self.filepath)
        if not song_data:
            self.close()
            return
        title, artist, album, year, genre, rating = song_data
        layout = QGridLayout(self)
        layout.addWidget(QLabel("Title:"), 0, 0); self.title_edit = QLineEdit(title); layout.addWidget(self.title_edit, 0, 1)
        layout.addWidget(QLabel("Artist:"), 1, 0); self.artist_edit = QLineEdit(artist); layout.addWidget(self.artist_edit, 1, 1)
        layout.addWidget(QLabel("Album:"), 2, 0); self.album_edit = QLineEdit(album); layout.addWidget(self.album_edit, 2, 1)
        layout.addWidget(QLabel("Year:"), 3, 0); self.year_edit = QLineEdit(str(year)); layout.addWidget(self.year_edit, 3, 1)
        layout.addWidget(QLabel("Genre:"), 4, 0); self.genre_edit = QLineEdit(genre); layout.addWidget(self.genre_edit, 4, 1)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box, 5, 0, 1, 2)

    def accept(self):
        new_metadata = {
            'title': self.title_edit.text(), 'artist': self.artist_edit.text(),
            'album': self.album_edit.text(), 'year': self.year_edit.text(),
            'genre': self.genre_edit.text()
        }
        database.update_song_metadata(self.filepath, new_metadata)
        super().accept()


class AdvancedBurnSettingsDialog(QDialog):
    # This dialog doesn't use persistent settings yet, so it remains unchanged for now.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Burn Settings")
        # Apply futuristic stylesheet if not already set by parent
        if not self.styleSheet():
            import os
            qss_path = os.path.join(os.path.dirname(__file__), 'alphaburn_theme.qss')
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        layout = QVBoxLayout(self)
        speed_layout = QHBoxLayout()
        speed_label = QLabel("Burn Speed:")
        speed_label.setToolTip("Select the speed at which the disc will be burned. Lower speeds can improve reliability on some media.")
        speed_layout.addWidget(speed_label)
        self.burn_speed_selector = QComboBox()
        self.burn_speed_selector.addItems(["Max", "48x", "32x", "24x", "16x", "8x", "4x"])
        self.burn_speed_selector.setToolTip("Choose the desired burn speed for your disc.")
        speed_layout.addWidget(self.burn_speed_selector)
        layout.addLayout(speed_layout)
        self.burn_proof_checkbox = QCheckBox("Enable Burn-Proof")
        self.burn_proof_checkbox.setToolTip("Enable buffer underrun protection to prevent failed burns on supported drives.")
        layout.addWidget(self.burn_proof_checkbox)
        self.test_mode_checkbox = QCheckBox("Enable Test Mode")
        self.test_mode_checkbox.setToolTip("Simulate the burn process without actually writing data to the disc. Useful for testing.")
        layout.addWidget(self.test_mode_checkbox)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Apply).setToolTip("Apply these advanced settings without closing the dialog.")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setToolTip("Cancel and close this dialog without saving changes.")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class SettingsDialog(QDialog):
    """Settings dialog now reads from and writes to config.ini."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        # Apply futuristic stylesheet if not already set by parent
        if not self.styleSheet():
            import os
            qss_path = os.path.join(os.path.dirname(__file__), 'alphaburn_theme.qss')
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        layout = QVBoxLayout(self)
        
        # Gemini API Key
        gemini_layout = QHBoxLayout()
        gemini_api_label = QLabel("Gemini AI API Key:")
        gemini_api_label.setToolTip("Your Google AI Studio API Key for Gemini.")
        gemini_layout.addWidget(gemini_api_label)
        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_api_key_input.setToolTip("Your Google AI Studio API Key for Gemini.")
        self.gemini_api_key_input.setText(config.get_setting("API_KEYS", "gemini_api_key"))
        gemini_layout.addWidget(self.gemini_api_key_input)
        layout.addLayout(gemini_layout)

        # Gemini Model Selection
        gemini_model_layout = QHBoxLayout()
        gemini_model_label = QLabel("Gemini Model:")
        gemini_model_label.setToolTip("Select the Gemini API model to use.")
        gemini_model_layout.addWidget(gemini_model_label)
        self.gemini_model_selector = QComboBox()
        self.gemini_model_selector.addItems(["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "custom"])
        self.gemini_model_selector.setToolTip("Select the Gemini API model to use.")
        gemini_model_layout.addWidget(self.gemini_model_selector)
        layout.addLayout(gemini_model_layout)

        # Custom Gemini Model Input
        self.custom_gemini_model_input = QLineEdit()
        self.custom_gemini_model_input.setPlaceholderText("Enter custom model name (e.g., gemini-pro-latest)")
        self.custom_gemini_model_input.setToolTip("Enter a custom Gemini model name if 'custom' is selected above.")
        layout.addWidget(self.custom_gemini_model_input)

        self.gemini_model_selector.currentTextChanged.connect(self.on_gemini_model_changed)

        # Load existing settings
        selected_model = config.get_setting("API_KEYS", "gemini_model", "gemini-1.5-pro")
        if selected_model in ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]:
            self.gemini_model_selector.setCurrentText(selected_model)
            self.custom_gemini_model_input.setVisible(False)
        else:
            self.gemini_model_selector.setCurrentText("custom")
            self.custom_gemini_model_input.setText(selected_model)
            self.custom_gemini_model_input.setVisible(True)

        # Spotify Client ID
        spotify_id_layout = QHBoxLayout()
        spotify_id_label = QLabel("Spotify Client ID:")
        spotify_id_label.setToolTip("Your Client ID from the Spotify Developer Dashboard.")
        spotify_id_layout.addWidget(spotify_id_label)
        self.spotify_id_input = QLineEdit()
        self.spotify_id_input.setToolTip("Your Client ID from the Spotify Developer Dashboard.")
        self.spotify_id_input.setText(config.get_setting("API_KEYS", "spotify_client_id"))
        spotify_id_layout.addWidget(self.spotify_id_input)
        layout.addLayout(spotify_id_layout)

        # Spotify Client Secret
        spotify_secret_layout = QHBoxLayout()
        spotify_secret_label = QLabel("Spotify Client Secret:")
        spotify_secret_label.setToolTip("Your Client Secret from the Spotify Developer Dashboard.")
        spotify_secret_layout.addWidget(spotify_secret_label)
        self.spotify_secret_input = QLineEdit()
        self.spotify_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.spotify_secret_input.setToolTip("Your Client Secret from the Spotify Developer Dashboard.")
        self.spotify_secret_input.setText(config.get_setting("API_KEYS", "spotify_client_secret"))
        spotify_secret_layout.addWidget(self.spotify_secret_input)
        layout.addLayout(spotify_secret_layout)


        # System Instructions for AI
        sysinst_layout = QVBoxLayout()
        sysinst_label = QLabel("AI System Instructions:")
        sysinst_label.setToolTip("Custom system instructions for the AI assistant.")
        sysinst_layout.addWidget(sysinst_label)
        self.system_instructions_input = QLineEdit()
        self.system_instructions_input.setPlaceholderText("e.g. You are the AI inside a CD burner app...")
        self.system_instructions_input.setToolTip("Custom system instructions for the AI assistant.")
        self.system_instructions_input.setText(config.get_setting("API_KEYS", "system_instructions", "You are the AI assistant inside a CD burner application. You can search for music, download playlists, and assist with burning discs."))
        sysinst_layout.addWidget(self.system_instructions_input)
        layout.addLayout(sysinst_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Apply).setToolTip("Apply changes without closing the dialog.")
        button_box.button(QDialogButtonBox.StandardButton.Ok).setToolTip("Apply changes and close the dialog.")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setToolTip("Cancel and close the dialog without saving changes.")
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        button_box.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self.ok_and_close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_gemini_model_changed(self, text):
        self.custom_gemini_model_input.setVisible(text == "custom")



    def apply_settings(self):
        """Saves all settings to the config.ini file, but does not close the dialog."""
        config.update_setting("API_KEYS", "gemini_api_key", self.gemini_api_key_input.text())
        if self.gemini_model_selector.currentText() == "custom":
            config.update_setting("API_KEYS", "gemini_model", self.custom_gemini_model_input.text())
        else:
            config.update_setting("API_KEYS", "gemini_model", self.gemini_model_selector.currentText())
        config.update_setting("API_KEYS", "spotify_client_id", self.spotify_id_input.text())
        config.update_setting("API_KEYS", "spotify_client_secret", self.spotify_secret_input.text())
        config.update_setting("API_KEYS", "system_instructions", self.system_instructions_input.text())

    def ok_and_close(self):
        self.apply_settings()
        super().accept()
