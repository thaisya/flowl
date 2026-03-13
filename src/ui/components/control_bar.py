import flet as ft

class ControlBar(ft.Container):
    """
    Floating toolbar for window controls.
    """
    def __init__(self, page: ft.Page, settings, on_settings_click, on_close, on_minimize, on_lock_toggle, on_font_size_change, on_opacity_change, on_font_color_change, on_bg_color_change, on_language_change, on_show_original_change, current_font_size=24, current_opacity=0.3, current_font_color="WHITE", current_bg_color="BLACK", current_from_code="en", current_to_code="ru", current_show_original=True):
        super().__init__()
        self.page = page
        self.settings = settings
        self._on_settings_click = on_settings_click
        self._on_close = on_close
        self._on_minimize = on_minimize
        self._on_lock_toggle = on_lock_toggle
        self._on_font_size_change = on_font_size_change
        self._on_opacity_change = on_opacity_change
        self._on_language_change = on_language_change
        self._on_font_color_change = on_font_color_change
        self._on_bg_color_change = on_bg_color_change
        self._on_show_original_change = on_show_original_change
        self.is_locked = False

        self.current_from_code = current_from_code
        self.current_to_code = current_to_code

        self.lock_btn = ft.IconButton(
            icon=ft.Icons.LOCK_OPEN,
            icon_color=ft.Colors.WHITE54,
            tooltip="Unlocked (Press Ctrl+Alt+L to lock)",
        )
        
        self.flags = {
            "en": "🇺🇸",
            "ru": "🇷🇺"
        }

        self.from_btn = ft.PopupMenuButton(
            content=ft.Text(self.flags.get(current_from_code, current_from_code), size=20, color=ft.Colors.WHITE),
            tooltip="Source Language",
            items=self._create_lang_menu_items(is_from=True)
        )

        self.to_btn = ft.PopupMenuButton(
            content=ft.Text(self.flags.get(current_to_code, current_to_code), size=20, color=ft.Colors.WHITE),
            tooltip="Target Language",
            items=self._create_lang_menu_items(is_from=False)
        )

        self.swap_btn = ft.IconButton(
            icon=ft.Icons.SWAP_HORIZ,
            icon_color=ft.Colors.WHITE,
            icon_size=20,
            tooltip="Swap Languages",
            on_click=lambda e: self._on_language_change(self.current_to_code, self.current_from_code)
        )

        lang_selector = ft.Row(
            controls=[
                self.from_btn,
                self.swap_btn,
                self.to_btn
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.CENTER
        )

        self.settings_btn = ft.PopupMenuButton(
            icon=ft.Icons.SETTINGS,
            icon_color=ft.Colors.WHITE,
            tooltip="Settings",
            items=[
                # Show Original Text Checkbox
                ft.PopupMenuItem(
                    content=ft.Checkbox(
                        label=ft.Text("Show Original Text", size=12, color=ft.Colors.BLACK),
                        value=current_show_original,
                        on_change=lambda e: self._on_show_original_change(e.control.value)
                    ),
                    disabled=True
                ),
                ft.PopupMenuItem(content=ft.Divider(), height=10, disabled=True),
                
                # Font Size Selection (Slider)
                ft.PopupMenuItem(
                    content=ft.Column(
                        controls=[
                            ft.Text("Font Size", size=12, color=ft.Colors.BLACK),
                            ft.Slider(
                                min=12, 
                                max=64, 
                                divisions=13, 
                                value=current_font_size, 
                                label="{value} px", 
                                on_change=lambda e: self._on_font_size_change(int(e.control.value))
                            )
                        ],
                        spacing=0
                    ),
                    disabled=True
                ),
                # Opacity Selection (Slider)
                ft.PopupMenuItem(
                    content=ft.Column(
                        controls=[
                            ft.Text("Opacity", size=12, color=ft.Colors.BLACK),
                            ft.Slider(
                                min=0, 
                                max=100, 
                                divisions=100, 
                                value=current_opacity*100, 
                                label="{value}%", 
                                on_change=lambda e: self._on_opacity_change(float(e.control.value)/100)
                            )
                        ],
                        spacing=0
                    ),
                    disabled=True
                ),
                ft.PopupMenuItem(content=ft.Divider(), height=10, disabled=True),
                
                # Font Color Selection
                ft.PopupMenuItem(
                    content=ft.Column(
                        controls=[
                            ft.Text("Font Color", size=12, color=ft.Colors.BLACK),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=20, height=20, border_radius=10, bgcolor=color,
                                        border=ft.border.all(2, ft.Colors.GREY_400) if current_font_color == color else None,
                                        on_click=lambda e, c=color: self._on_font_color_change(c)
                                    ) for color in ["WHITE", "BLACK", "RED", "GREEN", "BLUE", "YELLOW", "CYAN", "MAGENTA"]
                                ],
                                wrap=True,
                                spacing=5,
                                run_spacing=5
                            )
                        ],
                        spacing=5
                    ),
                    disabled=True
                ),

                # Background Color Selection
                ft.PopupMenuItem(
                    content=ft.Column(
                        controls=[
                            ft.Text("Background Color", size=12, color=ft.Colors.BLACK),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=20, height=20, border_radius=10, bgcolor=color,
                                        border=ft.border.all(2, ft.Colors.GREY_400) if current_bg_color == color else None,
                                        on_click=lambda e, c=color: self._on_bg_color_change(c)
                                    ) for color in ["WHITE", "BLACK", "RED", "GREEN", "BLUE", "YELLOW", "CYAN", "MAGENTA"]
                                ],
                                wrap=True,
                                spacing=5,
                                run_spacing=5
                            )
                        ],
                        spacing=5
                    ),
                    disabled=True
                ),
                ft.PopupMenuItem(content=ft.Divider(), height=10, disabled=True), # Divider
                ft.PopupMenuItem(
                    text="Advanced Settings", 
                    on_click=lambda e: self._on_settings_click(e)
                ),
            ]
        )

        minimize_btn = ft.IconButton(
            icon=ft.Icons.REMOVE,
            icon_color=ft.Colors.WHITE,
            tooltip="Minimize",
            on_click=self._on_minimize
        )

        close_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=ft.Colors.RED_400,
            tooltip="Close App",
            on_click=self._on_close
        )

        # Configure Container properties
        self.padding = 5
        
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
        darker = darker_map.get(current_bg_color, ft.Colors.GREY_900)
        self.bgcolor = ft.Colors.with_opacity(min(1.0, settings.opacity + 0.3), darker)

        self.content = ft.Row(
            controls=[
                # Left: Lock Button
                ft.Container(
                    content=self.lock_btn,
                    alignment=ft.alignment.center_left,
                    expand=1
                ),
                # Center: Language Selector (Explicitly centered)
                ft.Container(
                    content=lang_selector,
                    alignment=ft.alignment.center,
                    expand=1
                ),
                # Right: Settings & Window Controls
                ft.Container(
                    content=ft.Row(
                        controls=[
                            self.settings_btn,
                            minimize_btn,
                            close_btn,
                        ],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.END
                    ),
                    alignment=ft.alignment.center_right,
                    expand=1
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=0,
        )

    def set_lock_indicator(self, is_locked):
        self.is_locked = is_locked
        if self.is_locked:
            self.lock_btn.icon = ft.Icons.LOCK
            self.lock_btn.tooltip = "Locked (Press Ctrl+Alt+L to unlock)"
            self.lock_btn.icon_color = ft.Colors.RED_400
            self.settings_btn.disabled = True
            
            self.from_btn.disabled = True
            if isinstance(self.from_btn.content, ft.Text):
                self.from_btn.content.color = ft.Colors.GREY
            
            self.to_btn.disabled = True
            if isinstance(self.to_btn.content, ft.Text):
                self.to_btn.content.color = ft.Colors.GREY
                
            self.swap_btn.disabled = True
            self.swap_btn.icon_color = ft.Colors.GREY
        else:
            self.lock_btn.icon = ft.Icons.LOCK_OPEN
            self.lock_btn.tooltip = "Unlocked (Press Ctrl+Alt+L to lock)"
            self.lock_btn.icon_color = ft.Colors.WHITE54
            self.settings_btn.disabled = False
            
            self.from_btn.disabled = False
            if isinstance(self.from_btn.content, ft.Text):
                self.from_btn.content.color = ft.Colors.WHITE
                
            self.to_btn.disabled = False
            if isinstance(self.to_btn.content, ft.Text):
                self.to_btn.content.color = ft.Colors.WHITE
                
            self.swap_btn.disabled = False
            self.swap_btn.icon_color = ft.Colors.WHITE
        
        if self.page:
            self.update()
        
        if self._on_lock_toggle:
            self._on_lock_toggle(self.is_locked)
            
    def _handle_lang_select(self, is_from, selected_code):
        new_from = selected_code if is_from else self.current_from_code
        new_to = self.current_to_code if is_from else selected_code

        if new_from == new_to:
            if is_from:
                new_to = self.current_from_code
            else:
                new_from = self.current_to_code
                
        self._on_language_change(new_from, new_to)

    def _create_lang_menu_items(self, is_from):
        items = []
        for code in self.settings.aviable_langs:
            if code == self.current_from_code and is_from:
                continue
            if code == self.current_to_code and not is_from:
                continue
            items.append(
                ft.PopupMenuItem(
                    text=f"{self.flags.get(code, code)} {code.upper()}",
                    on_click=lambda e, c=code: self._handle_lang_select(is_from, c)
                )
            )
        return items

    def set_languages(self, from_code: str, to_code: str):
        """Update language flags dynamically."""
        self.current_from_code = from_code
        self.current_to_code = to_code

        if isinstance(self.from_btn.content, ft.Text):
            self.from_btn.content.value = self.flags.get(from_code, from_code)
        
        if isinstance(self.to_btn.content, ft.Text):
            self.to_btn.content.value = self.flags.get(to_code, to_code)
            
        self.from_btn.items = self._create_lang_menu_items(is_from=True)
        self.to_btn.items = self._create_lang_menu_items(is_from=False)
        
        if self.page:
            self.update()


