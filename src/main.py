"""Application entry point for Flowl real-time translator."""

import flet as ft
from utils.logger import logger

def main(page: ft.Page):
    """Start the Flowl UI application."""
    from ui.mainui import main as ui_main
    try:
        ui_main(page)
    except KeyboardInterrupt:
        logger.info("Manual exit")

if __name__ == "__main__":
    ft.app(target=main)
