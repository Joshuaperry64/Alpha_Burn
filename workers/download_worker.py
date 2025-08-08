import os
import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal

class DownloadWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(dict)

    def __init__(self, url, download_path):
        super().__init__()
        self.url = url
        self.download_path = download_path

    def run(self):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'progress_hooks': [self.progress.emit]
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # The info dictionary will contain the final filepath after postprocessing.
                # The original code's manual manipulation of this was buggy and has been removed.
                info = ydl.extract_info(self.url, download=True)
                self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))