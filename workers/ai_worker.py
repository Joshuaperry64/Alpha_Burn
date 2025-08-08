import os
from PyQt6.QtCore import QThread, pyqtSignal
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import config

class AIWorker(QThread):
    # This signal now emits a dictionary to handle different response types
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, prompt, library_model, api_key):
        super().__init__()
        self.prompt = prompt
        self.library_model = library_model
        self.api_key = api_key

    def run(self):
        try:
            # --- INTENT DETECTION ---
            # Determine if the user wants to download new music or curate the existing library.
            if self.prompt.lower().startswith(('download', 'find', 'get')):
                self.discover_and_download_playlist()
            else:
                self.curate_from_library()
        except Exception as e:
            self.error.emit(str(e))

    def discover_and_download_playlist(self):
        """Finds a playlist on Spotify based on the prompt and returns track names."""
        self.error.emit("This function has been deprecated, please use the download button instead")
        return
        
        # client_id = config.get_setting("API_KEYS", "spotify_client_id")
        # client_secret = config.get_setting("API_KEYS", "spotify_client_secret")

        # if not client_id or not client_secret:
        #     raise ValueError("Spotify credentials are required for music discovery.")

        # # Extract search query from prompt, e.g., "download a pop playlist" -> "pop playlist"
        # search_query = self.prompt.lower().replace('download', '').replace('find', '').replace('get', '').strip()
        # if "a" == search_query.split()[0]:
        #     search_query = " ".join(search_query.split()[1:])


        # auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        # sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # # Search Spotify for a playlist matching the query
        # results = sp.search(q=search_query, type='playlist', limit=1)
        # if not results['playlists']['items']:
        #     raise ValueError(f"Could not find a Spotify playlist for '{search_query}'.")

        # playlist_id = results['playlists']['items'][0]['id']
        # playlist_name = results['playlists']['items'][0]['name']

        # # Get tracks from the found playlist
        # track_results = sp.playlist_tracks(playlist_id)
        # tracks_to_download = []
        # for item in track_results['items']:
        #     track = item['track']
        #     if track:
        #         artist_name = track['artists'][0]['name']
        #         track_name = track['name']
        #         tracks_to_download.append(f"{artist_name} - {track_name}")

        # if not tracks_to_download:
        #     raise ValueError("Found a playlist, but it appears to be empty.")

        # # Emit a dictionary indicating the type of result and the data
        # self.finished.emit({
        #     "type": "download_list",
        #     "data": tracks_to_download,
        #     "playlist_name": playlist_name
        # })

    def curate_from_library(self):
        """Selects songs from the existing local library based on the prompt."""
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        if self.library_model.rowCount() == 0:
            raise ValueError("Your music library is empty. Cannot curate.")

        available_songs = []
        for row in range(self.library_model.rowCount()):
            artist = self.library_model.item(row, 1).text()
            title = self.library_model.item(row, 0).text()
            genre = self.library_model.item(row, 4).text()
            filepath = self.library_model.item(row, 6).text()
            available_songs.append(f"{title} by {artist} (Genre: {genre}) ||| {filepath}")

        prompt_for_api = f"""
        From the following list of available songs, select the filepaths that best match the user's request: "{self.prompt}".
        Each song is listed in the format: 'Title by Artist (Genre) ||| Filepath'.
        Available Songs:
        {'; '.join(available_songs)}
        Your response MUST be ONLY a comma-separated list of the full filepaths for the matching songs. Do not include any other text, explanation, or formatting.
        For example: C:/path/song1.mp3,D:/music/track2.mp3
        If no songs match, return an empty string.
        """

        response = model.generate_content(prompt_for_api)
        
        try:
            cleaned_text = response.text.strip()
            if not cleaned_text:
                matching_filepaths = []
            else:
                matching_filepaths = [path.strip() for path in cleaned_text.split(',')]
        except ValueError:
             raise ValueError("Gemini AI returned an empty or invalid response. This can happen with safety blocks.")

        if not matching_filepaths:
             raise ValueError("Gemini AI could not find any songs matching that description in your library.")

        # Emit a dictionary indicating the type of result and the data
        self.finished.emit({
            "type": "curation_list",
            "data": matching_filepaths
        })