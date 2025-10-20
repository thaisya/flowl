"""Basic PySide6 UI with sliding text window for Flowl translation."""

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit, QPushButton
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QTextCursor

from app import FlowlApp
from .settings_tab import SettingsTab

class SlidingTextWindow(QMainWindow):
    # Define signals for thread-safe communication
    translation_received = Signal(str, dict)  # event_type, data
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flowl Translation")
        self.setGeometry(200, 200, 600, 400)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title label
        title = QLabel("Real-time Translation")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Open settings window button
        settings_button = QPushButton("Open Settings")
        settings_button.clicked.connect(self.open_settings)
        layout.addWidget(settings_button)

        # Text display area
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Arial", 12))
        self.text_display.setPlaceholderText("Translation results will appear here...")
        layout.addWidget(self.text_display)
        
        # Connect signal to slot for thread-safe updates
        self.translation_received.connect(self.update_text)
        
        # Initialize FlowlApp with our callback
        self.app = FlowlApp(ui_callback=self.on_translation_event)
        
        # Start the app
        self.app.start()
        
    def on_translation_event(self, event_type: str, data: dict):
        """Handle translation events from FlowlApp (called from worker thread)."""
        # Emit signal to update UI in main thread
        self.translation_received.emit(event_type, data)
        
    def update_text(self, event_type: str, data: dict):
        """Update the text display (runs in main thread)."""
        original = data.get('original', '')
        translated = data.get('translated', '')
        
        if event_type == "final" or event_type == "partial":
            # Just replace the entire text - true sliding effect
            self.text_display.setText(f"{original} → {translated}")
            
        # Auto-scroll to bottom
        self.text_display.moveCursor(QTextCursor.End)

    def open_settings(self):
        """Open the settings window."""
        def on_saved():
            self.restart_app()
        dlg = SettingsTab(on_saved)
        dlg.exec()

    def restart_app(self):
        try:
            self.app.restart()
            self.text_display.append("🔁 App restarted with new settings")
        except Exception as e:
            self.text_display.append(f"❌ Error restarting app: {e}")

def create_ui_app():
    """Create and return the UI application."""
    app = QApplication([])
    window = SlidingTextWindow()
    window.show()
    return app, window
