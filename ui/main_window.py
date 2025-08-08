import sys
import os
import subprocess
import time
import platform
import ctypes
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QFrame, QSplitter, QTableView, QListWidget, QListWidgetItem,
    QComboBox, QProgressBar, QLabel, QStatusBar, QMessageBox,
    QInputDialog, QMenu, QStyledItemDelegate, QTableWidgetItem
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction, QKeyEvent, QPainter, QColor, QIcon
from PyQt6.QtCore import Qt, QTimer, QModelIndex, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

import google.generativeai as genai

# Import dialogs and workers from their respective modules
from .dialogs import SettingsDialog, AdvancedBurnSettingsDialog, EditSongDialog
from workers.download_worker import DownloadWorker
from workers.tagger_worker import TaggerWorker
from workers.burn_worker import BurnWorker
from workers.gemini_sender import GeminiSender
from workers.spotify_worker import SpotifyWorker
from workers.library_worker import LibraryWorker
import database
import config
import constants
from .ui_setup import UiSetup

class StarRatingDelegate(QStyledItemDelegate):
    """A custom delegate to display integer ratings as stars."""
    def paint(self, painter: QPainter, option, index: QModelIndex):
        if index.column() == 5: # The rating column
            rating = index.model().data(index, Qt.ItemDataRole.DisplayRole)
            if rating is not None:
                rating = int(rating)
                painter.save()
                painter.setPen(QColor(constants.STAR_COLOR))
                for i in range(5):
                    painter.drawText(option.rect.x() + i * 15, option.rect.y() + 15, "★" if i < rating else "☆")
                painter.restore()
                return
        super().paint(painter, option, index)

