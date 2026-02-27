"""Flet-based UI with sliding text window for Flowl translation."""

import flet as ft
import queue
import threading
import time
import subprocess
import sys
import keyboard

from app import FlowlApp
from .settings_tab import SettingsTab
from utils.settings import SettingsManager
from utils.logger import logger

from .components.overlay_window import OverlayWindow


class SlidingTextWindow:
    """Main UI window utilizing the Blueprint Overlay components."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Flowl Overlay"
        
        self.page.window.width = 1000
        self.page.window.height = 350
        self.page.window.bgcolor = ft.Colors.TRANSPARENT
        self.page.bgcolor = ft.Colors.TRANSPARENT
        self.page.window.frameless = True
        self.page.window.title_bar_hidden = True
        self.page.window.title_bar_buttons_hidden = True
        self.page.window.always_on_top = True
        self.page.window.center()
        
        self._update_queue = queue.Queue()

        self.settings = SettingsManager.load_from_file()
        
        self.overlay = OverlayWindow(
            page, 
            self.settings, 
            on_settings_req=self.open_settings,
            on_close_req=self.close_app_req,
            on_restart_req=self.restart_app
        )
        
        self.page.add(self.overlay)
        
        self.app = FlowlApp(ui_callback=self.on_translation_event, settings=self.settings)
        
        self._start_update_processor()
        
        keyboard.add_hotkey('ctrl+alt+l', self.toggle_global_lock)
        
        self.app.start()

    def _start_update_processor(self):
        """Start processing queued updates on background thread."""
        def update_loop():
            while True:
                try:
                    updates_batch = []
                    # We running this loop to get all the updates that are in the queue
                    while True:
                        try:
                            item = self._update_queue.get_nowait()
                            updates_batch.append(item)
                        except queue.Empty:
                            break
                    
                    if updates_batch:
                        latest_trans = None
                        
                        # Process batch
                        for event_type, data in updates_batch:
                            # We only care about the LATEST translation event ?? TODO: Check this
                            if event_type in ["final", "partial"]:
                                latest_trans = (event_type, data)
                            elif event_type == "lambda":
                                # Execute generic lambdas immediately
                                try:
                                    data() 
                                except Exception as e:
                                    print(f"Error executing lambda update: {e}")

                        # Apply latest translation update once
                        if latest_trans:
                            try:
                                self._handle_trans_update(*latest_trans)
                            except Exception as e:
                                print(f"Error updating translation UI: {e}")
                                
                except Exception as e:
                    print(f"CRITICAL Update Loop Error: {e}")
                    import traceback
                    traceback.print_exc()

                time.sleep(0.033) # Cap at ~30 FPS
        
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()

    def toggle_global_lock(self):
        """Toggle the global lock state using a hotkey."""
        new_state = not self.overlay.is_locked
        self.overlay.is_locked = new_state
        self.overlay.control_bar.set_lock_indicator(new_state)
        self.page.window.ignore_mouse_events = new_state
        self.page.update()
    
    def on_translation_event(self, event_type: str, data: dict):
        """Handle translation events from FlowlApp."""
        # We push data tuples instead of lambdas now to allow inspection/batching
        self._update_queue.put((event_type, data))

    def _handle_trans_update(self, event_type: str, data: dict):
        if event_type in ["final", "partial"]:
            original = data.get('original', '')
            translated = data.get('translated', '')
            is_final = (event_type == "final")
            try:
                self.overlay.update_translation(original, translated, is_final=is_final)
            except Exception as e:
                print(f"Overlay update failed: {e}")

    def open_settings(self, e):
        """Open the settings in a completely separate native OS window."""
        
        def run_settings_process():
            # Show loading/spinning indicator on main GUI if desired, but we'll leave it as is.
            try:
                # Launch the settings tab as a distinct Python process
                process = subprocess.Popen(
                    [sys.executable, "src/ui/settings_tab.py"],
                    cwd="." # Assuming we are always running from project root
                )
                
                # Wait for the user to close the settings window
                exit_code = process.wait()
                
                # Exit code 0 means "Save" was clicked and config.json updated
                if exit_code == 0:
                    self.restart_app()
            except Exception as e:
                print(f"Error launching settings process: {e}")
                
        # Launch the waiting process in a background thread so we don't block the UI
        threading.Thread(target=run_settings_process, daemon=True).start()
    
    def restart_app(self):
        if hasattr(self, 'app') and self.app:
            self.overlay.show_loading(True)
            self.page.update()
            
            def _do_restart():
                self.app.restart()
                self.overlay.show_loading(False)
                
                if self.page:
                    self.page.update()
                    
            threading.Thread(target=_do_restart, daemon=True).start()
        else:
            print("WARNING: restart_app called but app is not initialized.")

    def close_app_req(self, e):
        """User requested close via UI button."""
        self.close_app()
        self.page.window.close()

    def close_app(self):
        """Handle cleanup."""
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        if self.app:
            self.app.stop()


def main(page: ft.Page):
    """Main entry point for Flet app."""
    window = SlidingTextWindow(page)

def create_ui_app():
    return main
