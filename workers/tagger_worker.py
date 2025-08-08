import musicbrainzngs as mb
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TCON, TRCK
from PyQt6.QtCore import QThread, pyqtSignal

mb.set_useragent("Alpha_Burn", "1.5", "https://github.com/josh-perry/alpha_burn")

class TaggerWorker(QThread):
    finished = pyqtSignal(str, dict)
    error = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(self, file_path, original_title):
        super().__init__()
        self.file_path = file_path
        self.title = original_title

    def run(self):
        try:
            self.status_update.emit(f"Searching for '{self.title}'...")
            result = mb.search_recordings(query=self.title, limit=1)
            if not result.get('recording-list'):
                raise ValueError("No metadata found on MusicBrainz.")
            
            rec = result['recording-list'][0]
            meta = {
                'title': rec.get('title', 'Unknown Title'),
                'artist': rec.get('artist-credit-list', [{}])[0].get('artist', {}).get('name', 'Unknown Artist'),
                'album': rec.get('release-list', [{}])[0].get('title', 'Unknown Album'),
                'year': rec.get('release-list', [{}])[0].get('date', '0000').split('-')[0],
                'filepath': self.file_path
            }
            
            audio = MP3(self.file_path, ID3=ID3)
            audio.add_tags()
            audio.tags.clear()
            audio.tags.add(TIT2(encoding=3, text=meta['title']))
            audio.tags.add(TPE1(encoding=3, text=meta['artist']))
            audio.tags.add(TALB(encoding=3, text=meta['album']))
            audio.tags.add(TDRC(encoding=3, text=meta['year']))
            
            release_id = rec.get('release-list', [{}])[0].get('id')
            if release_id:
                try:
                    self.status_update.emit("Downloading album art...")
                    art = mb.get_image_front(release_id)
                    audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=art))
                except mb.ResponseError:
                    pass # No art found
            
            audio.save()
            self.finished.emit(self.file_path, meta)
        except Exception as e:
            self.error.emit(f"Tagging failed for '{self.title}': {e}")
