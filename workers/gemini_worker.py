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
        self._conversation = []
        # Send system prompt as initial user message (Gemini API does not support 'system' role)
        if self.system_instructions:
            self._conversation.append({"role": "user", "parts": [self.system_instructions]})

    def send_message(self, message):
        try:
            self._conversation.append({"role": "user", "parts": [message]})
            response = self.model.generate_content(self._conversation)
            # Gemini API may return a response object with .text or .candidates[0].text
            text = getattr(response, 'text', None)
            if text is None and hasattr(response, 'candidates') and response.candidates:
                text = response.candidates[0].text
            else:
                text = str(response)
            self._conversation.append({"role": "model", "parts": [text]})
            self.response_received.emit(text)
        except Exception as e:
            self.error_occurred.emit(str(e))
