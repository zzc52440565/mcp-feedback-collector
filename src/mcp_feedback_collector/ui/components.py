"""
UI组件模块
提供可重用的UI组件
"""

import tkinter as tk
from tkinter import scrolledtext
from typing import Optional, Callable, Any
import math

from .theme import ModernTheme


class RoundedFrame(tk.Frame):
    """圆角框架组件"""
    
    def __init__(self, parent, radius: int = 8, shadow: bool = False, 
                 bg: str = None, **kwargs):
        """
        初始化圆角框架
        
        Args:
            parent: 父组件
            radius: 圆角半径
            shadow: 是否显示阴影
            bg: 背景颜色
            **kwargs: 其他参数
        """
        super().__init__(parent, **kwargs)
        
        self.radius = radius
        self.shadow = shadow
        self.bg_color = bg or ModernTheme.CARD_BACKGROUND
        
        # 创建Canvas用于绘制圆角
        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            relief='flat',
            borderwidth=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 创建内容框架
        self.content_frame = tk.Frame(
            self.canvas,
            bg=self.bg_color,
            relief='flat',
            borderwidth=0
        )
        
        # 绑定事件
        self.bind('<Configure>', self._on_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # 初始化绘制
        self.after(1, self._draw_rounded_background)
    
    def _on_configure(self, event):
        """窗口大小改变事件"""
        if event.widget == self:
            self.after_idle(self._draw_rounded_background)
    
    def _on_canvas_configure(self, event):
        """Canvas大小改变事件"""
        # 更新内容框架位置
        canvas_width = event.width
        canvas_height = event.height
        
        # 计算内容区域（考虑圆角和阴影）
        padding = max(self.radius // 2, 4)
        if self.shadow:
            padding += 2
        
        content_width = max(1, canvas_width - 2 * padding)
        content_height = max(1, canvas_height - 2 * padding)
        
        # 更新内容框架大小和位置
        self.canvas.coords(
            self.content_window,
            padding, padding
        )
        self.canvas.itemconfig(
            self.content_window,
            width=content_width,
            height=content_height
        )
        
        self._draw_rounded_background()
    
    def _draw_rounded_background(self):
        """绘制圆角背景"""
        self.canvas.delete("background")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # 设置Canvas背景
        parent_bg = (self.master.cget('bg') if hasattr(self.master, 'cget') 
                    else ModernTheme.BACKGROUND_PRIMARY)
        self.canvas.configure(bg=parent_bg)
        
        # 绘制阴影（如果启用）
        if self.shadow:
            shadow_offset = 2
            shadow_color = "#0f0f0f"
            self._draw_rounded_rect_on_canvas(
                shadow_offset, shadow_offset,
                width - 2 + shadow_offset, height - 2 + shadow_offset,
                self.radius, shadow_color, "shadow"
            )
        
        # 绘制主背景
        self._draw_rounded_rect_on_canvas(
            2, 2, width - 2, height - 2,
            self.radius, self.bg_color, "background"
        )
        
        # 确保内容框架存在
        if not hasattr(self, 'content_window'):
            self.content_window = self.canvas.create_window(
                0, 0, anchor='nw', window=self.content_frame
            )
    
    def _draw_rounded_rect_on_canvas(self, x1, y1, x2, y2, radius, color, tag):
        """在Canvas上绘制圆角矩形"""
        if x2 - x1 < 2 * radius:
            radius = (x2 - x1) // 2
        if y2 - y1 < 2 * radius:
            radius = (y2 - y1) // 2
        
        if radius <= 0:
            # 如果半径太小，绘制普通矩形
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="", tags=tag)
            return
        
        # 绘制圆角矩形的各个部分
        # 中央矩形
        self.canvas.create_rectangle(
            x1 + radius, y1, x2 - radius, y2,
            fill=color, outline="", tags=tag
        )
        self.canvas.create_rectangle(
            x1, y1 + radius, x2, y2 - radius,
            fill=color, outline="", tags=tag
        )
        
        # 四个圆角
        self.canvas.create_oval(
            x1, y1, x1 + 2 * radius, y1 + 2 * radius,
            fill=color, outline="", tags=tag
        )
        self.canvas.create_oval(
            x2 - 2 * radius, y1, x2, y1 + 2 * radius,
            fill=color, outline="", tags=tag
        )
        self.canvas.create_oval(
            x1, y2 - 2 * radius, x1 + 2 * radius, y2,
            fill=color, outline="", tags=tag
        )
        self.canvas.create_oval(
            x2 - 2 * radius, y2 - 2 * radius, x2, y2,
            fill=color, outline="", tags=tag
        )


class ModernScrolledText(scrolledtext.ScrolledText):
    """现代化滚动文本组件"""
    
    def __init__(self, parent, placeholder: str = "", **kwargs):
        """
        初始化现代化滚动文本组件
        
        Args:
            parent: 父组件
            placeholder: 占位符文本
            **kwargs: 其他参数
        """
        # 应用主题样式
        style = ModernTheme.get_text_widget_style()
        style.update(kwargs)
        
        super().__init__(parent, **style)
        
        self.placeholder = placeholder
        self.placeholder_active = False
        
        # 设置占位符
        if placeholder:
            self._set_placeholder()
        
        # 绑定事件
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<KeyPress>', self._on_key_press)
    
    def _set_placeholder(self):
        """设置占位符"""
        if not self.get(1.0, tk.END).strip():
            self.placeholder_active = True
            self.insert(1.0, self.placeholder)
            self.configure(fg=ModernTheme.TEXT_MUTED)
    
    def _clear_placeholder(self):
        """清除占位符"""
        if self.placeholder_active:
            self.placeholder_active = False
            self.delete(1.0, tk.END)
            self.configure(fg=ModernTheme.TEXT_PRIMARY)
    
    def _on_focus_in(self, event):
        """获得焦点事件"""
        self._clear_placeholder()
    
    def _on_focus_out(self, event):
        """失去焦点事件"""
        if not self.get(1.0, tk.END).strip():
            self._set_placeholder()
    
    def _on_key_press(self, event):
        """按键事件"""
        if self.placeholder_active:
            self._clear_placeholder()
    
    def get_text(self) -> str:
        """获取文本内容（不包括占位符）"""
        if self.placeholder_active:
            return ""
        return self.get(1.0, tk.END).strip()
    
    def set_text(self, text: str):
        """设置文本内容"""
        self.placeholder_active = False
        self.delete(1.0, tk.END)
        self.insert(1.0, text)
        self.configure(fg=ModernTheme.TEXT_PRIMARY)
        
        if not text and self.placeholder:
            self._set_placeholder()


class ModernButton(tk.Button):
    """现代化按钮组件"""
    
    def __init__(self, parent, button_type: str = "primary", 
                 hover_effect: bool = True, **kwargs):
        """
        初始化现代化按钮
        
        Args:
            parent: 父组件
            button_type: 按钮类型 (primary, secondary, success, danger)
            hover_effect: 是否启用悬停效果
            **kwargs: 其他参数
        """
        # 应用主题样式
        style = ModernTheme.get_button_style(button_type)
        style.update(kwargs)
        
        super().__init__(parent, **style)
        
        self.button_type = button_type
        self.hover_effect = hover_effect
        self.original_bg = style.get('bg')
        self.hover_bg = style.get('activebackground')
        
        if hover_effect:
            self.bind('<Enter>', self._on_enter)
            self.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        """鼠标进入事件"""
        if self.hover_effect and self.hover_bg:
            self.configure(bg=self.hover_bg)
    
    def _on_leave(self, event):
        """鼠标离开事件"""
        if self.hover_effect and self.original_bg:
            self.configure(bg=self.original_bg)


class ImagePreview(tk.Frame):
    """图片预览组件"""
    
    def __init__(self, parent, image_data: bytes, source: str, 
                 on_remove: Optional[Callable] = None, **kwargs):
        """
        初始化图片预览组件
        
        Args:
            parent: 父组件
            image_data: 图片数据
            source: 图片来源
            on_remove: 删除回调函数
            **kwargs: 其他参数
        """
        super().__init__(parent, **kwargs)
        
        self.image_data = image_data
        self.source = source
        self.on_remove = on_remove
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建组件"""
        # 图片显示区域
        self.image_label = tk.Label(
            self,
            bg=ModernTheme.CARD_BACKGROUND,
            relief='solid',
            borderwidth=1
        )
        self.image_label.pack(side=tk.TOP, padx=2, pady=2)
        
        # 删除按钮
        if self.on_remove:
            remove_btn = ModernButton(
                self,
                text="×",
                button_type="danger",
                font=(ModernTheme.FONT_FAMILY_PRIMARY, 10, "bold"),
                width=2,
                height=1,
                command=self.on_remove
            )
            remove_btn.pack(side=tk.TOP, pady=(2, 0))
        
        # 来源标签
        source_label = tk.Label(
            self,
            text=self.source[:15] + "..." if len(self.source) > 15 else self.source,
            **ModernTheme.get_label_style("muted"),
            font=(ModernTheme.FONT_FAMILY_PRIMARY, 8)
        )
        source_label.pack(side=tk.TOP, pady=(2, 0))
