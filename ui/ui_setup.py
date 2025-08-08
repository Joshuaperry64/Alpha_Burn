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
        top_bar.addWidget(self.main_window.url_input)
        self.main_window.download_button = QPushButton("Download")
        top_bar.addWidget(self.main_window.download_button)
        self.main_window.send_chat_button = QPushButton("Send")
        top_bar.addWidget(self.main_window.send_chat_button)
        self.main_window.main_layout.addLayout(top_bar)

    def create_central_splitter(self):
        self.main_window.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_window.main_layout.addWidget(self.main_window.splitter, 1)

    def create_left_pane(self):
        left_pane = QFrame()
        left_layout = QVBoxLayout(left_pane)
        self.main_window.library_table = QTableView()
        left_layout.addWidget(self.main_window.library_table)
        self.main_window.splitter.addWidget(left_pane)

    def create_right_pane(self):
        right_pane = QFrame()
        right_layout = QVBoxLayout(right_pane)
        
        self.create_drive_selection(right_layout)
        self.create_preset_buttons(right_layout)
        
        self.main_window.burn_queue_list = QListWidget()
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
        cap_layout.addWidget(self.main_window.capacity_label)
        self.main_window.capacity_progress = QProgressBar()
        cap_layout.addWidget(self.main_window.capacity_progress)
        layout.addLayout(cap_layout)

    def create_burn_controls(self, layout):
        burn_ctrl_layout = QHBoxLayout()
        self.main_window.advanced_burn_button = QPushButton("Advanced...")
        burn_ctrl_layout.addStretch()
        burn_ctrl_layout.addWidget(self.main_window.advanced_burn_button)
        self.main_window.burn_button = QPushButton("Burn Disc")
        self.main_window.burn_button.setStyleSheet("background-color: #4CAF50;")
        burn_ctrl_layout.addWidget(self.main_window.burn_button)
        layout.addLayout(burn_ctrl_layout)

    def create_chat_area(self, layout):
        chat_layout = QVBoxLayout()
        self.main_window.chat_history = QTextEdit()
        self.main_window.chat_history.setReadOnly(True)
        chat_layout.addWidget(self.main_window.chat_history)
        self.main_window.chat_input = QLineEdit(placeholderText="Chat with Gemini...")
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
