import flet as ft
from .subtitle_display import SubtitleDisplay
from .control_bar import ControlBar
from ui.logger import LoggerUI

class OverlayWindow(ft.Container):
    """
    Main component that orchestrates the blueprint UI.
    Inherits from Container to allow swapping content (DragArea vs Stack).
    """
    def __init__(self, page: ft.Page, settings_manager, on_settings_req, on_close_req, on_restart_req):
        super().__init__()
        self.page = page
        self.settings = settings_manager
        self.expand = True
        self.is_locked = False
        self.is_loading = False
        self.border_radius = 10
        
        self.current_original = ""
        self.current_translated = ""
        
        self._final_originals = []
        self._final_translated = []
        self._max_history_chars = 150
        
        self._accumulated_partial_original = ""
        self._last_partial_original_word_count = 0
        self._accumulated_partial_translated = ""
        self._last_partial_translated_word_count = 0
        
        self.on_restart_req = on_restart_req

        self.resize_icon = ft.Icon(ft.Icons.SOUTH_EAST, color=ft.Colors.WHITE54, size=20)
        
        self.settings_overlay = ft.Container(
            content=None,
            visible=False,
            expand=True,
            padding=10,
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
        )

        self.logger_overlay = LoggerUI(page)
        self.logger_overlay.bottom = 40
        self.logger_overlay.right = 20

        self.control_bar = ControlBar(
            page, 
            settings=self.settings,
            on_settings_click=on_settings_req,
            on_close=on_close_req,
            on_minimize=self._minimize_window,
            on_lock_toggle=self._on_lock_toggle,
            on_font_size_change=self._on_font_size_change,
            on_opacity_change=self._on_opacity_change,
            on_font_color_change=self._on_font_color_change,
            on_bg_color_change=self._on_bg_color_change,
            on_language_change=self._on_language_change,
            on_show_original_change=self._on_show_original_change,
            on_logger_toggle=self._on_logger_toggle,
            on_text_alignment_change=self._on_text_alignment_change,
            current_font_size=self.settings.font_size,
            current_opacity=self.settings.opacity,
            current_font_color=self.settings.font_color,
            current_bg_color=self.settings.bg_color,
            current_from_code=self.settings.from_code,
            current_to_code=self.settings.to_code,
            current_show_original=self.settings.show_original,
            current_text_alignment=self.settings.text_alignment,
        )

        self.subtitle_display = SubtitleDisplay(self.settings)
        self.subtitle_display.alignment = self._get_flet_alignment(self.settings.text_alignment)

        self.resize_handle = ft.GestureDetector(
            content=ft.Container(
                content=self.resize_icon,
                padding=5,
                bgcolor=ft.Colors.TRANSPARENT,
            ),
            on_pan_update=self._on_resize_pan,
            right=0,
            bottom=0,
            visible=not self.is_locked
        )

        self.subtitle_container = ft.Container(
            content=self.subtitle_display,
            top=0, bottom=0, left=0, right=0,
        )

        self.stack = ft.Stack(
            controls=[
                # Main Content Area (Subtitles) - Centered
                self.subtitle_container,
                
                # Control Bar - Top (Full Width)
                ft.Container(
                    content=self.control_bar,
                    top=0,
                    left=0,
                    right=0,
                    padding=0,
                ),
                
                # Logger Overlay
                self.logger_overlay,

                # Settings Overlay
                self.settings_overlay,

                # Resize Handle
                self.resize_handle,
            ],
            expand=True,
        )

        # Keep WindowDragArea permanent. When locked, global ignore_mouse_events makes it inactive.
        self.content = ft.WindowDragArea(
            content=self.stack,
            expand=True
        )

    def _minimize_window(self, e):
        self.page.window.minimized = True
        self.page.update()

    def _on_lock_toggle(self, is_locked):
        self.is_locked = is_locked
        self.resize_handle.visible = not self.is_locked
        self.resize_handle.update()

    def _on_logger_toggle(self, e):
        self.logger_overlay.toggle()

    def _on_font_size_change(self, size):
        self.settings.font_size = size
        self.settings.save_to_file()
        self.subtitle_display.set_font_size(size)
        self.update()

    def _on_opacity_change(self, opacity):
        self.settings.opacity = opacity
        self.settings.save_to_file()
        self.subtitle_display.set_opacity(opacity)

        darker_map = {
            color: shade for color, shade in zip(ControlBar.AVAILABLE_COLORS, [
                ft.Colors.GREY_300, ft.Colors.GREY_900,
                ft.Colors.RED_900, ft.Colors.GREEN_900,
                ft.Colors.BLUE_900, ft.Colors.YELLOW_900,
                ft.Colors.CYAN_900, ft.Colors.PURPLE_900
            ])
        }
        darker = darker_map.get(self.settings.bg_color, ft.Colors.GREY_900)
        self.control_bar.bgcolor = ft.Colors.with_opacity(min(1.0, self.settings.opacity + 0.3), darker)
        if self.page:
            self.update()

    def _on_font_color_change(self, color):
        self.settings.font_color = color
        self.settings.save_to_file()
        self.subtitle_display.set_font_color(color)
        self.update()

    def _on_bg_color_change(self, color):
        self.settings.bg_color = color
        self.settings.save_to_file()
        self.subtitle_display.set_bg_color(color)
        
        darker_map = {
            color: shade for color, shade in zip(ControlBar.AVAILABLE_COLORS, [
                ft.Colors.GREY_300, ft.Colors.GREY_900,
                ft.Colors.RED_900, ft.Colors.GREEN_900,
                ft.Colors.BLUE_900, ft.Colors.YELLOW_900,
                ft.Colors.CYAN_900, ft.Colors.PURPLE_900
            ])
        }
        darker = darker_map.get(color, ft.Colors.GREY_900)
        self.control_bar.bgcolor = ft.Colors.with_opacity(min(1.0, self.settings.opacity + 0.3), darker)
        if self.page:
            self.update()

    def _on_language_change(self, from_code, to_code):
        self.settings.from_code = from_code
        self.settings.to_code = to_code
        self.settings.save_to_file()
        
        self.control_bar.set_languages(from_code, to_code)

        if self.on_restart_req:
            self.on_restart_req()

    def _on_show_original_change(self, show_original):
        self.settings.show_original = show_original
        self.settings.save_to_file()
        self.subtitle_display.set_show_original(show_original)

    def _get_flet_alignment(self, align_str: str):
        align_map = {
            "TOP_LEFT": ft.alignment.top_left,
            "TOP_CENTER": ft.alignment.top_center,
            "TOP_RIGHT": ft.alignment.top_right,
            "CENTER_LEFT": ft.alignment.center_left,
            "CENTER": ft.alignment.center,
            "CENTER_RIGHT": ft.alignment.center_right,
            "BOTTOM_LEFT": ft.alignment.bottom_left,
            "BOTTOM_CENTER": ft.alignment.bottom_center,
            "BOTTOM_RIGHT": ft.alignment.bottom_right,
        }
        return align_map.get(align_str, ft.alignment.center)

    def _on_text_alignment_change(self, alignment: str):
        self.settings.text_alignment = alignment
        self.settings.save_to_file()
        self.subtitle_display.alignment = self._get_flet_alignment(alignment)
        if self.page:
            self.subtitle_display.update()

    def _on_resize_pan(self, e: ft.DragUpdateEvent):
        """Handle window resizing."""
        if self.is_locked: return

        MIN_WIDTH = 400
        MIN_HEIGHT = 150
        
        new_width = max(MIN_WIDTH, self.page.window.width + e.delta_x)
        new_height = max(MIN_HEIGHT, self.page.window.height + e.delta_y)
        
        self.page.window.width = new_width
        self.page.window.height = new_height
        self.page.update()

    def _accumulate_partial(self, text: str, accumulated: str, last_count: int) -> tuple[str, int]:
        """Helper to accumulate trailing words for partial text updates."""
        words = text.split()
        new_count = len(words)
        diff = new_count - last_count
        
        if diff > 0:
            new_words = words[-diff:]
            accumulated = accumulated + (" " if accumulated else "") + " ".join(new_words)
        elif new_count < last_count:
            accumulated = text
            
        return accumulated, new_count

    def update_translation(self, original: str, translated: str, is_final: bool = False):
        """
        Updates the subtitle display with new text.
        Handles merging partial sentences and rolling history when length exceeds Max History.
        """
        # Strip once at the top
        original = original.strip()
        translated = translated.strip()

        if is_final:
            # Filter out standalone "the" (common ASR hallucination/noise)
            if original.lower() == "the":
                return
            if original:
                self._final_originals.append(original)
            if translated:
                self._final_translated.append(translated)
            
            self._accumulated_partial_original = ""
            self._last_partial_original_word_count = 0
            self._accumulated_partial_translated = ""
            self._last_partial_translated_word_count = 0
                
        merged_original = " ".join(self._final_originals)
        merged_translated = " ".join(self._final_translated)
        
        if not is_final:
            if original:
                self._accumulated_partial_original, self._last_partial_original_word_count = self._accumulate_partial(
                    original, self._accumulated_partial_original, self._last_partial_original_word_count
                )
                merged_original = merged_original + (" " if merged_original else "") + self._accumulated_partial_original
                
            if translated:
                self._accumulated_partial_translated, self._last_partial_translated_word_count = self._accumulate_partial(
                    translated, self._accumulated_partial_translated, self._last_partial_translated_word_count
                )
                merged_translated = merged_translated + (" " if merged_translated else "") + self._accumulated_partial_translated

        # Trim history if it gets too long
        while len(merged_original) > self._max_history_chars and len(self._final_originals) > 0:
            self._final_originals.pop(0)
            merged_original = " ".join(self._final_originals)
            if not is_final and original:
                merged_original = merged_original + (" " if merged_original else "") + self._accumulated_partial_original
                
        while len(merged_translated) > self._max_history_chars and len(self._final_translated) > 0:
            self._final_translated.pop(0)
            merged_translated = " ".join(self._final_translated)
            if not is_final and translated:
                merged_translated = merged_translated + (" " if merged_translated else "") + self._accumulated_partial_translated
                
        self.current_original = merged_original
        self.current_translated = merged_translated
        self.subtitle_display.update_text(merged_original, merged_translated)

    def show_loading(self, is_loading: bool):
        """Show or hide the loading indicator."""
        self.is_loading = is_loading
        self.subtitle_display.set_loading(is_loading)

    def show_settings(self, content):
        """Show the settings overlay with provided content."""
        self.settings_overlay.content = content
        self.settings_overlay.visible = True
        self.resize_icon.color = ft.Colors.BLACK
        self.page.update()

    def hide_settings(self):
        """Hide the settings overlay."""
        self.settings_overlay.visible = False
        self.settings_overlay.content = None
        self.resize_icon.color = ft.Colors.WHITE54
        self.page.update()