class AlphaBurnApp(QMainWindow):
    # Store CD state
    cd_state = {
        'drive': None,
        'space_mb': None,
        'finalized': None,
        'rewritable': None,
        'files': [],
        'needs_wipe': False
    }
    # --- CD Drive Controls ---
    def eject_selected_drive(self):
        drive = self.drive_selector.currentText()
        if not drive or "No drives" in drive:
            self.statusBar().showMessage("No drive selected.")
            return
        try:
            if platform.system() == "Windows":
                drive_letter = drive.split(':')[0]
                ctypes.windll.WINMM.mciSendStringW(f"set cdaudio!{drive_letter} door open", None, 0, None)
                self.statusBar().showMessage(f"Eject command sent to drive {drive}")
            elif platform.system() == "Linux":
                subprocess.run(["eject", f"/dev/{drive}"], check=True)
                self.statusBar().showMessage(f"Ejected drive {drive}")
            else:
                self.statusBar().showMessage("Ejection not supported on this OS.")
        except Exception as e:
            self.statusBar().showMessage(f"Failed to eject drive {drive}: {e}")

    def wipe_selected_drive(self):
        drive = self.drive_selector.currentText()
        if not drive or "No drives" in drive:
            self.statusBar().showMessage("No drive selected.")
            return
        reply = QMessageBox.question(self, "Confirm Wipe", f"Are you sure you want to wipe the disc in drive {drive}? This is irreversible.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            self.statusBar().showMessage(f"Wiping drive {drive}... please wait.")
            if platform.system() == "Windows":
                # Using a PowerShell command to format the disc
                command = ["powershell", "-Command", f"Get-CimInstance -ClassName Win32_CDROMDrive | Where-Object {{ $_.Drive -eq '{drive}' }} | Invoke-CimMethod -MethodName 'Format'"]
                subprocess.run(command, check=True, capture_output=True, text=True)
            elif platform.system() == "Linux":
                command = ["wodim", "-v", f"dev=/dev/{drive}", "blank=fast"]
                subprocess.run(command, check=True, capture_output=True, text=True)
            else:
                raise NotImplementedError("Wipe not supported on this OS.")
            self.statusBar().showMessage(f"Successfully wiped drive {drive}")
        except subprocess.CalledProcessError as e:
            self.statusBar().showMessage(f"Failed to wipe drive {drive}: {e.stderr}")
        except Exception as e:
            self.statusBar().showMessage(f"An error occurred during wipe: {e}")

    def read_selected_cd(self):
        drive = self.drive_selector.currentText()
        if not drive or "No drives" in drive:
            self.statusBar().showMessage("No drive selected.")
            return
        self.statusBar().showMessage(f"Reading disc in {drive}...")
        try:
            if platform.system() == "Windows":
                fs = ctypes.windll.kernel32.GetDiskFreeSpaceExW
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                fs(f"{drive}\\", ctypes.byref(free_bytes), ctypes.byref(total_bytes), None)
                self.cd_state['space_mb'] = total_bytes.value / (1024 * 1024)
                # A simple check for finalization might involve trying to write a small file
                # For now, we'll assume it's not finalized if it has space
                self.cd_state['finalized'] = self.cd_state['space_mb'] < 1
            elif platform.system() == "Linux":
                # Use a command-line tool to get disc info
                result = subprocess.run(["isoinfo", "-d", "-i", f"/dev/{drive}"], capture_output=True, text=True)
                output = result.stdout
                # Parse output for space and finalization status
                # This is a simplified example
                if "Volume size is: " in output:
                    size_str = output.split("Volume size is: ")[1].split()[0]
                    self.cd_state['space_mb'] = int(size_str) * 2 / 1024 # Assuming 2k blocks
                self.cd_state['finalized'] = "Status: complete" in output

            # For both platforms, list files
            files = os.listdir(f"{drive}\\")
            self.cd_state['files'] = files
            self.cd_content_table.setRowCount(len(files))
            for i, fname in enumerate(files):
                self.cd_content_table.setItem(i, 0, QTableWidgetItem(fname))
            self.statusBar().showMessage(f"Read disc in {drive} successfully.")
        except Exception as e:
            self.statusBar().showMessage(f"Failed to read disc: {e}")

    # --- Audio Player Controls ---
    def play_selected_audio(self):
        selected_indexes = self.library_table.selectionModel().selectedRows()
        if not selected_indexes:
            self.statusBar().showMessage("No track selected.")
            return
        filepath = self.library_model.item(selected_indexes[0].row(), 6).text()
        if not os.path.exists(filepath):
            self.statusBar().showMessage("File not found.")
            return
        self.media_player.setSource(QUrl.fromLocalFile(filepath))
        self.media_player.play()
        self.statusBar().showMessage(f"Playing: {os.path.basename(filepath)}")

    def pause_audio(self):
        self.media_player.pause()
        self.statusBar().showMessage("Playback paused.")

    def stop_audio(self):
        self.media_player.stop()
        self.statusBar().showMessage("Playback stopped.")
    def showEvent(self, event):
        super().showEvent(event)
        self.showMaximized()
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{constants.APP_NAME} v{constants.APP_VERSION}")
        self.showMaximized()

        # Apply futuristic stylesheet
        qss_path = os.path.join(os.path.dirname(__file__), 'alphaburn_theme.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

        self.download_path = config.get_setting('PATHS', 'DownloadFolder')
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        database.init_db()
        self.download_queue = []
        self.is_batch_downloading = False

        self.chat_history = None  # Will be set by UiSetup
        self.chat_input = None    # Will be set by UiSetup

        self.ui_setup = UiSetup(self)
        self.ui_setup.setup_ui()

        self._create_actions()
        self._create_menus()
        self._setup_library_model()
        self.load_library_from_db()
        self._populate_drives()

        self.statusBar().showMessage("Ready.")
        self.credit_label = QLabel("Developed by, Alpha & Joshua Perry")
        self.statusBar().addPermanentWidget(self.credit_label)

        # Initialize Media Player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)


    def _create_actions(self):
        self.open_roadmap_action = QAction("&Open Roadmap", self, triggered=self.open_roadmap)
        self.settings_action = QAction("&Settings", self, triggered=self.open_settings)
        self.rescan_library_action = QAction("&Rescan Library Folder", self, triggered=self.rescan_library_folder)

    def _create_menus(self):
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.settings_action)
        file_menu.addAction(self.rescan_library_action)
        file_menu.addSeparator()
        file_menu.addAction(QAction("E&xit", self, triggered=self.close))
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self.open_roadmap_action)

    def open_settings(self):
        SettingsDialog(self).exec()

    def open_advanced_burn_settings(self):
        dialog = AdvancedBurnSettingsDialog(self)
        dialog.exec()

    def open_roadmap(self):
        if not os.path.exists("Project Roadmap.txt"):
            QMessageBox.warning(self, "File Not Found", "Project Roadmap.txt not found.")
            return
        try: os.startfile("Project Roadmap.txt")
        except: QMessageBox.critical(self, "Error", "Could not open Project Roadmap.txt.")

    def _setup_library_model(self):
        self.library_model = QStandardItemModel(0, 7)
        self.library_model.setHorizontalHeaderLabels(['Title', 'Artist', 'Album', 'Year', 'Genre', 'Rating', 'File Path'])
        self.library_table.setModel(self.library_model)
        self.library_table.setItemDelegateForColumn(5, StarRatingDelegate(self))
        self.library_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.library_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.library_table.setColumnHidden(6, True)
        self.library_table.horizontalHeader().setStretchLastSection(True)
        self.library_table.setColumnWidth(0, constants.TITLE_WIDTH)
        self.library_table.setColumnWidth(1, constants.ARTIST_WIDTH)
        self.library_table.setColumnWidth(2, constants.ALBUM_WIDTH)
        self.library_table.setColumnWidth(5, constants.RATING_WIDTH)

    def load_library_from_db(self):
        print("[DEBUG] Loading library from DB...")
        self.library_model.removeRows(0, self.library_model.rowCount())
        songs = database.get_all_songs()
        print(f"[DEBUG] Songs from DB: {songs}")
        for song_data in songs:
            row = [QStandardItem(str(field)) for field in song_data]
            self.library_model.appendRow(row)
        self.statusBar().showMessage(f"Library loaded with {len(songs)} tracks.", 3000)

    def rescan_library_folder(self):
        self.rescan_library_action.setEnabled(False)
        self.library_worker = LibraryWorker(self.download_path)
        self.library_worker.finished.connect(self.on_library_scan_finished)
        self.library_worker.status_update.connect(self.statusBar().showMessage)
        self.library_worker.start()

    def on_library_scan_finished(self, found_new):
        print(f"[DEBUG] Library scan finished. Found new: {found_new}")
        if found_new > 0:
            QMessageBox.information(self, "Rescan Complete", f"Found and added {found_new} new tracks.")
            self.load_library_from_db()
        else:
            QMessageBox.information(self, "Rescan Complete", "No new tracks were found.")
            self.load_library_from_db()
        self.statusBar().showMessage("Ready.", 3000)
        self.rescan_library_action.setEnabled(True)

    def _populate_drives(self):
        # Windows: Use Win32_LogicalDisk to find optical drives (DriveType 5)
        import platform
        self.drive_selector.clear()
        drives = []
        if platform.system() == "Windows":
            try:
                import subprocess
                result = subprocess.run([
                    "powershell", "-Command",
                    "Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DriveType -eq 5 } | Select-Object -ExpandProperty DeviceID"
                ], capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line:
                        drives.append(line)
            except Exception as e:
                drives = []
        if not drives:
            self.drive_selector.addItem("No drives found")
        else:
            self.drive_selector.addItems(drives)

    def browse_music_directory(self):
        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "Select Music Directory", self.download_path)
        if dir_path:
            import config
            config.update_setting('PATHS', 'DownloadFolder', dir_path)
            self.download_path = dir_path
            self.load_library_from_db()

    def show_library_context_menu(self, position):
        indexes = self.library_table.selectionModel().selectedRows()
        if not indexes: return
        menu = QMenu()
        edit_action = QAction("Edit Metadata", self, triggered=self.edit_selected_song)
        menu.addAction(edit_action)
        rating_menu = menu.addMenu("Set Rating")
        for i in range(1, 6):
            rating_action = QAction(f"{'★' * i}{'☆' * (5-i)}", self)
            rating_action.triggered.connect(lambda checked, r=i: self.set_song_rating(r))
            rating_menu.addAction(rating_action)
        menu.exec(self.library_table.viewport().mapToGlobal(position))

    def edit_selected_song(self):
        indexes = self.library_table.selectionModel().selectedRows()
        if not indexes: return
        filepath = self.library_model.item(indexes[0].row(), 6).text()
        dialog = EditSongDialog(filepath, self)
        if dialog.exec(): self.load_library_from_db()

    def set_song_rating(self, rating):
        indexes = self.library_table.selectionModel().selectedRows()
        if not indexes: return
        for index in indexes:
            filepath = self.library_model.item(index.row(), 6).text()
            database.update_song_rating(filepath, rating)
            self.library_model.item(index.row(), 5).setText(str(rating))

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key.Key_Delete and self.burn_queue_list.hasFocus():
            for item in self.burn_queue_list.selectedItems(): self.burn_queue_list.takeItem(self.burn_queue_list.row(item))
            self.update_capacity_meter()
        else: super().keyPressEvent(e)

    def add_to_burn_queue_from_index(self, index): self.add_filepath_to_burn_queue(self.library_model.item(index.row(), 6).text())

    def add_filepath_to_burn_queue(self, filepath):
        if any(self.burn_queue_list.item(i).data(Qt.ItemDataRole.UserRole) == filepath for i in range(self.burn_queue_list.count())): return
        song_info = database.get_song_by_filepath(filepath)
        if song_info:
            item = QListWidgetItem(f"{song_info[1]} - {song_info[0]}"); item.setData(Qt.ItemDataRole.UserRole, filepath); self.burn_queue_list.addItem(item); self.update_capacity_meter()

    def update_capacity_meter(self):
        total_size = sum(os.path.getsize(self.burn_queue_list.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.burn_queue_list.count()) if os.path.exists(self.burn_queue_list.item(i).data(Qt.ItemDataRole.UserRole)))
        total_mb = total_size / (1024*1024); cap_mb = 700.0; pct = (total_mb / cap_mb) * 100 if cap_mb > 0 else 0
        self.capacity_progress.setStyleSheet("QProgressBar::chunk { background-color: red; }" if pct > 100 else ""); self.capacity_progress.setValue(int(pct)); self.capacity_label.setText(f"{total_mb:.1f} MB / {cap_mb:.1f} MB ({pct:.1f}%)")

    

    def start_burn_process(self):
        if self.burn_queue_list.count() == 0: QMessageBox.warning(self, "Empty Queue", "Burn queue is empty."); return
        drive = self.drive_selector.currentText()
        if not drive or "No drives" in drive or "Error" in drive: QMessageBox.warning(self, "No Drive", "Please select a valid optical drive."); return
        file_list = [self.burn_queue_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.burn_queue_list.count())]
        iso_path = os.path.join(os.getcwd(), f"AlphaBurn_{int(time.time())}.iso")
        self.burn_button.setEnabled(False)
        self.burn_worker = BurnWorker(drive, file_list, iso_path); self.burn_worker.finished.connect(self.on_burn_finished); self.burn_worker.error.connect(self.on_worker_error); self.burn_worker.progress.connect(lambda msg: self.statusBar().showMessage(msg)); self.burn_worker.start()

    def on_burn_finished(self, message): QMessageBox.information(self, "Success", message); self.statusBar().showMessage(message, 5000); self.burn_button.setEnabled(True)

    def start_download_handler(self):
        url = self.url_input.text()
        if not url: return
        if "spotify.com/playlist/" in url: self.start_spotify_playlist_download(url)
        else: self.download_queue.append(url); self.process_download_queue()

    def start_spotify_playlist_download(self, url):
        client_id = config.get_setting("API_KEYS", "spotify_client_id"); client_secret = config.get_setting("API_KEYS", "spotify_client_secret")
        if not client_id or not client_secret: QMessageBox.critical(self, "Spotify Credentials Missing", "Please set Spotify credentials in File > Settings."); return
        self.download_button.setEnabled(False); self.spotify_worker = SpotifyWorker(url, client_id, client_secret); self.spotify_worker.finished.connect(self.on_spotify_playlist_fetched); self.spotify_worker.error.connect(self.on_worker_error); self.spotify_worker.progress.connect(lambda msg: self.statusBar().showMessage(msg)); self.spotify_worker.start()

    def on_spotify_playlist_fetched(self, tracks):
        self.statusBar().showMessage(f"Found {len(tracks)} tracks. Starting batch download."); self.download_queue.extend(tracks); self.is_batch_downloading = True; self.process_download_queue()

    def process_download_queue(self):
        if self.is_batch_downloading and not self.download_queue:
            self.is_batch_downloading = False; self.download_button.setEnabled(True); QMessageBox.information(self, "Batch Download Complete", "Finished downloading all tracks."); return
        if self.download_queue and self.download_button.isEnabled():
            url = self.download_queue.pop(0); self.statusBar().showMessage(f"Downloading: {url} ({len(self.download_queue)} left)"); self.download_button.setEnabled(False)
            self.worker = DownloadWorker(url, self.download_path); self.worker.finished.connect(self.on_download_finished); self.worker.error.connect(self.on_worker_error); self.worker.start()

    def on_download_finished(self, info):
        title = info.get('title', 'Unknown Title')
        expected_filepath = os.path.join(self.download_path, f"{title}.mp3")

        if not os.path.exists(expected_filepath):
            self.on_worker_error(f"File not found for '{title}'.")
            return
        
        filepath = expected_filepath
        
        self.tagger = TaggerWorker(filepath, info.get('title','')); self.tagger.finished.connect(self.on_tagging_finished); self.tagger.error.connect(self.on_worker_error); self.tagger.status_update.connect(lambda msg: self.statusBar().showMessage(msg)); self.tagger.start()

    def on_tagging_finished(self, file_path, metadata):
        import shutil
        # Move to Local Music Folder if set
        local_music_folder = config.get_setting('PATHS', 'LocalMusicFolder')
        dest_path = file_path
        if local_music_folder and os.path.isdir(local_music_folder):
            try:
                dest_path = os.path.join(local_music_folder, os.path.basename(file_path))
                if os.path.abspath(file_path) != os.path.abspath(dest_path):
                    shutil.move(file_path, dest_path)
                    file_path = dest_path
            except Exception as e:
                self.statusBar().showMessage(f"Failed to move file: {e}", 5000)
        database.add_song(file_path, metadata)
        self.load_library_from_db()
        self.url_input.clear()
        self.download_button.setEnabled(True)
        if self.is_batch_downloading:
            QTimer.singleShot(500, self.process_download_queue)

    def on_worker_error(self, error_message):
        QMessageBox.critical(self, "Error", f"{error_message}"); self.statusBar().showMessage("Error occurred.", 5000)
        self.download_button.setEnabled(True); self.burn_button.setEnabled(True); self.chat_input.setEnabled(True)
        if self.is_batch_downloading: self.is_batch_downloading = False; self.download_queue.clear(); QMessageBox.warning(self, "Batch Download Halted", "An error occurred, halting the playlist download.")


    def restart_gemini_session(self):
        """Initializes or restarts the Gemini chat session."""
        self.statusBar().showMessage("Initializing Gemini session...")
        api_key = config.get_setting("API_KEYS", "gemini_api_key")
        model_name = config.get_setting("API_KEYS", "gemini_model", "gemini-1.5-pro")
        instructions_path = config.get_setting("API_KEYS", "system_instructions_file")

        if not api_key:
            self.chat_history.append("<b style='color:orange;'>AI Assistant is offline. Please set your Gemini API key in File > Settings.</b>")
            self.gemini_chat_session = None
            return

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            
            system_instructions = []
            if instructions_path and os.path.exists(instructions_path):
                with open(instructions_path, 'r', encoding='utf-8') as f:
                    system_instructions.append(f.read())
            else:
                # Fallback: always provide full context for Alpha's role and environment
                system_instructions.append(
                    'You are Alpha, the AI assistant in control of a CD burning and music downloader application called Alpha_Burn. '
                    'You always know your environment, your role, and your purpose: to help the user download, tag, manage, and burn music. '
                    'You can interact with the application to start burns, set settings, and answer questions about features (e.g., "what does finalize disc do?"). '
                    'You always filter your responses to only show the text output, and prefix your answers with "Alpha:". '
                    'If you need instructions for how to use the app, you have access to them. '
                    'You can move files, manage directories, and help the user with all music and disc operations.'
                )

            self.gemini_chat_session = model.start_chat(history=[])
            # Send the system instructions as the first message
            self.gemini_chat_session.send_message(system_instructions)

            self.statusBar().showMessage("Gemini session started.", 3000)
            self.chat_history.append("<b style='color:green;'>AI Assistant is online.</b>")

        except Exception as e:
            self.on_gemini_error_occurred(f"Failed to initialize Gemini: {e}")
            self.gemini_chat_session = None

    def send_chat_message(self):
        prompt = self.chat_input.text()
        if not prompt:
            return

        if self.gemini_chat_session is None:
            QMessageBox.warning(self, "Gemini Offline", "The AI assistant is not configured. Please set your API key in the settings.")
            return

        self.chat_history.append(f"<span style='color:#2196F3;'><b>You:</b> {prompt}</span>")
        self.chat_input.clear()
        self.chat_input.setEnabled(False)
        self.send_chat_button.setEnabled(False)
        self.statusBar().showMessage(f"Asking Gemini: '{prompt[:30]}...' ")

        self.thinking_label.setVisible(True)
        self.spinner_label.setVisible(True)
        if hasattr(self, 'spinner_movie') and self.spinner_movie:
            self.spinner_movie.start()

        cd_state_str = f"[CD STATE] Drive: {self.cd_state.get('drive')}, Space: {self.cd_state.get('space_mb')}MB, Finalized: {self.cd_state.get('finalized')}, Rewritable: {self.cd_state.get('rewritable')}, Files: {self.cd_state.get('files')}, Needs wipe: {self.cd_state.get('needs_wipe')}\n"
        full_prompt = cd_state_str + prompt

        self.gemini_sender = GeminiSender(self.gemini_chat_session, full_prompt)
        self.gemini_sender.response_received.connect(self.on_gemini_response_received)
        self.gemini_sender.error_occurred.connect(self.on_gemini_error_occurred)
        self.gemini_sender.start()

    def on_gemini_response_received(self, response):
        self.thinking_label.setVisible(False)
        self.spinner_label.setVisible(False)
        if hasattr(self, 'spinner_movie') and self.spinner_movie:
            self.spinner_movie.stop()
        # Only show the AI's text output, with prefix 'Alpha:'
        self.chat_history.append(f"<span style='color:#43A047;'><b>Alpha:</b> {response}</span>")
        self.chat_input.setEnabled(True)
        self.send_chat_button.setEnabled(True)
        self.statusBar().showMessage("Alpha response received.", 5000)

    def on_gemini_error_occurred(self, error_message):
        self.thinking_label.setVisible(False)
        self.spinner_label.setVisible(False)
        if hasattr(self, 'spinner_movie') and self.spinner_movie:
            self.spinner_movie.stop()
        self.chat_history.append(f"<b style='color:red;'>Gemini Error:</b> {error_message}")
        self.chat_input.setEnabled(True)
        self.send_chat_button.setEnabled(True)
        self.statusBar().showMessage("Gemini error occurred.", 5000)

    def save_preset(self):
        if self.burn_queue_list.count() == 0: return
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
        if ok and name:
            paths = [self.burn_queue_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.burn_queue_list.count())]
            config.update_setting("PRESETS", name, ",".join(paths))
            self._load_presets()
            self.preset_selector.setCurrentText(name)

    def delete_preset(self):
        name = self.preset_selector.currentText()
        if name in ["Standard Audio CD", "MP3 CD"]: return
        if QMessageBox.question(self, "Confirm", f"Delete preset '{name}'?") == QMessageBox.StandardButton.Yes:
            cfg = config.get_config()
            cfg.remove_option("PRESETS", name)
            with open(config.CONFIG_FILE, 'w') as configfile:
                cfg.write(configfile)
            self._load_presets()

    def _load_presets(self):
        current = self.preset_selector.currentText()
        self.preset_selector.clear(); self.preset_selector.addItems(["Standard Audio CD", "MP3 CD"])
        cfg = config.get_config()
        if cfg.has_section("PRESETS"):
            self.preset_selector.addItems(cfg.options("PRESETS"))
        self.preset_selector.setCurrentText(current if self.preset_selector.findText(current) != -1 else "Standard Audio CD")

    def load_preset(self):
        name = self.preset_selector.currentText(); self.burn_queue_list.clear()
        if name not in ["Standard Audio CD", "MP3 CD"]:
            paths_str = config.get_setting("PRESETS", name)
            paths = paths_str.split(',')
            for path in paths:
                if path: self.add_filepath_to_burn_queue(path)
        self.update_capacity_meter()