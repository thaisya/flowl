"""Centralized logging system for Flowl application."""

import sys
from datetime import datetime
from typing import Optional, Callable


class FlowlLogger:
    """Centralized logger that can route logs to UI or console."""
    
    def __init__(self):
        self._log_callback: Optional[Callable[[str, str], None]] = None
    
    def set_ui_callback(self, callback: Callable[[str, str], None], ui_instance=None):
        """Set the callback for UI logging and optionally store UI instance."""
        self._log_callback = callback
    
    def log(self, message: str, level: str = "INFO", module: str = ""):
        """Log a message with optional module prefix."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format message with module prefix if provided
        if module:
            formatted_message = f"[{module}] {message}"
        else:
            formatted_message = message
        
        # Try UI callback first
        if self._log_callback:
            try:
                # Send fully formatted message to UI (with timestamp)
                full_message = f"[{timestamp}] {level}: {formatted_message}"
                self._log_callback(level, full_message)
                return
            except Exception as e:
                # Fallback to console if UI callback fails
                print(f"[{timestamp}] {level}: UI logging failed: {e}", file=sys.stderr)
        
        # Fallback to console logging
        print(f"[{timestamp}] {level}: {formatted_message}")
    
    def info(self, message: str, module: str = ""):
        """Log an info message."""
        self.log(message, "INFO", module)
    
    def warning(self, message: str, module: str = ""):
        """Log a warning message."""
        self.log(message, "WARNING", module)
    
    def error(self, message: str, module: str = ""):
        """Log an error message."""
        self.log(message, "ERROR", module)
    
    def debug(self, message: str, module: str = ""):
        """Log a debug message."""
        self.log(message, "DEBUG", module)

# Global logger instance
logger = FlowlLogger()
