## 2024-05-23 - Initial Exploration
**Learning:** This is a PySide6 application for real-time translation using `vosk` (implied by `rec.Result()`) and presumably a translation model. It uses worker threads (`ASRWorker`, `MTWorker`) to handle audio processing and translation to avoid blocking the UI.
**Action:** Investigating `QTextEdit` usage in `src/ui/mainui.py` for potential performance improvements.
