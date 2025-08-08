from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QComboBox, 
    QCheckBox, QLabel, QDialogButtonBox
)
# Import the new config module instead of QSettings
import config

class EditSongDialog(QDialog):
    """A dialog for manually editing a song's metadata."""
    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Metadata")
        self.filepath = filepath
        
        # This will now need to be updated to use the new database functions
        # For now, this structure remains the same as it's called from main_window
        # which will be updated next.
        import database
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
        import database
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
        layout = QVBoxLayout(self)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Burn Speed:"))
        self.burn_speed_selector = QComboBox()
        self.burn_speed_selector.addItems(["Max", "48x", "32x", "24x", "16x", "8x", "4x"])
        speed_layout.addWidget(self.burn_speed_selector)
        layout.addLayout(speed_layout)
        self.burn_proof_checkbox = QCheckBox("Enable Burn-Proof")
        layout.addWidget(self.burn_proof_checkbox)
        self.test_mode_checkbox = QCheckBox("Enable Test Mode")
        layout.addWidget(self.test_mode_checkbox)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class SettingsDialog(QDialog):
    """Settings dialog now reads from and writes to config.ini."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)
        
        # Gemini API Key
        gemini_layout = QHBoxLayout()
        gemini_layout.addWidget(QLabel("Gemini AI API Key:"))
        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_api_key_input.setToolTip("Your Google AI Studio API Key for Gemini.")
        self.gemini_api_key_input.setText(config.get_setting("API_KEYS", "gemini_api_key"))
        gemini_layout.addWidget(self.gemini_api_key_input)
        layout.addLayout(gemini_layout)

        # Spotify Client ID
        spotify_id_layout = QHBoxLayout()
        spotify_id_layout.addWidget(QLabel("Spotify Client ID:"))
        self.spotify_id_input = QLineEdit()
        self.spotify_id_input.setToolTip("Your Client ID from the Spotify Developer Dashboard.")
        self.spotify_id_input.setText(config.get_setting("API_KEYS", "spotify_client_id"))
        spotify_id_layout.addWidget(self.spotify_id_input)
        layout.addLayout(spotify_id_layout)

        # Spotify Client Secret
        spotify_secret_layout = QHBoxLayout()
        spotify_secret_layout.addWidget(QLabel("Spotify Client Secret:"))
        self.spotify_secret_input = QLineEdit()
        self.spotify_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.spotify_secret_input.setToolTip("Your Client Secret from the Spotify Developer Dashboard.")
        self.spotify_secret_input.setText(config.get_setting("API_KEYS", "spotify_client_secret"))
        spotify_secret_layout.addWidget(self.spotify_secret_input)
        layout.addLayout(spotify_secret_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        """Saves all settings to the config.ini file."""
        config.update_setting("API_KEYS", "gemini_api_key", self.gemini_api_key_input.text())
        config.update_setting("API_KEYS", "spotify_client_id", self.spotify_id_input.text())
        config.update_setting("API_KEYS", "spotify_client_secret", self.spotify_secret_input.text())
        super().accept()
