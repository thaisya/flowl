import flet as ft
from utils.logger import logger

class SubtitleDisplay(ft.Container):
    """
    A specific component for rendering the translation text.
    Designed to be easily styled later.
    """
    def __init__(self, settings_manager):
        super().__init__()
        self.settings = settings_manager
        
        self.text_before_translation = ft.Text(
            size=int(self.settings.font_size * 0.8),
            opacity=0.6,
            color=self.settings.font_color,
            weight=ft.FontWeight.NORMAL,
            text_align=ft.TextAlign.LEFT,
            visible=self.settings.show_original,
        )
        self.text_after_translation = ft.Text(
            size=self.settings.font_size,
            opacity=1.0,
            color=self.settings.font_color,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.LEFT,
            style=ft.TextThemeStyle.HEADLINE_MEDIUM, 
        )
        
        self.loading_ring = ft.ProgressRing(
            width=40,
            height=40,
            stroke_width=4,
            color=self.settings.font_color,
            visible=False,
        )
        
        self.loading_text = ft.Text(
            value="Loading",
            size=self.settings.font_size,
            color=self.settings.font_color,
            weight=ft.FontWeight.BOLD,
            visible=False,
        )

        self.padding = ft.padding.only(top=65, bottom=20, left=20, right=20)
        self.bgcolor = ft.Colors.with_opacity(self.settings.opacity, self.settings.bg_color)
        self.expand = False
        self.alignment = None
        self.border_radius = 10
        self.content = ft.Column(
            controls=[
                self.text_before_translation,
                self.text_after_translation,
                self.loading_ring,
                self.loading_text,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=5,
            tight=True,
        )

    def update_text(self, original: str, translated: str, original_tail: str = "", translated_tail: str = ""):
        """Update the text content."""
        if original_tail and original.endswith(original_tail):
            stable_part = original[:-len(original_tail)]
            self.text_before_translation.value = ""
            self.text_before_translation.spans = [
                ft.TextSpan(stable_part),
                ft.TextSpan(
                    original_tail, 
                    style=ft.TextStyle(color=ft.Colors.with_opacity(0.4, self.settings.font_color))
                )
            ]
        else:
            self.text_before_translation.spans = None
            self.text_before_translation.value = original

        if translated_tail and translated.endswith(translated_tail):
            trans_stable_part = translated[:-len(translated_tail)]
            self.text_after_translation.value = ""
            self.text_after_translation.spans = [
                ft.TextSpan(trans_stable_part),
                ft.TextSpan(
                    translated_tail,
                    style=ft.TextStyle(color=ft.Colors.with_opacity(0.4, self.settings.font_color))
                )
            ]
        else:
            self.text_after_translation.spans = None
            self.text_after_translation.value = translated

        if self.page:
            self.update()
        else:
            logger.error("SubtitleDisplay: Skipped update (detached from page)")

    def set_loading(self, is_loading: bool):
        """Toggle the loading state UI."""
        self.loading_ring.visible = is_loading
        self.loading_text.visible = is_loading
        
        if is_loading:
            self.text_before_translation.visible = False
            self.text_after_translation.visible = False
            self.content.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        else:
            self.text_before_translation.visible = self.settings.show_original
            self.text_after_translation.visible = True
            self.content.horizontal_alignment = ft.CrossAxisAlignment.START
            
        if self.page:
            self.update()

    def set_font_size(self, size: int):
        """Update the font size."""
        self.text_after_translation.size = size
        self.text_before_translation.size = int(size * 0.8)
        if self.page:
            self.update()

    def set_opacity(self, opacity: float):
        """Update the background opacity."""
        self.bgcolor = ft.Colors.with_opacity(opacity, self.settings.bg_color)
        if self.page:
            self.update()

    def set_font_color(self, color: str):
        """Update the font color."""
        self.text_before_translation.color = color
        self.text_after_translation.color = color
        self.loading_ring.color = color
        self.loading_text.color = color
        if self.page:
            self.update()

    def set_bg_color(self, color: str):
        """Update the background color (maintaining opacity)."""
        self.bgcolor = ft.Colors.with_opacity(self.settings.opacity, color)
        if self.page:
            self.update()

    def set_show_original(self, show_original: bool):
        """Toggle visibility of the original text."""
        self.text_before_translation.visible = show_original
        if self.page:
            self.update()
