import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QFrame, QSplitter, QTableView, QListWidget, QListWidgetItem,
    QComboBox, QProgressBar, QLabel, QStatusBar, QMessageBox,
    QInputDialog, QMenu
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction, QKeyEvent
from PyQt6.QtCore import Qt, QSettings

# Import dialogs and workers from their respective modules
from .dialogs import SettingsDialog, AdvancedBurnSettingsDialog
from workers.download_worker import DownloadWorker
from workers.tagger_worker import TaggerWorker
from workers.burn_worker import BurnWorker
from workers.ai_worker import AIWorker

class AlphaBurnApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alpha_Burn v1.0")
        self.setGeometry(100, 100, 1400, 900)
        self.settings = QSettings("AlphaBurn", "Settings")
        self.download_path = os.path.join(os.getcwd(), "AlphaBurn_Downloads")
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._create_actions()
        self._create_menus()
        self._setup_ui()
        self._setup_library_model()
        self.load_library()
        self._populate_drives()

        self.statusBar().showMessage("Ready.")
        self.credit_label = QLabel("Developed by, Alpha & Joshua Perry")
        self.statusBar().addPermanentWidget(self.credit_label)

    def _create_actions(self):
        self.open_roadmap_action = QAction("&Open Roadmap", self, triggered=self.open_roadmap)
        self.settings_action = QAction("&Settings", self, triggered=self.open_settings)

    def _create_menus(self):
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.settings_action)
        file_menu.addSeparator()
        file_menu.addAction(QAction("E&xit", self, triggered=self.close))
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self.open_roadmap_action)

    def open_settings(self):
        SettingsDialog(self).exec()

    def open_roadmap(self):
        if not os.path.exists("roadmap.txt"):
            QMessageBox.warning(self, "File Not Found", "roadmap.txt not found.")
            return
        try:
            os.startfile("roadmap.txt")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open roadmap.txt: {e}")

    def _setup_library_model(self):
        self.library_model = QStandardItemModel(0, 6)
        self.library_model.setHorizontalHeaderLabels(['Title', 'Artist', 'Album', 'Year', 'Genre', 'File Path'])
        self.library_table.setModel(self.library_model)
        self.library_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.library_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.library_table.setColumnHidden(5, True)
        self.library_table.horizontalHeader().setStretchLastSection(True)
        self.library_table.setColumnWidth(0, 250)
        self.library_table.setColumnWidth(1, 150)
        self.library_table.setColumnWidth(2, 200)

    def load_library(self):
        # This will be replaced by database logic later
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3
        self.library_model.removeRows(0, self.library_model.rowCount())
        for filename in os.listdir(self.download_path):
            if filename.endswith(".mp3"):
                filepath = os.path.join(self.download_path, filename)
                try:
                    audio = MP3(filepath, ID3=ID3)
                    row = [QStandardItem(str(audio.get(k, [''])[0])) for k in ['TIT2', 'TPE1', 'TALB', 'TDRC', 'TCON']]
                    row.append(QStandardItem(filepath))
                    self.library_model.appendRow(row)
                except Exception:
                    pass

    def _populate_drives(self):
        self.drive_selector.clear()
        try:
            if sys.platform == "win32":
                process = subprocess.Popen('wmic logicaldisk where drivetype=5 get deviceid', stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, _ = process.communicate()
                drives = [line.strip() for line in stdout.split('\n') if line.strip() and "DeviceID" not in line]
                if drives:
                    self.drive_selector.addItems(drives)
                else:
                    self.drive_selector.addItem("No drives found")
            else:
                self.drive_selector.addItem("N/A (Linux/Mac)")
        except Exception as e:
            self.drive_selector.addItem("Error")
            self.statusBar().showMessage(f"Could not detect drives: {e}", 5000)

    def _setup_ui(self):
        top_bar = QHBoxLayout()
        self.url_input = QLineEdit(placeholderText="Enter URL...")
        top_bar.addWidget(self.url_input)
        self.download_button = QPushButton("Download")
        top_bar.addWidget(self.download_button)
        self.ai_curator_input = QLineEdit(placeholderText="Ask Gemini AI...")
        top_bar.addWidget(self.ai_curator_input, 1)
        self.main_layout.addLayout(top_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(splitter, 1)

        left_pane = QFrame()
        left_layout = QVBoxLayout(left_pane)
        self.library_table = QTableView()
        left_layout.addWidget(self.library_table)
        splitter.addWidget(left_pane)

        right_pane = QFrame()
        right_layout = QVBoxLayout(right_pane)
        
        drive_layout = QHBoxLayout()
        drive_layout.addWidget(QLabel("Drive:"))
        self.drive_selector = QComboBox()
        drive_layout.addWidget(self.drive_selector)
        drive_layout.addWidget(QLabel("Preset:"))
        self.preset_selector = QComboBox()
        drive_layout.addWidget(self.preset_selector)
        right_layout.addLayout(drive_layout)
        
        preset_btn_layout = QHBoxLayout()
        self.save_preset_button = QPushButton("Save Preset")
        preset_btn_layout.addWidget(self.save_preset_button)
        self.delete_preset_button = QPushButton("Delete Preset")
        preset_btn_layout.addWidget(self.delete_preset_button)
        right_layout.addLayout(preset_btn_layout)
        
        self.burn_queue_list = QListWidget()
        right_layout.addWidget(self.burn_queue_list)
        
        cap_layout = QHBoxLayout()
        self.capacity_label = QLabel("0.0 MB / 700.0 MB (0%)")
        cap_layout.addWidget(self.capacity_label)
        self.capacity_progress = QProgressBar()
        cap_layout.addWidget(self.capacity_progress)
        right_layout.addLayout(cap_layout)
        
        burn_ctrl_layout = QHBoxLayout()
        self.advanced_burn_button = QPushButton("Advanced...")
        burn_ctrl_layout.addStretch()
        burn_ctrl_layout.addWidget(self.advanced_burn_button)
        self.burn_button = QPushButton("Burn Disc")
        self.burn_button.setStyleSheet("background-color: #4CAF50;")
        burn_ctrl_layout.addWidget(self.burn_button)
        right_layout.addLayout(burn_ctrl_layout)
        
        splitter.addWidget(right_pane)

        # Connect signals
        self.library_table.doubleClicked.connect(self.add_to_burn_queue_from_index)
        self.download_button.clicked.connect(self.start_download)
        self.save_preset_button.clicked.connect(self.save_preset)
        self.delete_preset_button.clicked.connect(self.delete_preset)
        self.preset_selector.activated.connect(self.load_preset)
        self.advanced_burn_button.clicked.connect(self.open_advanced_burn_settings)
        self.burn_button.clicked.connect(self.start_burn_process)
        self.ai_curator_input.returnPressed.connect(self.start_ai_curation)
        
        self._load_presets()

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key.Key_Delete and self.burn_queue_list.hasFocus():
            for item in self.burn_queue_list.selectedItems():
                self.burn_queue_list.takeItem(self.burn_queue_list.row(item))
            self.update_capacity_meter()
        else:
            super().keyPressEvent(e)

    def add_to_burn_queue_from_index(self, index):
        self.add_filepath_to_burn_queue(self.library_model.item(index.row(), 5).text())

    def add_filepath_to_burn_queue(self, filepath):
        if any(self.burn_queue_list.item(i).data(Qt.ItemDataRole.UserRole) == filepath for i in range(self.burn_queue_list.count())):
            return
        for row in range(self.library_model.rowCount()):
            if self.library_model.item(row, 5).text() == filepath:
                item = QListWidgetItem(f"{self.library_model.item(row, 1).text()} - {self.library_model.item(row, 0).text()}")
                item.setData(Qt.ItemDataRole.UserRole, filepath)
                self.burn_queue_list.addItem(item)
                self.update_capacity_meter()
                break

    def update_capacity_meter(self):
        total_size = sum(os.path.getsize(self.burn_queue_list.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.burn_queue_list.count()) if os.path.exists(self.burn_queue_list.item(i).data(Qt.ItemDataRole.UserRole)))
        total_mb = total_size / (1024 * 1024)
        cap_mb = 700.0
        pct = (total_mb / cap_mb) * 100 if cap_mb > 0 else 0
        self.capacity_progress.setStyleSheet("QProgressBar::chunk { background-color: red; }" if pct > 100 else "")
        self.capacity_progress.setValue(int(pct))
        self.capacity_label.setText(f"{total_mb:.1f} MB / {cap_mb:.1f} MB ({pct:.1f}%)")

    def start_ai_curation(self):
        prompt = self.ai_curator_input.text()
        if not prompt:
            return
        api_key = self.settings.value("gemini_api_key")
        if not api_key:
            QMessageBox.critical(self, "API Key Missing", "Please set your Gemini API key in File > Settings.")
            return
            
        self.statusBar().showMessage(f"Asking Gemini AI: '{prompt}'...")
        self.ai_curator_input.setEnabled(False)
        self.ai_worker = AIWorker(prompt, self.library_model, api_key)
        self.ai_worker.finished.connect(self.on_ai_curation_finished)
        self.ai_worker.error.connect(self.on_worker_error)
        self.ai_worker.start()

    def on_ai_curation_finished(self, filepaths):
        self.statusBar().showMessage(f"AI selected {len(filepaths)} tracks.", 5000)
        self.burn_queue_list.clear()
        for path in filepaths:
            self.add_filepath_to_burn_queue(path)
        self.ai_curator_input.clear()
        self.ai_curator_input.setEnabled(True)

    def start_burn_process(self):
        if self.burn_queue_list.count() == 0:
            QMessageBox.warning(self, "Empty Queue", "Burn queue is empty.")
            return
        drive = self.drive_selector.currentText()
        if not drive or "No drives" in drive or "Error" in drive:
            QMessageBox.warning(self, "No Drive", "Please select a valid optical drive.")
            return
        file_list = [self.burn_queue_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.burn_queue_list.count())]
        iso_path = os.path.join(os.getcwd(), f"AlphaBurn_{int(time.time())}.iso")
        
        self.burn_button.setEnabled(False)
        self.burn_worker = BurnWorker(drive, file_list, iso_path)
        self.burn_worker.finished.connect(self.on_burn_finished)
        self.burn_worker.error.connect(self.on_worker_error)
        self.burn_worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        self.burn_worker.start()

    def on_burn_finished(self, message):
        QMessageBox.information(self, "Success", message)
        self.statusBar().showMessage(message, 5000)
        self.burn_button.setEnabled(True)

    def start_download(self):
        url = self.url_input.text()
        if not url:
            return
        self.download_button.setEnabled(False)
        self.worker = DownloadWorker(url, self.download_path)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.progress.connect(lambda d: self.statusBar().showMessage(f"Downloading... {d.get('_percent_str', '0%')}"))
        self.worker.start()

    def on_download_finished(self, info):
        filepath = info.get('filepath')
        if not filepath or not os.path.exists(filepath):
            self.on_worker_error(f"File not found for '{info.get('title','')}'.")
            return
        self.tagger = TaggerWorker(filepath, info.get('title',''))
        self.tagger.finished.connect(self.on_tagging_finished)
        self.tagger.error.connect(self.on_worker_error)
        self.tagger.status_update.connect(lambda msg: self.statusBar().showMessage(msg))
        self.tagger.start()

    def on_tagging_finished(self, file_path, metadata):
        self.statusBar().showMessage(f"Tagged '{metadata['title']}'.", 5000)
        row = [QStandardItem(metadata.get(k, '')) for k in ['title', 'artist', 'album', 'year', 'genre']]
        row.append(QStandardItem(file_path))
        self.library_model.appendRow(row)
        self.download_button.setEnabled(True)
        self.url_input.clear()

    def on_worker_error(self, error_message):
        QMessageBox.critical(self, "Error", f"{error_message}")
        self.statusBar().showMessage("Error occurred.", 5000)
        self.download_button.setEnabled(True)
        self.burn_button.setEnabled(True)
        self.ai_curator_input.setEnabled(True)

    def save_preset(self):
        if self.burn_queue_list.count() == 0:
            return
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
        if ok and name:
            if name in ["Standard Audio CD", "MP3 CD"]:
                QMessageBox.warning(self, "Invalid Name", "Cannot overwrite defaults.")
                return
            paths = [self.burn_queue_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.burn_queue_list.count())]
            self.settings.setValue(f"presets/{name}", paths)
            self._load_presets()
            self.preset_selector.setCurrentText(name)

    def delete_preset(self):
        name = self.preset_selector.currentText()
        if name in ["Standard Audio CD", "MP3 CD"]:
            return
        if QMessageBox.question(self, "Confirm", f"Delete preset '{name}'?") == QMessageBox.StandardButton.Yes:
            self.settings.remove(f"presets/{name}")
            self._load_presets()

    def _load_presets(self):
        current = self.preset_selector.currentText()
        self.preset_selector.clear()
        self.preset_selector.addItems(["Standard Audio CD", "MP3 CD"])
        self.settings.beginGroup("presets")
        self.preset_selector.addItems(self.settings.childKeys())
        self.settings.endGroup()
        self.preset_selector.setCurrentText(current if self.preset_selector.findText(current) != -1 else "Standard Audio CD")

    def load_preset(self):
        name = self.preset_selector.currentText()
        self.burn_queue_list.clear()
        if name not in ["Standard Audio CD", "MP3 CD"]:
            paths = self.settings.value(f"presets/{name}", [])
            for path in paths:
                self.add_filepath_to_burn_queue(path)
        self.update_capacity_meter()
