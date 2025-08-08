from PyQt6.QtCore import QThread, pyqtSignal

class GeminiSender(QThread):
    """A worker to send a single message to a Gemini chat session."""
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, chat_session, prompt):
        super().__init__()
        self.chat = chat_session
        self.prompt = prompt

    def run(self):
        try:
            if self.chat is None:
                raise ValueError("Chat session is not initialized.")
            
            response = self.chat.send_message(self.prompt)
            
            # Logic to extract text from response, similar to old worker
            text = getattr(response, 'text', None)
            if not text and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                    part = candidate.content.parts[0]
                    if isinstance(part, dict) and 'text' in part:
                        text = part['text']
                    elif hasattr(part, 'text'):
                        text = part.text
            
            if not text:
                text = "(No valid response text found)"
                
            self.response_received.emit(text)
        except Exception as e:
            self.error_occurred.emit(str(e))
