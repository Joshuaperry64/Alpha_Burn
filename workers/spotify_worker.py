import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from PyQt6.QtCore import QThread, pyqtSignal

class SpotifyWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, playlist_url, client_id, client_secret):
        super().__init__()
        self.playlist_url = playlist_url
        self.client_id = client_id
        self.client_secret = client_secret

    def run(self):
        try:
            if not self.client_id or not self.client_secret:
                raise ValueError("Spotify credentials are not set in the settings.")

            self.progress.emit("Authenticating with Spotify...")
            auth_manager = SpotifyClientCredentials(client_id=self.client_id, client_secret=self.client_secret)
            sp = spotipy.Spotify(auth_manager=auth_manager)

            self.progress.emit("Fetching playlist tracks from Spotify...")
            results = sp.playlist_tracks(self.playlist_url)
            
            tracks = []
            for item in results['items']:
                track = item['track']
                if track:
                    # Create a search query for yt-dlp
                    artist_name = track['artists'][0]['name']
                    track_name = track['name']
                    search_query = f"{artist_name} - {track_name}"
                    tracks.append(search_query)
            
            if not tracks:
                raise ValueError("Could not find any tracks in the provided Spotify playlist.")

            self.finished.emit(tracks)

        except Exception as e:
            self.error.emit(f"Spotify Error: {e}")
