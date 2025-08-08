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
        self._system_prompt_sent = False
        # Only send system instructions as the first user message if conversation is empty
        if self.system_instructions:
            self._conversation.append({"role": "user", "parts": [self.system_instructions]})
            self._system_prompt_sent = True

    def send_message(self, message):
        try:
            # Only send system instructions if conversation is empty and not already sent
            if not self._conversation and self.system_instructions and not self._system_prompt_sent:
                self._conversation.append({"role": "user", "parts": [self.system_instructions]})
                self._system_prompt_sent = True
            self._conversation.append({"role": "user", "parts": [message]})
            response = self.model.generate_content(self._conversation)
            # Try to extract the actual reply text
            text = getattr(response, 'text', None)
            if not text and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                # Gemini 1.5/2.0: candidate.content.parts[0].text
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                    part = candidate.content.parts[0]
                    if isinstance(part, dict) and 'text' in part:
                        text = part['text']
                    elif hasattr(part, 'text'):
                        text = part.text
            if not text:
                text = "(No response text found)"
            self._conversation.append({"role": "model", "parts": [text]})
            self.response_received.emit(text)
        except Exception as e:
            self.error_occurred.emit(str(e))
