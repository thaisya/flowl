import flet as ft
from .subtitle_display import SubtitleDisplay
from .control_bar import ControlBar

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
            current_font_size=self.settings.font_size,
            current_opacity=self.settings.opacity,
            current_font_color=self.settings.font_color,
            current_bg_color=self.settings.bg_color,
            current_from_code=self.settings.from_code,
            current_to_code=self.settings.to_code,
            current_show_original=self.settings.show_original,
        )

        self._update_layout()

    def _minimize_window(self, e):
        self.page.window.minimized = True
        self.page.update()

    def _on_lock_toggle(self, is_locked):
        self.is_locked = is_locked
        self._update_layout()
        self.update()

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
            "WHITE": ft.Colors.GREY_300,
            "BLACK": ft.Colors.GREY_900,
            "RED": ft.Colors.RED_900,
            "GREEN": ft.Colors.GREEN_900,
            "BLUE": ft.Colors.BLUE_900,
            "YELLOW": ft.Colors.YELLOW_900,
            "CYAN": ft.Colors.CYAN_900,
            "MAGENTA": ft.Colors.PURPLE_900
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
            "WHITE": ft.Colors.GREY_300,
            "BLACK": ft.Colors.GREY_900,
            "RED": ft.Colors.RED_900,
            "GREEN": ft.Colors.GREEN_900,
            "BLUE": ft.Colors.BLUE_900,
            "YELLOW": ft.Colors.YELLOW_900,
            "CYAN": ft.Colors.CYAN_900,
            "MAGENTA": ft.Colors.PURPLE_900
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

    def _update_layout(self):
        """Reconstruct the control tree based on lock state."""
        self.subtitle_display = SubtitleDisplay(self.settings)
        self.subtitle_display.update_text(self.current_original, self.current_translated)
        self.subtitle_display.set_loading(self.is_loading)
        stack = ft.Stack(
            controls=[
                # Main Content Area (Subtitles) - Centered
                ft.Container(
                    content=self.subtitle_display,
                    alignment=ft.alignment.center,
                    expand=True,
                ),
                
                # Control Bar - Top (Full Width)
                ft.Container(
                    content=self.control_bar,
                    top=0,
                    left=0,
                    right=0,
                    padding=0,
                ),
                
                # Resize Handle - Bottom Right
                ft.GestureDetector(
                    content=ft.Container(
                        content=ft.Icon(ft.Icons.SOUTH_EAST, color=ft.Colors.WHITE54, size=20),
                        padding=5,
                        bgcolor=ft.Colors.TRANSPARENT,
                    ),
                    on_pan_update=self._on_resize_pan,
                    right=0,
                    bottom=0,
                    visible=not self.is_locked
                ),
            ],
            expand=True,
        )

        if self.is_locked:
            self.content = stack
        else:
            self.content = ft.WindowDragArea(
                content=stack,
                expand=True
            )

    def update_translation(self, original, translated, is_final=False):
        if is_final:
            if original.strip().lower() == "the":
                return
            if original.strip():
                self._final_originals.append(original.strip())
            if translated.strip():
                self._final_translated.append(translated.strip())
            
            self._accumulated_partial_original = ""
            self._last_partial_original_word_count = 0
            self._accumulated_partial_translated = ""
            self._last_partial_translated_word_count = 0
                
        merged_original = " ".join(self._final_originals)
        merged_translated = " ".join(self._final_translated)
        
        if not is_final:
            if original.strip():
                orig_words = original.strip().split()
                new_orig_count = len(orig_words)
                diff_orig = new_orig_count - self._last_partial_original_word_count
                
                if diff_orig > 0:
                    new_words = orig_words[-diff_orig:]
                    self._accumulated_partial_original = self._accumulated_partial_original + (" " if self._accumulated_partial_original else "") + " ".join(new_words)
                elif new_orig_count < self._last_partial_original_word_count:
                    self._accumulated_partial_original = original.strip()
                    
                self._last_partial_original_word_count = new_orig_count
                merged_original = merged_original + (" " if merged_original else "") + self._accumulated_partial_original
                
            if translated.strip():
                trans_words = translated.strip().split()
                new_trans_count = len(trans_words)
                diff_trans = new_trans_count - self._last_partial_translated_word_count
                
                if diff_trans > 0:
                    new_words = trans_words[-diff_trans:]
                    self._accumulated_partial_translated = self._accumulated_partial_translated + (" " if self._accumulated_partial_translated else "") + " ".join(new_words)
                elif new_trans_count < self._last_partial_translated_word_count:
                    self._accumulated_partial_translated = translated.strip()
                    
                self._last_partial_translated_word_count = new_trans_count
                merged_translated = merged_translated + (" " if merged_translated else "") + self._accumulated_partial_translated

        while len(merged_original) > self._max_history_chars and len(self._final_originals) > 0:
            self._final_originals.pop(0)
            merged_original = " ".join(self._final_originals)
            if not is_final and original.strip():
                merged_original = merged_original + (" " if merged_original else "") + self._accumulated_partial_original
                
        while len(merged_translated) > self._max_history_chars and len(self._final_translated) > 0:
            self._final_translated.pop(0)
            merged_translated = " ".join(self._final_translated)
            if not is_final and translated.strip():
                merged_translated = merged_translated + (" " if merged_translated else "") + self._accumulated_partial_translated
                
        self.current_original = merged_original
        self.current_translated = merged_translated
        self.subtitle_display.update_text(merged_original, merged_translated)

    def show_loading(self, is_loading: bool):
        """Show or hide the loading indicator."""
        self.is_loading = is_loading
        self.subtitle_display.set_loading(is_loading)
