import flet as ft
from utils.logger import logger

class LoggerUI(ft.Container):
    """
    On-screen UI component for displaying application logs.
    Hooks into FlowlLogger to receive updates in real-time.
    Draggable and Resizable within its parent stack.
    """
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        
        self.log_list = ft.ListView(
            expand=True,
            spacing=2,
            auto_scroll=True
        )

        # Title bar for dragging the window
        self.title_bar = ft.GestureDetector(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.WHITE54, size=14),
                        ft.Text("Logs", color=ft.Colors.WHITE54, size=12, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                padding=ft.padding.only(left=10, top=5, bottom=5, right=10),
            ),
            on_pan_update=self._on_pan_update,
            mouse_cursor=ft.MouseCursor.MOVE
        )

        # Resize handle at the bottom right
        self.resize_handle = ft.GestureDetector(
            content=ft.Container(
                content=ft.Icon(ft.Icons.SOUTH_EAST, color=ft.Colors.WHITE54, size=14),
                alignment=ft.alignment.bottom_right,
                padding=5,
            ),
            on_pan_update=self._on_resize_update,
            mouse_cursor=ft.MouseCursor.RESIZE_DOWN_RIGHT
        )

        self.box = ft.Container(
            content=ft.Column(
                [
                    self.title_bar,
                    ft.Container(content=self.log_list, expand=True, padding=ft.padding.only(left=8, right=8)),
                    self.resize_handle
                ],
                spacing=0,
            ),
            width=750,
            height=300,
            bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.BLACK),
            border_radius=10,
            border=ft.border.all(1, ft.Colors.WHITE24),
            clip_behavior=ft.ClipBehavior.HARD_EDGE
        )
        
        self.content = self.box
        self.visible = False
        
        # Hook into utils.logger
        logger.set_ui_callback(self.add_log)

    def _on_pan_update(self, e: ft.DragUpdateEvent):
        if self.page:
            TOP_MARGIN = 50
            LEFT_MARGIN = 20
            RIGHT_MARGIN = 20
            BOTTOM_MARGIN = 20
            max_right = self.page.window.width - self.box.width - LEFT_MARGIN
            max_bottom = self.page.window.height - self.box.height - TOP_MARGIN
            
            if self.right is not None:
                new_right = self.right - e.delta_x
                # Clamp between RIGHT_MARGIN (right edge) and max_right (left edge)
                self.right = max(RIGHT_MARGIN, min(new_right, max(RIGHT_MARGIN, max_right)))
                
            if self.bottom is not None:
                new_bottom = self.bottom - e.delta_y
                # Clamp between BOTTOM_MARGIN (bottom edge) and max_bottom (top edge)
                self.bottom = max(BOTTOM_MARGIN, min(new_bottom, max(BOTTOM_MARGIN, max_bottom)))
                
            self.update()

    def _on_resize_update(self, e: ft.DragUpdateEvent):
        if not self.page:
            return
            
        old_width = self.box.width
        old_height = self.box.height
        
        # Calculate raw requested sizes
        raw_width = old_width + e.delta_x
        raw_height = old_height + e.delta_y
        
        # Max width/height to keep the resize handle away from the edges
        RIGHT_MARGIN = 20
        BOTTOM_MARGIN = 20
        max_width = old_width + (self.right if self.right is not None else RIGHT_MARGIN) - RIGHT_MARGIN
        max_height = old_height + (self.bottom if self.bottom is not None else BOTTOM_MARGIN) - BOTTOM_MARGIN
        
        # Clamp to min and max boundaries
        new_width = max(200, min(raw_width, max_width))
        new_height = max(100, min(raw_height, max_height))
        
        # Adjust anchors exactly by the difference in size to keep top-left perfectly fixed!
        if self.right is not None:
            self.right = self.right + (old_width - new_width)
        if self.bottom is not None:
            self.bottom = self.bottom + (old_height - new_height)
            
        self.box.width = new_width
        self.box.height = new_height

        self.update()

    def add_log(self, level: str, message: str):
        color = ft.Colors.WHITE
        if level == "ERROR" or level == "CRITICAL":
            color = ft.Colors.RED_400
        elif level == "WARNING":
            color = ft.Colors.YELLOW_400
        elif level == "DEBUG":
            color = ft.Colors.GREY_500
        
        self.log_list.controls.append(
            ft.Text(message, size=11, color=color, selectable=True, font_family="Consolas")
        )
        
        if len(self.log_list.controls) > 100:
            self.log_list.controls.pop(0)

        if self.page:
            try:
                self.update()
            except Exception:
                pass

    def toggle(self):
        """Show or hide the logger UI."""
        self.visible = not self.visible
        if self.page:
            self.update()
