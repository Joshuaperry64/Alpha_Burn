import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

# We now import the main window from its own module
from ui.main_window import AlphaBurnApp
import constants

if __name__ == '__main__':
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

