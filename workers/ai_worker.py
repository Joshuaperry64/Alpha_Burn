import time
import os
from PyQt6.QtCore import QThread, pyqtSignal
import google.generativeai as genai

class AIWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, prompt, library_model, api_key):
        super().__init__()
        self.prompt = prompt
        self.library_model = library_model
        self.api_key = api_key

    def run(self):
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-pro')

            available_songs = []
            for row in range(self.library_model.rowCount()):
                artist = self.library_model.item(row, 1).text()
                title = self.library_model.item(row, 0).text()
                genre = self.library_model.item(row, 4).text()
                filepath = self.library_model.item(row, 5).text()
                # Use a separator that is unlikely to be in a filename
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
            
            # Clean up the response text
            cleaned_text = response.text.strip()
            if not cleaned_text:
                matching_filepaths = []
            else:
                matching_filepaths = [path.strip() for path in cleaned_text.split(',')]

            if not matching_filepaths:
                 raise ValueError("Gemini AI could not find any songs matching that description in your library.")

            self.finished.emit(matching_filepaths)

        except Exception as e:
            self.error.emit(f"Gemini AI Error: {e}")
