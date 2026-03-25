"""Flet-based UI with sliding text window for Flowl translation."""

import flet as ft
import queue
import threading
import time
import subprocess
import sys
import keyboard
import traceback

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
        
        self._prev_window_width = 1000
        self._prev_window_height = 350
        self.page.on_resized = self._on_page_resize
        
        self._update_queue = queue.Queue()
        self._shutdown = threading.Event()

        self.settings = SettingsManager.load_from_file()
        
        self.overlay = OverlayWindow(
            page, 
            self.settings, 
            on_settings_req=self.open_settings,
            on_close_req=self.close_app_req,
            on_restart_req=self.restart_app
        )
        
        self.page.add(self.overlay)
        
        self.app = None
        self.overlay.show_loading(True)
        self.page.update()
        
        def _init_and_start_app():
            self.app = FlowlApp(ui_callback=self.on_translation_event, settings=self.settings)
            
            self._start_update_processor()
            
            keyboard.add_hotkey(self.settings.lock_hotkey, self.toggle_global_lock)
            
            self.app.start()
            self.overlay.show_loading(False)
            if self.page:
                self.page.update()
                
        threading.Thread(target=_init_and_start_app, daemon=True).start()

    def _on_page_resize(self, e):
        """Ensure the logger stays within the screen bounds when the main window resizes."""
        new_width = self.page.window.width
        new_height = self.page.window.height
        
        logger_ui = self.overlay.logger_overlay
        
        if new_width and new_height:
            TOP_MARGIN = 50
            LEFT_MARGIN = 20
            RIGHT_MARGIN = 20
            BOTTOM_MARGIN = 20
            # First clamp the anchors to ensure it doesn't stay off-screen
            if logger_ui.right is not None:
                max_right = max(RIGHT_MARGIN, new_width - logger_ui.box.width - LEFT_MARGIN)
                logger_ui.right = max(RIGHT_MARGIN, min(logger_ui.right, max_right))
                
            if logger_ui.bottom is not None:
                max_bottom = max(BOTTOM_MARGIN, new_height - logger_ui.box.height - TOP_MARGIN)
                logger_ui.bottom = max(BOTTOM_MARGIN, min(logger_ui.bottom, max_bottom))

            # Then clamp the size if the window shrunk below the logger's size
            max_allowed_width = new_width - LEFT_MARGIN - (logger_ui.right if logger_ui.right is not None else RIGHT_MARGIN)
            max_allowed_height = new_height - TOP_MARGIN - (logger_ui.bottom if logger_ui.bottom is not None else BOTTOM_MARGIN)
            
            if logger_ui.box.width > max_allowed_width:
                logger_ui.box.width = max(200, max_allowed_width)
            if logger_ui.box.height > max_allowed_height:
                logger_ui.box.height = max(100, max_allowed_height)
                
            try:
                logger_ui.update()
            except Exception:
                pass
                
        self._prev_window_width = new_width
        self._prev_window_height = new_height

    def _start_update_processor(self):
        """Start processing queued updates on background thread."""
        def update_loop():
            while not self._shutdown.is_set():
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
                            # We only care about the LATEST translation event
                            if event_type == "final":
                                self._handle_trans_update(event_type, data)
                            elif event_type == "partial":
                                latest_trans = (event_type, data)
                            elif event_type == "lambda":
                                # Execute generic lambdas immediately
                                try:
                                    data() 
                                except Exception as e:
                                    logger.error(f"Error executing lambda update: {e}")

                        # Apply latest translation update once
                        if latest_trans:
                            try:
                                self._handle_trans_update(*latest_trans)
                            except Exception as e:
                                logger.error(f"Error updating translation UI: {e}")
                                
                except Exception as e:
                    logger.critical(f"CRITICAL Update Loop Error: {e}")
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
                logger.error(f"Overlay update failed: {e}")

    def open_settings(self, e):
        """Open the settings inside an overlay within the main window."""
        
        def on_saved():
            self.overlay.hide_settings()
            self.restart_app()
            
        def on_close():
            self.overlay.hide_settings()
            
        active_idx = None
        if self.app and self.app.audio_engine:
            active_idx = self.app.audio_engine._input_device_index
            
        settings_app = SettingsTab(self.page, on_saved=on_saved, on_close=on_close, active_device_index=active_idx)
        
        # Build the container for the settings overlay
        settings_content = ft.Container(
            theme=ft.Theme(color_scheme_seed=ft.Colors.BLUE, visual_density=ft.VisualDensity.COMPACT),
            theme_mode=ft.ThemeMode.LIGHT,
            content=ft.Column(
                [
                    ft.Row(
                        [ft.Text("Flowl Settings", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=settings_app.content,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.TextButton("Reset", on_click=settings_app.reset_to_defaults, style=ft.ButtonStyle(color=ft.Colors.BLACK)),
                                ft.TextButton("Cancel", on_click=settings_app._close_actions, style=ft.ButtonStyle(color=ft.Colors.BLACK)),
                                ft.ElevatedButton("Save", on_click=settings_app.save_settings),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                        padding=ft.padding.only(right=40),
                    )
                ],
                expand=True
            )
        )

        self.overlay.show_settings(settings_content)
    
    def restart_app(self):
        if self.app:
            self.overlay.show_loading(True)
            self.page.update()

            def _do_restart():
                self.settings = SettingsManager.load_from_file()
                self.app.restart()
                
                # Re-register hotkey with potentially new keybind
                keyboard.unhook_all_hotkeys()
                keyboard.add_hotkey(self.settings.lock_hotkey, self.toggle_global_lock)
                
                self.overlay.show_loading(False)
                
                if self.page:
                    self.page.update()
                    
            threading.Thread(target=_do_restart, daemon=True).start()
        else:
            logger.warning("restart_app called but app is not initialized.")

    def close_app_req(self, e):
        """User requested close via UI button."""
        self.close_app()
        self.page.window.close()

    def close_app(self):
        """Handle cleanup."""
        self._shutdown.set()
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
