"""Basic PySide6 UI with sliding text window for Flowl translation."""

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit, QPushButton, QTabWidget
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QTextCursor

from app import FlowlApp
from .settings_tab import SettingsTab
from utils.settings import SettingsManager
from utils.logger import logger
from _version import __version__

class SlidingTextWindow(QMainWindow):
    # Define signals for thread-safe communication
    translation_received = Signal(str, dict)  # event_type, data
    log_received = Signal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Flowl Translation v{__version__}")
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

        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Translation tab
        translation_widget = QWidget()
        translation_layout = QVBoxLayout(translation_widget)
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Arial", 12))
        self.text_display.setPlaceholderText("Translation results will appear here...")
        translation_layout.addWidget(self.text_display)
        
        tab_widget.addTab(translation_widget, "Translations")

        # Log tab
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Courier New", 10))  # Monospace font for logs
        self.log_display.setPlaceholderText("Log information will appear here...")
        self.log_display.setAcceptRichText(True)  # Enable HTML formatting
        log_layout.addWidget(self.log_display)
        
        # Clear logs button
        clear_logs_button = QPushButton("Clear Logs")
        clear_logs_button.clicked.connect(self.clear_logs)
        log_layout.addWidget(clear_logs_button)
        
        tab_widget.addTab(log_widget, "Logs")

        # Connect signals to slot for thread-safe updates
        self.translation_received.connect(self.update_text)
        self.log_received.connect(self.update_log)
        
        # Set up the global logger to use our UI callback
        logger.set_ui_callback(self.on_log_event, self)
        
        # Load settings and initialize FlowlApp with our callbacks
        settings = SettingsManager.load_from_file()
        self.app = FlowlApp(ui_callback=self.on_translation_event, settings=settings)
        
        # Start the app
        self.app.start()
        
    def on_translation_event(self, event_type: str, data: dict):
        """Handle translation events from FlowlApp (called from worker thread)."""
        # Emit signal to update UI in main thread
        self.translation_received.emit(event_type, data)
    
    def on_log_event(self, level: str, message: str):
        """Handle log events from FlowlApp (called from worker thread)."""
        log_data = {
            'message': message,
            'level': level
        }
        # Emit signal to update UI in main thread
        self.log_received.emit("log", log_data)
         
    def update_text(self, event_type: str, data: dict):
        """Update the text display (runs in main thread)."""
        original = data.get('original', '')
        translated = data.get('translated', '')
        
        if event_type == "final" or event_type == "partial":
            self.text_display.setText(f"{original} → {translated}")
        self.text_display.moveCursor(QTextCursor.End)

    def update_log(self, event_type: str, data: dict):
        """Update the log display (runs in main thread)."""
        log_message = data.get('message', '')
        log_level = data.get('level', 'INFO')
        
        # Set color based on log level
        if log_level == "ERROR":
            color = "#DC143C"  # Crimson Red
        elif log_level == "WARNING":
            color = "#FF8C00"  # Dark Orange
        elif log_level == "INFO":
            color = "#0066CC"  # Blue
        elif log_level == "DEBUG":
            color = "#696969"  # Dim Gray
        else:
            color = "#000000"  # Black (default)
        
        # Format message with color
        colored_message = f'<span style="color: {color};">{log_message}</span>'
        
        # Append to log display with HTML formatting
        self.log_display.append(colored_message)
    
    def clear_logs(self):
        """Clear the log display."""
        self.log_display.clear()

    def open_settings(self):
        """Open the settings window."""
        def on_saved():
            self.restart_app()
        dlg = SettingsTab(on_saved)
        dlg.exec()

    def restart_app(self):
        try:
            self.app.restart()
            logger.info("App restarted with new settings", "UI")
        except Exception as e:
            logger.error(f"Error restarting app: {e}", "UI")

    def closeEvent(self, event):
        """Handle window close event with proper cleanup."""
        self.app.stop()
        event.accept()

def create_ui_app():
    """Create and return the UI application."""
    app = QApplication([])
    window = SlidingTextWindow()
    window.show()
    return app, window
