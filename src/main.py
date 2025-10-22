"""Application entry point for Flowl real-time translator."""

import sys
from utils.settings import SettingsManager
from utils.logger import logger

def main():
    """Start the Flowl UI application."""
    from ui import create_ui_app
    try:
        # Create and run the UI application
        app, window = create_ui_app()
        app.exec()
    except KeyboardInterrupt:
        logger.info("Manual exit")

if __name__ == "__main__":
    main()
