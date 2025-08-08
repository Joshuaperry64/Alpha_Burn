import google.generativeai as genai
from PyQt6.QtCore import QObject, pyqtSignal

class GeminiWorker(QObject):
    """Worker to interact with the Gemini API."""
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_key, model_name, system_instructions=None):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name
        self.system_instructions = system_instructions or "You are the AI assistant inside this CD burner application. You can search for music, download playlists, and assist with burning discs. Respond as a helpful in-app assistant."
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def send_message(self, message):
        try:
            # Prepend system instructions to the user message
            full_prompt = f"[SYSTEM INSTRUCTIONS]\n{self.system_instructions}\n[USER]\n{message}"
            response = self.model.generate_content(full_prompt)
            self.response_received.emit(response.text)
        except Exception as e:
            self.error_occurred.emit(str(e))
