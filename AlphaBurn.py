import sys
import os
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

# We now import the main window from its own module
from ui.main_window import AlphaBurnApp
import constants

if __name__ == '__main__':
    # --- START OF FIX ---
    # Determine the absolute path of the directory containing this script.
    # This ensures that files in the project folder (like ffmpeg.exe) can be found.
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundled executable (e.g., via PyInstaller)
        application_path = os.path.dirname(sys.executable)
    else:
        # If the application is run as a .py script
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    # Prepend the application's directory to the system's PATH environment variable.
    # This allows yt-dlp to find ffmpeg.exe when it's in the same folder.
    os.environ['PATH'] = application_path + os.pathsep + os.environ.get('PATH', '')
    # --- END OF FIX ---

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Optional: Create a splash.png for a more polished look
    splash_pix = QPixmap(300, 200)
    splash_pix.fill(Qt.GlobalColor.darkGray)
    splash = QSplashScreen(splash_pix)
    splash.showMessage(f"Loading {constants.APP_NAME}...", Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.white)
    splash.show()
    app.processEvents()
    
    main_app = AlphaBurnApp()
    splash.finish(main_app)
    main_app.show()
    sys.exit(app.exec())