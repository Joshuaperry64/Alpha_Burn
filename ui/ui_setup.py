from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFrame, QSplitter, 
    QTableView, QListWidget, QComboBox, QProgressBar, QLabel, QWidget, QTextEdit
)
from PyQt6.QtCore import Qt

class UiSetup:
    """Handles the setup of UI components for the main window."""
    def __init__(self, main_window):
        self.main_window = main_window

    def setup_ui(self):
        self.create_main_layout()
        self.create_top_bar()
        self.create_central_splitter()
        self.create_left_pane()
        self.create_right_pane()
        self.connect_signals()

    def create_main_layout(self):
        self.main_window.central_widget = QWidget()
        self.main_window.setCentralWidget(self.main_window.central_widget)
        self.main_window.main_layout = QVBoxLayout(self.main_window.central_widget)

    def create_top_bar(self):
        top_bar = QHBoxLayout()
        self.main_window.url_input = QLineEdit(placeholderText="Enter URL or Spotify Playlist...")
        self.main_window.url_input.setToolTip("Paste a YouTube or Spotify playlist URL here to download music.")
        top_bar.addWidget(self.main_window.url_input)
        self.main_window.download_button = QPushButton("Download")
        self.main_window.download_button.setToolTip("Download the music or playlist from the entered URL.")
        top_bar.addWidget(self.main_window.download_button)
        self.main_window.send_chat_button = QPushButton("Send")
        self.main_window.send_chat_button.setToolTip("Send your message to the AI assistant.")
        top_bar.addWidget(self.main_window.send_chat_button)
        self.main_window.main_layout.addLayout(top_bar)

    def create_central_splitter(self):
        self.main_window.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_window.main_layout.addWidget(self.main_window.splitter, 1)

    def create_left_pane(self):
        left_pane = QFrame()
        left_layout = QVBoxLayout(left_pane)
        self.main_window.library_table = QTableView()
        self.main_window.library_table.setToolTip("Your local music library. Double-click a track to add it to the burn queue.")
        left_layout.addWidget(self.main_window.library_table)
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QSlider
        player_layout = QHBoxLayout()
        self.main_window.audio_play_button = QPushButton("Play")
        self.main_window.audio_play_button.setToolTip("Play the selected track from your library or CD.")
        self.main_window.audio_pause_button = QPushButton("Pause")
        self.main_window.audio_pause_button.setToolTip("Pause playback.")
        self.main_window.audio_stop_button = QPushButton("Stop")
        self.main_window.audio_stop_button.setToolTip("Stop playback.")
        self.main_window.audio_slider = QSlider(Qt.Orientation.Horizontal)
        self.main_window.audio_slider.setToolTip("Seek within the current track.")
        player_layout.addWidget(self.main_window.audio_play_button)
        player_layout.addWidget(self.main_window.audio_pause_button)
        player_layout.addWidget(self.main_window.audio_stop_button)
        player_layout.addWidget(self.main_window.audio_slider)
        left_layout.addLayout(player_layout)
        self.main_window.splitter.addWidget(left_pane)

    def create_right_pane(self):
        right_pane = QFrame()
        right_layout = QVBoxLayout(right_pane)

        self.create_drive_selection(right_layout)
        self.create_preset_buttons(right_layout)

        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
        self.main_window.cd_content_table = QTableWidget()
        self.main_window.cd_content_table.setColumnCount(1)
        self.main_window.cd_content_table.setHorizontalHeaderLabels(["CD Content"])
        self.main_window.cd_content_table.setToolTip("Contents of the currently inserted CD. Tracks and files will appear here after scanning.")
        right_layout.addWidget(self.main_window.cd_content_table)

        self.main_window.burn_queue_list = QListWidget()
        self.main_window.burn_queue_list.setToolTip("Tracks queued for burning to disc. Drag and drop to reorder.")
        right_layout.addWidget(self.main_window.burn_queue_list)

        self.create_capacity_meter(right_layout)
        self.create_burn_controls(right_layout)
        self.create_chat_area(right_layout)

        self.main_window.splitter.addWidget(right_pane)

    def create_drive_selection(self, layout):
        drive_layout = QHBoxLayout()
        drive_layout.addWidget(QLabel("Drive:"))
        self.main_window.drive_selector = QComboBox()
        drive_layout.addWidget(self.main_window.drive_selector)
        from PyQt6.QtWidgets import QPushButton
        # Add Eject, Wipe, Read CD, Refresh buttons
        self.main_window.eject_drive_button = QPushButton("Eject")
        self.main_window.eject_drive_button.setToolTip("Eject the selected drive")
        drive_layout.addWidget(self.main_window.eject_drive_button)
        self.main_window.wipe_drive_button = QPushButton("Wipe")
        self.main_window.wipe_drive_button.setToolTip("Erase a rewritable CD")
        drive_layout.addWidget(self.main_window.wipe_drive_button)
        self.main_window.read_cd_button = QPushButton("Read CD")
        self.main_window.read_cd_button.setToolTip("Read the contents of the CD")
        drive_layout.addWidget(self.main_window.read_cd_button)
        self.main_window.refresh_drive_button = QPushButton("Refresh")
        self.main_window.refresh_drive_button.setToolTip("Refresh available drives")
        drive_layout.addWidget(self.main_window.refresh_drive_button)
        self.main_window.browse_music_button = QPushButton("Browse...")
        self.main_window.browse_music_button.setToolTip("Select your music directory")
        drive_layout.addWidget(self.main_window.browse_music_button)
        drive_layout.addWidget(QLabel("Preset:"))
        self.main_window.preset_selector = QComboBox()
        drive_layout.addWidget(self.main_window.preset_selector)
        layout.addLayout(drive_layout)

    def create_preset_buttons(self, layout):
        preset_btn_layout = QHBoxLayout()
        self.main_window.save_preset_button = QPushButton("Save Preset")
        preset_btn_layout.addWidget(self.main_window.save_preset_button)
        self.main_window.delete_preset_button = QPushButton("Delete Preset")
        preset_btn_layout.addWidget(self.main_window.delete_preset_button)
        layout.addLayout(preset_btn_layout)

    def create_capacity_meter(self, layout):
        cap_layout = QHBoxLayout()
        self.main_window.capacity_label = QLabel("0.0 MB / 700.0 MB (0%)")
        self.main_window.capacity_label.setToolTip("Shows the total size of your burn queue compared to the disc's capacity.")
        cap_layout.addWidget(self.main_window.capacity_label)
        self.main_window.capacity_progress = QProgressBar()
        self.main_window.capacity_progress.setToolTip("Visual indicator of how full your disc will be after burning.")
        cap_layout.addWidget(self.main_window.capacity_progress)
        layout.addLayout(cap_layout)

    def create_burn_controls(self, layout):
        burn_ctrl_layout = QHBoxLayout()
        self.main_window.advanced_burn_button = QPushButton("Advanced...")
        self.main_window.advanced_burn_button.setToolTip("Open advanced burning options and settings.")
        burn_ctrl_layout.addStretch()
        burn_ctrl_layout.addWidget(self.main_window.advanced_burn_button)
        self.main_window.burn_button = QPushButton("Burn Disc")
        self.main_window.burn_button.setStyleSheet("background-color: #4CAF50;")
        self.main_window.burn_button.setToolTip("Start burning the current queue to the selected disc.")
        burn_ctrl_layout.addWidget(self.main_window.burn_button)
        layout.addLayout(burn_ctrl_layout)

    def create_chat_area(self, layout):
        chat_layout = QVBoxLayout()
        self.main_window.chat_history = QTextEdit()
        self.main_window.chat_history.setReadOnly(True)
        self.main_window.chat_history.setToolTip("Conversation history with the AI assistant.")
        chat_layout.addWidget(self.main_window.chat_history)
        from PyQt6.QtWidgets import QLabel, QHBoxLayout
        from PyQt6.QtGui import QMovie
        thinking_layout = QHBoxLayout()
        self.main_window.thinking_label = QLabel("Thinking...")
        self.main_window.thinking_label.setVisible(False)
        self.main_window.thinking_label.setToolTip("The AI is generating a response.")
        self.main_window.spinner_label = QLabel()
        self.main_window.spinner_label.setVisible(False)
        self.main_window.spinner_label.setToolTip("Loading animation while the AI is thinking.")
        try:
            self.main_window.spinner_movie = QMovie("spinner.gif")
            self.main_window.spinner_label.setMovie(self.main_window.spinner_movie)
        except Exception:
            self.main_window.spinner_label.setText("...")
        thinking_layout.addWidget(self.main_window.spinner_label)
        thinking_layout.addWidget(self.main_window.thinking_label)
        chat_layout.addLayout(thinking_layout)
        self.main_window.chat_input = QLineEdit(placeholderText="Chat with Gemini...")
        self.main_window.chat_input.setToolTip("Type your message to the AI assistant and press Enter or click Send.")
        chat_layout.addWidget(self.main_window.chat_input)
        layout.addLayout(chat_layout)

    def connect_signals(self):
        self.main_window.library_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.main_window.library_table.customContextMenuRequested.connect(self.main_window.show_library_context_menu)
        self.main_window.library_table.doubleClicked.connect(self.main_window.add_to_burn_queue_from_index)
        self.main_window.download_button.clicked.connect(self.main_window.start_download_handler)
        self.main_window.save_preset_button.clicked.connect(self.main_window.save_preset)
        self.main_window.delete_preset_button.clicked.connect(self.main_window.delete_preset)
        self.main_window.preset_selector.activated.connect(self.main_window.load_preset)
        self.main_window.advanced_burn_button.clicked.connect(self.main_window.open_advanced_burn_settings)
        self.main_window.burn_button.clicked.connect(self.main_window.start_burn_process)
        self.main_window.send_chat_button.clicked.connect(self.main_window.send_chat_message)
        self.main_window.chat_input.returnPressed.connect(self.main_window.send_chat_message)
        self.main_window.browse_music_button.clicked.connect(self.main_window.browse_music_directory)
        self.main_window.refresh_drive_button.clicked.connect(self.main_window._populate_drives)
        self.main_window.eject_drive_button.clicked.connect(self.main_window.eject_selected_drive)
        self.main_window.wipe_drive_button.clicked.connect(self.main_window.wipe_selected_drive)
        self.main_window.read_cd_button.clicked.connect(self.main_window.read_selected_cd)
        self.main_window.audio_play_button.clicked.connect(self.main_window.play_selected_audio)
        self.main_window.audio_pause_button.clicked.connect(self.main_window.pause_audio)
        self.main_window.audio_stop_button.clicked.connect(self.main_window.stop_audio)
