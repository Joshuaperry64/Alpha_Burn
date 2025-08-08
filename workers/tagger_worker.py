import os
import musicbrainzngs as mb
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TCON, TRCK
from PyQt6.QtCore import QThread, pyqtSignal
import config # Use the new config module

mb.set_useragent("Alpha_Burn", "1.6", "https://github.com/josh-perry/alpha_burn")

class TaggerWorker(QThread):
    finished = pyqtSignal(str, dict)
    error = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(self, file_path, original_title):
        super().__init__()
        self.file_path = file_path
        self.title = original_title
        self.artwork_cache_path = config.get_setting('PATHS', 'artworkcache')
        if not os.path.exists(self.artwork_cache_path):
            os.makedirs(self.artwork_cache_path)

    def run(self):
        try:
            self.status_update.emit(f"Searching for '{self.title}'...")
            result = mb.search_recordings(query=self.title, limit=1)
            if not result.get('recording-list'):
                raise ValueError("No metadata found on MusicBrainz.")
            
            rec = result['recording-list'][0]
            release = rec.get('release-list', [{}])[0]
            
            meta = {
                'title': rec.get('title', 'Unknown Title'),
                'artist': rec.get('artist-credit-list', [{}])[0].get('artist', {}).get('name', 'Unknown Artist'),
                'album': release.get('title', 'Unknown Album'),
                'year': release.get('date', '0000').split('-')[0],
                'filepath': self.file_path
            }
            
            audio = MP3(self.file_path, ID3=ID3)
            audio.add_tags()
            audio.tags.clear()
            audio.tags.add(TIT2(encoding=3, text=meta['title']))
            audio.tags.add(TPE1(encoding=3, text=meta['artist']))
            audio.tags.add(TALB(encoding=3, text=meta['album']))
            audio.tags.add(TDRC(encoding=3, text=meta['year']))
            
            release_id = release.get('id')
            if release_id:
                # Artwork Caching Logic
                cached_art_path = os.path.join(self.artwork_cache_path, f"{release_id}.jpg")
                
                if os.path.exists(cached_art_path):
                    self.status_update.emit("Loading album art from cache...")
                    with open(cached_art_path, 'rb') as art_file:
                        art_data = art_file.read()
                else:
                    try:
                        self.status_update.emit("Downloading album art...")
                        art_data = mb.get_image_front(release_id)
                        # Save to cache
                        with open(cached_art_path, 'wb') as art_file:
                            art_file.write(art_data)
                    except mb.ResponseError:
                        art_data = None # No art found
                
                if art_data:
                    audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=art_data))
            
            audio.save()
            self.finished.emit(self.file_path, meta)
        except Exception as e:
            self.error.emit(f"Tagging failed for '{self.title}': {e}")
