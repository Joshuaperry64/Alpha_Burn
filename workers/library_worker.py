import os
from PyQt6.QtCore import QThread, pyqtSignal
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import database

class LibraryWorker(QThread):
    """A worker to handle library scanning in the background."""
    finished = pyqtSignal(int)
    status_update = pyqtSignal(str)

    def __init__(self, download_path):
        super().__init__()
        self.download_path = download_path

    def run(self):
        try:
            self.status_update.emit(f"Scanning library folder: {self.download_path}")
            print(f"[LibraryWorker] Scanning directory: {self.download_path}")
            if not os.path.exists(self.download_path):
                self.status_update.emit(f"Directory does not exist: {self.download_path}")
                return
            files = os.listdir(self.download_path)
            print(f"[LibraryWorker] Files found: {files}")
            all_db_songs = {song[-1] for song in database.get_all_songs()}
            found_new = 0
            for filename in files:
                if filename.lower().endswith(".mp3"):
                    filepath = os.path.join(self.download_path, filename)
                    if filepath not in all_db_songs:
                        try:
                            audio = MP3(filepath, ID3=ID3)
                            metadata = {
                                'title': str(audio.get('TIT2', [''])[0]),
                                'artist': str(audio.get('TPE1', [''])[0]),
                                'album': str(audio.get('TALB', [''])[0]),
                                'year': str(audio.get('TDRC', [''])[0]),
                                'genre': str(audio.get('TCON', [''])[0])
                            }
                            database.add_song(filepath, metadata)
                            found_new += 1
                        except Exception as e:
                            self.status_update.emit(f"Error processing {filepath}: {e}")
                            print(f"Error processing {filepath}: {e}")
                            continue
            self.finished.emit(found_new)
        except Exception as e:
            self.status_update.emit(f"Library scan failed: {e}")
            print(f"Library scan failed: {e}")
