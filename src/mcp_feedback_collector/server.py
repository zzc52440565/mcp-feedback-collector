"""
交互式反馈收集器 MCP 服务器
AI调用时会汇报工作内容，用户可以提供文本反馈和/或图片反馈
"""

import io
import base64
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import threading
import queue
from pathlib import Path
from datetime import datetime
import os
import math
import re

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Image as MCPImage

# 创建MCP服务器
mcp = FastMCP(
    "交互式反馈收集器",
    dependencies=["pillow", "tkinter"]
)

# 配置超时时间（秒）
DEFAULT_DIALOG_TIMEOUT = 300  # 5分钟
DIALOG_TIMEOUT = int(os.getenv("MCP_DIALOG_TIMEOUT", DEFAULT_DIALOG_TIMEOUT))

# 简单的Markdown渲染器
class SimpleMarkdownRenderer:
    """简单的Markdown渲染器，用于在tkinter Text组件中显示格式化文本"""

    def __init__(self, text_widget, theme):
        self.text_widget = text_widget
        self.theme = theme
        self.setup_tags()

    def setup_tags(self):
        """设置文本标签样式 - 现代化Markdown渲染优化版本"""
        # 一级标题 - 主要标题，更大更醒目
        self.text_widget.tag_configure("h1",
            font=(self.theme.FONT_FAMILY_PRIMARY, self.theme.FONT_SIZE_2XL, "bold"),
            foreground=self.theme.PRIMARY_LIGHT,
            spacing1=self.theme.SPACING_LG,  # 增加上间距
            spacing3=self.theme.SPACING_MD,  # 增加下间距
            justify=tk.LEFT)

        # 二级标题 - 章节标题，醒目的颜色
        self.text_widget.tag_configure("h2",
            font=(self.theme.FONT_FAMILY_PRIMARY, self.theme.FONT_SIZE_XL, "bold"),
            foreground=self.theme.SECONDARY_LIGHT,
            spacing1=self.theme.SPACING_MD,  # 增加上间距
            spacing3=self.theme.SPACING_SM,  # 增加下间距
            justify=tk.LEFT)

        # 三级标题 - 子章节标题
        self.text_widget.tag_configure("h3",
            font=(self.theme.FONT_FAMILY_PRIMARY, self.theme.FONT_SIZE_LG, "bold"),
            foreground=self.theme.SUCCESS_LIGHT,
            spacing1=self.theme.SPACING_SM,  # 增加上间距
            spacing3=self.theme.SPACING_SM,  # 增加下间距
            justify=tk.LEFT)

        # 四级标题 - 小节标题
        self.text_widget.tag_configure("h4",
            font=(self.theme.FONT_FAMILY_PRIMARY, self.theme.FONT_SIZE_BASE, "bold"),
            foreground=self.theme.WARNING_LIGHT,
            spacing1=self.theme.SPACING_SM,  # 增加上间距
            spacing3=self.theme.SPACING_XS,  # 增加下间距
            justify=tk.LEFT)

        # 粗体和斜体 - 调整字体大小
        self.text_widget.tag_configure("bold",
            font=(self.theme.FONT_FAMILY_SECONDARY, self.theme.FONT_SIZE_SM, "bold"),
            foreground=self.theme.PRIMARY_LIGHT)

        self.text_widget.tag_configure("italic",
            font=(self.theme.FONT_FAMILY_SECONDARY, self.theme.FONT_SIZE_SM, "italic"),
            foreground=self.theme.SECONDARY_LIGHT)

        # 代码样式 - 移除边框，简化设计
        self.text_widget.tag_configure("code",
            font=(self.theme.FONT_FAMILY_MONO, self.theme.FONT_SIZE_XS),
            foreground=self.theme.SUCCESS_LIGHT,
            background=self.theme.BACKGROUND_TERTIARY)

        # 列表样式 - 现代化列表设计，更好的间距和视觉层次
        self.text_widget.tag_configure("list",
            font=(self.theme.FONT_FAMILY_SECONDARY, self.theme.FONT_SIZE_SM),
            foreground=self.theme.TEXT_PRIMARY,
            lmargin1=self.theme.SPACING_LG,  # 增加左边距
            lmargin2=self.theme.SPACING_XL,  # 增加续行缩进
            spacing1=self.theme.SPACING_XS,  # 增加列表项间距
            spacing3=self.theme.SPACING_XS)

        # 引用样式 - 现代化引用块设计，更醒目的视觉效果
        self.text_widget.tag_configure("quote",
            font=(self.theme.FONT_FAMILY_SECONDARY, self.theme.FONT_SIZE_SM, "italic"),
            foreground=self.theme.SECONDARY_LIGHT,
            lmargin1=self.theme.SPACING_LG,  # 增加左边距
            lmargin2=self.theme.SPACING_LG,  # 保持一致的缩进
            rmargin=self.theme.SPACING_MD,   # 增加右边距
            spacing1=self.theme.SPACING_SM,  # 增加上间距
            spacing3=self.theme.SPACING_SM,  # 增加下间距
            background=self.theme.BACKGROUND_TERTIARY)

        # 普通文本 - 调整字体大小
        self.text_widget.tag_configure("normal",
            font=(self.theme.FONT_FAMILY_SECONDARY, self.theme.FONT_SIZE_SM),
            foreground=self.theme.TEXT_PRIMARY)

        # 分隔线样式 - 调整字体大小
        self.text_widget.tag_configure("separator",
            font=(self.theme.FONT_FAMILY_PRIMARY, self.theme.FONT_SIZE_XS),
            foreground=self.theme.BORDER_DEFAULT,
            justify=tk.CENTER)

        # 强调文本 - 调整字体大小
        self.text_widget.tag_configure("emphasis",
            font=(self.theme.FONT_FAMILY_PRIMARY, self.theme.FONT_SIZE_SM, "bold"),
            foreground=self.theme.PRIMARY_LIGHT)

        # 链接样式 - 调整字体大小
        self.text_widget.tag_configure("link",
            font=(self.theme.FONT_FAMILY_SECONDARY, self.theme.FONT_SIZE_SM, "underline"),
            foreground=self.theme.SECONDARY_LIGHT)

        # 表格样式 - 调整字体大小
        self.text_widget.tag_configure("table",
            font=(self.theme.FONT_FAMILY_MONO, self.theme.FONT_SIZE_XS),
            foreground=self.theme.TEXT_PRIMARY,
            background=self.theme.BACKGROUND_TERTIARY)

    def render(self, markdown_text):
        """渲染Markdown文本到Text组件"""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)

        lines = markdown_text.split('\n')

        for line in lines:
            self._render_line(line)

        self.text_widget.config(state=tk.DISABLED)

    def _render_line(self, line):
        """渲染单行文本 - 美化版本"""
        # 标题 - 支持更多级别和美化
        if line.startswith('# '):
            self.text_widget.insert(tk.END, f"🎯 {line[2:]}\n", "h1")
        elif line.startswith('## '):
            self.text_widget.insert(tk.END, f"✨ {line[3:]}\n", "h2")
        elif line.startswith('### '):
            self.text_widget.insert(tk.END, f"🔧 {line[4:]}\n", "h3")
        elif line.startswith('#### '):
            self.text_widget.insert(tk.END, f"📋 {line[5:]}\n", "h4")
        # 美化分隔线
        elif line.strip() in ['---', '***', '___']:
            self.text_widget.insert(tk.END, '\n', "normal")
            self.text_widget.insert(tk.END, '━' * 60 + '\n', "separator")
            self.text_widget.insert(tk.END, '\n', "normal")
        # 美化列表
        elif line.startswith('- ') or line.startswith('* '):
            self._render_inline_formatting(f"  ▸ {line[2:]}\n", "list")
        elif re.match(r'^\d+\. ', line):
            match = re.match(r'^(\d+)\. (.*)$', line)
            if match:
                self._render_inline_formatting(f"  {match.group(1)}. {match.group(2)}\n", "list")
        # 美化引用
        elif line.startswith('> '):
            self._render_inline_formatting(f"💭 {line[2:]}\n", "quote")
        # 美化代码块
        elif line.startswith('```'):
            if line.strip() == '```':
                self.text_widget.insert(tk.END, '└' + '─' * 58 + '┘\n\n', "code")
            else:
                lang = line[3:].strip()
                if lang:
                    self.text_widget.insert(tk.END, f"\n┌─ 📝 {lang.upper()} " + '─' * (50 - len(lang)) + '┐\n', "code")
                else:
                    self.text_widget.insert(tk.END, '\n┌─ 💻 CODE ' + '─' * 47 + '┐\n', "code")
        # 美化表格
        elif '|' in line and line.count('|') >= 2:
            formatted_line = line.replace('|', ' │ ').strip()
            self.text_widget.insert(tk.END, f"  {formatted_line}\n", "table")
        # 美化任务列表
        elif line.startswith('- [ ]') or line.startswith('- [x]'):
            checkbox = '☐' if '[ ]' in line else '✅'
            content = line[5:].strip()
            self._render_inline_formatting(f"    {checkbox} {content}\n", "list")
        # 空行
        elif line.strip() == '':
            self.text_widget.insert(tk.END, '\n', "normal")
        # 普通文本（处理内联格式）
        else:
            self._render_inline_formatting(line + '\n')

    def _render_inline_formatting(self, text, default_tag="normal"):
        """处理内联格式（粗体、斜体、代码）"""
        # 更完善的内联格式处理
        parts = []
        current_pos = 0

        # 按优先级处理各种格式
        patterns = [
            (r'\*\*(.*?)\*\*', "bold"),      # 粗体
            (r'\*(.*?)\*', "italic"),        # 斜体
            (r'`(.*?)`', "code"),            # 内联代码
        ]

        # 找到所有匹配项并按位置排序
        matches = []
        for pattern, tag in patterns:
            for match in re.finditer(pattern, text):
                matches.append((match.start(), match.end(), match.group(1), tag))

        matches.sort(key=lambda x: x[0])  # 按开始位置排序

        # 处理重叠问题，优先处理较早出现的格式
        filtered_matches = []
        last_end = 0
        for start, end, content, tag in matches:
            if start >= last_end:
                filtered_matches.append((start, end, content, tag))
                last_end = end

        # 构建格式化文本片段
        current_pos = 0
        for start, end, content, tag in filtered_matches:
            # 添加前面的普通文本
            if start > current_pos:
                parts.append((text[current_pos:start], default_tag))
            # 添加格式化文本
            parts.append((content, tag))
            current_pos = end

        # 添加剩余的普通文本
        if current_pos < len(text):
            parts.append((text[current_pos:], default_tag))

        # 如果没有找到任何格式，整个文本都使用默认格式
        if not parts:
            parts = [(text, default_tag)]

        # 插入格式化文本
        for part_text, tag in parts:
            if part_text:  # 只插入非空文本
                self.text_widget.insert(tk.END, part_text, tag)

# 商业级深色主题配置
class ModernTheme:
    """商业级深色主题配置 - 专业科技感设计"""

    # === 高端大气上档次配色系统 ===
    # 深邃奢华背景系统 - 顶级质感
    BACKGROUND_PRIMARY = "#0D1117"      # 深邃主背景 - GitHub风格
    BACKGROUND_SECONDARY = "#161B22"    # 中层背景 - 层次分明
    BACKGROUND_TERTIARY = "#21262D"     # 浅层背景 - 精致对比
    BACKGROUND_ELEVATED = "#30363D"     # 悬浮背景 - 高端质感

    # 奢华圆角卡片系统 - 高端设计
    CARD_BACKGROUND = "#161B22"         # 卡片背景 - 奢华质感
    CARD_BACKGROUND_HOVER = "#1C2128"   # 卡片悬停 - 微妙变化
    CARD_BORDER = "#30363D"             # 精致分隔 - 高端设计
    CARD_BORDER_HOVER = "#58A6FF"       # 悬停强调 - 高端蓝
    CARD_SHADOW = "rgba(0,0,0,0.4)"     # 深度阴影 - 奢华层次

    # 专业级主色调系统 - 参考Apple/Google设计系统
    PRIMARY = "#007AFF"                 # Apple蓝 - 专业权威
    PRIMARY_HOVER = "#0056CC"           # 悬停态 - 深度蓝
    PRIMARY_ACTIVE = "#004499"          # 激活态 - 最深蓝
    PRIMARY_LIGHT = "#4DA6FF"           # 浅色变体 - 友好蓝
    PRIMARY_DARK = "#003366"            # 深色变体 - 权威深蓝
    PRIMARY_GLOW = "#007AFF"            # 发光效果

    # 专业级渐变系统 - 现代科技感
    GRADIENT_START = "#007AFF"          # 渐变起始色 - Apple蓝
    GRADIENT_END = "#0056CC"            # 渐变结束色 - 深蓝
    GRADIENT_HOVER_START = "#0056CC"    # 悬停渐变起始 - 深蓝
    GRADIENT_HOVER_END = "#004499"      # 悬停渐变结束 - 最深蓝

    # 专业级次要色调 - 参考Google Material Design
    SECONDARY = "#00C853"               # Material绿 - 专业活力
    SECONDARY_HOVER = "#00A843"         # 悬停态
    SECONDARY_ACTIVE = "#008A33"        # 激活态
    SECONDARY_LIGHT = "#4CAF50"         # 浅色变体
    SECONDARY_GLOW = "#00C853"          # 发光效果

    # 专业级成功色 - Material Design绿色系
    SUCCESS = "#4CAF50"                 # Material成功绿 - 可靠稳定
    SUCCESS_HOVER = "#43A047"           # 悬停态
    SUCCESS_ACTIVE = "#388E3C"          # 激活态
    SUCCESS_LIGHT = "#81C784"           # 浅色变体
    SUCCESS_GLOW = "#4CAF50"            # 发光效果

    # 专业级警告色 - Material Design橙色系
    WARNING = "#FF9800"                 # Material警告橙 - 专业提醒
    WARNING_HOVER = "#F57C00"           # 悬停态
    WARNING_ACTIVE = "#E65100"          # 激活态
    WARNING_LIGHT = "#FFB74D"           # 浅色变体
    WARNING_GLOW = "#FF9800"            # 发光效果

    # 专业级危险色 - Material Design红色系
    DANGER = "#F44336"                  # Material危险红 - 专业警示
    DANGER_HOVER = "#E53935"            # 悬停态
    DANGER_ACTIVE = "#D32F2F"           # 激活态
    DANGER_LIGHT = "#EF5350"            # 浅色变体
    DANGER_GLOW = "#F44336"             # 发光效果

    # 专业级文字色系 - WCAG AAA级对比度
    TEXT_PRIMARY = "#FFFFFF"            # 主要文字 - 纯白高对比度
    TEXT_SECONDARY = "#CCCCCC"          # 次要文字 - 专业灰色
    TEXT_MUTED = "#999999"              # 弱化文字 - 中性灰色
    TEXT_DISABLED = "#666666"           # 禁用文字 - 深灰色
    TEXT_INVERSE = "#1E1E1E"            # 反色文字（用于亮色背景）
    TEXT_ACCENT = "#007AFF"             # 强调文字 - Apple蓝

    # 简洁美观边框色系 - 温暖舒适
    BORDER_DEFAULT = "#4A4E6B"          # 温暖边框 - 柔和清晰
    BORDER_MUTED = "#3A3D5C"            # 弱化边框 - 温暖层次
    BORDER_SUBTLE = "#5A5E7A"           # 微妙边框 - 温暖对比
    BORDER_FOCUS = "#007AFF"            # 聚焦边框 - Apple蓝
    BORDER_SUCCESS = "#4CAF50"          # 成功边框 - Material绿
    BORDER_DANGER = "#F44336"           # 危险边框 - Material红

    # 简洁美观输入框系统 - 舒适体验
    INPUT_BACKGROUND = "#3A3D5C"        # 温暖输入框背景 - 舒适感
    INPUT_BORDER = "#4A4E6B"            # 温暖输入框边框 - 柔和清晰
    INPUT_BORDER_FOCUS = "#007AFF"      # 聚焦时边框 - Apple蓝
    INPUT_PLACEHOLDER = "#B8BCC8"       # 温暖占位符文字 - 柔和可读

    # 简洁美观滚动条系统 - 温暖融合
    SCROLLBAR_TRACK = "#3A3D5C"         # 滚动条轨道（与温暖背景融合）
    SCROLLBAR_THUMB = "#4A4E6B"         # 滚动条滑块（温暖可见）
    SCROLLBAR_THUMB_HOVER = "#007AFF"   # 滚动条滑块悬停（Apple蓝）
    SCROLLBAR_WIDTH = 8                 # 滚动条宽度（更细）

    # 阴影系统 - 多层次深度
    SHADOW_XS = "#000000"               # 极小阴影
    SHADOW_SM = "#000000"               # 小阴影
    SHADOW_MD = "#000000"               # 中等阴影
    SHADOW_LG = "#000000"               # 大阴影
    SHADOW_XL = "#000000"               # 超大阴影
    SHADOW_GLOW = "#4338ca"             # 发光阴影

    # 渐变色系 - 现代科技感
    GRADIENT_PRIMARY = "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)"
    GRADIENT_SECONDARY = "linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)"
    GRADIENT_SUCCESS = "linear-gradient(135deg, #10b981 0%, #059669 100%)"
    GRADIENT_DANGER = "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)"
    GRADIENT_CARD = "linear-gradient(145deg, #1c2128 0%, #161b22 100%)"

    # 字体系统 - 现代化层次
    FONT_FAMILY_PRIMARY = "Segoe UI"    # 主字体
    FONT_FAMILY_SECONDARY = "Microsoft YaHei UI"  # 中文字体
    FONT_FAMILY_MONO = "Consolas"       # 等宽字体

    # 字体大小系统 - 优化版本，避免过大
    FONT_SIZE_XS = 8                    # 极小
    FONT_SIZE_SM = 9                    # 小
    FONT_SIZE_BASE = 10                 # 基础
    FONT_SIZE_LG = 11                   # 大
    FONT_SIZE_XL = 12                   # 超大
    FONT_SIZE_2XL = 13                  # 2倍大
    FONT_SIZE_3XL = 14                  # 3倍大
    FONT_SIZE_4XL = 16                  # 4倍大

    # 字重系统
    FONT_WEIGHT_LIGHT = "normal"
    FONT_WEIGHT_NORMAL = "normal"
    FONT_WEIGHT_MEDIUM = "bold"
    FONT_WEIGHT_BOLD = "bold"

    # 间距系统 - 8px基准
    SPACING_XS = 4                      # 极小间距
    SPACING_SM = 8                      # 小间距
    SPACING_MD = 16                     # 中等间距
    SPACING_LG = 24                     # 大间距
    SPACING_XL = 32                     # 超大间距
    SPACING_2XL = 48                    # 2倍大间距

    # 圆角系统
    RADIUS_SM = 4                       # 小圆角
    RADIUS_MD = 8                       # 中等圆角
    RADIUS_LG = 12                      # 大圆角
    RADIUS_XL = 16                      # 超大圆角
    RADIUS_FULL = 9999                  # 完全圆角

    @staticmethod
    def create_card_style():
        """创建现代化无边框卡片样式 - 扁平化设计"""
        return {
            "bg": ModernTheme.CARD_BACKGROUND,
            "relief": tk.FLAT,
            "bd": 0,
            "highlightthickness": 0  # 完全无边框
        }

    @staticmethod
    def create_elevated_card_style():
        """创建现代化悬浮卡片样式 - 背景色差异层次"""
        return {
            "bg": ModernTheme.BACKGROUND_ELEVATED,
            "relief": tk.FLAT,
            "bd": 0,
            "highlightthickness": 0  # 完全无边框，用背景色区分
        }

    @staticmethod
    def create_premium_card_style():
        """创建现代化高级卡片样式 - 无边框扁平设计"""
        return {
            "bg": ModernTheme.CARD_BACKGROUND,
            "relief": tk.FLAT,  # 扁平化设计
            "bd": 0,  # 无边框
            "highlightthickness": 0  # 完全无边框
        }

    @staticmethod
    def create_modern_flat_card_style():
        """创建现代化扁平卡片样式 - Web应用风格"""
        return {
            "bg": ModernTheme.BACKGROUND_SECONDARY,
            "relief": tk.FLAT,
            "bd": 0,
            "highlightthickness": 0  # 现代化无边框设计
        }

    @staticmethod
    def create_borderless_input_style():
        """创建完全无边框输入框样式 - 现代Web风格"""
        return {
            "bg": ModernTheme.INPUT_BACKGROUND,
            "fg": ModernTheme.TEXT_PRIMARY,
            "relief": tk.FLAT,  # 完全扁平
            "bd": 0,  # 无边框
            "highlightthickness": 0,  # 无聚焦边框
            "highlightbackground": ModernTheme.INPUT_BACKGROUND,
            "highlightcolor": ModernTheme.INPUT_BACKGROUND,
            "insertbackground": ModernTheme.PRIMARY,
            "selectbackground": ModernTheme.PRIMARY_LIGHT,
            "selectforeground": ModernTheme.TEXT_PRIMARY
        }

    @staticmethod
    def create_subtle_focus_input_style():
        """创建微妙聚焦效果输入框样式 - 现代化设计"""
        return {
            "bg": ModernTheme.INPUT_BACKGROUND,
            "fg": ModernTheme.TEXT_PRIMARY,
            "relief": tk.FLAT,  # 扁平设计
            "bd": 0,  # 无边框
            "highlightthickness": 1,  # 极细的聚焦提示
            "highlightbackground": ModernTheme.INPUT_BACKGROUND,  # 默认与背景同色
            "highlightcolor": ModernTheme.PRIMARY,  # 聚焦时主色调
            "insertbackground": ModernTheme.PRIMARY,
            "selectbackground": ModernTheme.PRIMARY_LIGHT,
            "selectforeground": ModernTheme.TEXT_PRIMARY
        }

    @staticmethod
    def create_input_style():
        """创建现代化无边框输入框样式 - 扁平化设计"""
        return {
            "bg": ModernTheme.INPUT_BACKGROUND,
            "fg": ModernTheme.TEXT_PRIMARY,
            "relief": tk.FLAT,  # 现代化扁平设计
            "bd": 0,  # 完全无边框
            "highlightthickness": 1,  # 微妙的聚焦提示
            "highlightbackground": ModernTheme.INPUT_BACKGROUND,  # 默认与背景同色
            "highlightcolor": ModernTheme.PRIMARY,  # 聚焦时主色调
            "insertbackground": ModernTheme.PRIMARY,
            "selectbackground": ModernTheme.PRIMARY_LIGHT,
            "selectforeground": ModernTheme.TEXT_PRIMARY
        }

    @staticmethod
    def create_enhanced_input_style():
        """创建现代化无边框增强输入框样式 - Web应用风格"""
        return {
            "bg": ModernTheme.INPUT_BACKGROUND,
            "fg": ModernTheme.TEXT_PRIMARY,
            "relief": tk.FLAT,  # 扁平化无边框设计
            "bd": 0,  # 完全无边框
            "highlightthickness": 2,  # 聚焦时的颜色变化提示
            "highlightbackground": ModernTheme.INPUT_BACKGROUND,  # 默认与背景同色
            "highlightcolor": ModernTheme.PRIMARY_GLOW,  # 聚焦时发光效果
            "insertbackground": ModernTheme.PRIMARY,
            "selectbackground": ModernTheme.PRIMARY_LIGHT,
            "selectforeground": ModernTheme.TEXT_PRIMARY
        }

class ModernScrolledText(tk.Frame):
    """现代化无边框滚动文本框组件"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=ModernTheme.INPUT_BACKGROUND, relief=tk.FLAT, bd=0)

        # 提取文本框特定参数
        text_kwargs = {}
        frame_kwargs = {}

        for key, value in kwargs.items():
            if key in ['wrap', 'font', 'padx', 'pady', 'state', 'cursor', 'height', 'width']:
                text_kwargs[key] = value
            else:
                frame_kwargs[key] = value

        # 创建前端专家级文本框
        input_style = ModernTheme.create_enhanced_input_style()
        # 合并样式，避免重复参数
        final_style = {**input_style, **text_kwargs}

        self.text = tk.Text(
            self,
            **final_style
        )

        # 创建完全隐藏的滚动条 - 只保留滚动功能
        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.text.yview,
            bg=ModernTheme.INPUT_BACKGROUND,  # 与背景同色
            troughcolor=ModernTheme.INPUT_BACKGROUND,  # 轨道与背景同色
            activebackground=ModernTheme.INPUT_BACKGROUND,  # 激活时也与背景同色
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            width=0  # 设置宽度为0，完全隐藏
        )

        # 配置文本框滚动
        self.text.configure(yscrollcommand=self.scrollbar.set)

        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            self.text.yview_scroll(int(-1*(event.delta/120)), "units")

        self.text.bind("<MouseWheel>", _on_mousewheel)
        self.text.bind("<Button-4>", lambda e: self.text.yview_scroll(-1, "units"))
        self.text.bind("<Button-5>", lambda e: self.text.yview_scroll(1, "units"))

        # 布局 - 不显示滚动条
        self.text.pack(side="left", fill="both", expand=True)

        # 代理常用方法
        self.insert = self.text.insert
        self.delete = self.text.delete
        self.get = self.text.get
        self.bind = self.text.bind
        self.config = self.text.config
        self.configure = self.text.configure
        self.tag_configure = self.text.tag_configure
        self.tag_add = self.text.tag_add
        self.tag_remove = self.text.tag_remove

class RoundedButton(tk.Canvas):
    """现代化圆角按钮组件 - 支持圆角和无边框设计"""

    def __init__(self, parent, text="", command=None, style="primary", size="medium", icon="", radius=8, **kwargs):
        # 根据大小设置尺寸
        if size == "small":
            width, height = 80, 32
            font_size = 10
        elif size == "large":
            width, height = 120, 44
            font_size = 12
        elif size == "xl":
            width, height = 140, 48
            font_size = 14
        else:  # medium
            width, height = 100, 36
            font_size = 11

        super().__init__(parent, width=width, height=height, highlightthickness=0, **kwargs)

        self.text = text
        self.icon = icon
        self.command = command
        self.style = style
        self.radius = radius
        self.font_size = font_size
        self.is_pressed = False
        self.is_hovered = False

        # 设置颜色
        self._setup_colors()

        # 绘制按钮
        self._draw_button()

        # 绑定事件
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _setup_colors(self):
        """设置按钮颜色"""
        if self.style == "primary":
            self.bg_color = ModernTheme.PRIMARY
            self.hover_color = ModernTheme.PRIMARY_HOVER
            self.active_color = ModernTheme.PRIMARY_ACTIVE
            self.text_color = "#ffffff"
        elif self.style == "secondary":
            self.bg_color = ModernTheme.SECONDARY
            self.hover_color = ModernTheme.SECONDARY_HOVER
            self.active_color = ModernTheme.SECONDARY_ACTIVE
            self.text_color = "#ffffff"
        elif self.style == "success":
            self.bg_color = ModernTheme.SUCCESS
            self.hover_color = ModernTheme.SUCCESS_HOVER
            self.active_color = ModernTheme.SUCCESS_ACTIVE
            self.text_color = "#ffffff"
        elif self.style == "danger":
            self.bg_color = ModernTheme.DANGER
            self.hover_color = ModernTheme.DANGER_HOVER
            self.active_color = ModernTheme.DANGER_ACTIVE
            self.text_color = "#ffffff"
        elif self.style == "outline":
            self.bg_color = ModernTheme.BACKGROUND_PRIMARY
            self.hover_color = ModernTheme.PRIMARY
            self.active_color = ModernTheme.PRIMARY_ACTIVE
            self.text_color = ModernTheme.PRIMARY
        else:  # default
            self.bg_color = ModernTheme.BACKGROUND_ELEVATED
            self.hover_color = ModernTheme.BACKGROUND_TERTIARY
            self.active_color = ModernTheme.CARD_BACKGROUND
            self.text_color = ModernTheme.TEXT_PRIMARY

    def _draw_button(self):
        """绘制高端圆角按钮"""
        self.delete("all")

        # 确定当前颜色
        if self.is_pressed:
            current_color = self.active_color
        elif self.is_hovered:
            current_color = self.hover_color
        else:
            current_color = self.bg_color

        # 获取实际尺寸
        width = self.winfo_width() if self.winfo_width() > 1 else self.winfo_reqwidth()
        height = self.winfo_height() if self.winfo_height() > 1 else self.winfo_reqheight()

        # 设置画布背景为透明
        parent_bg = self.master.cget('bg') if hasattr(self.master, 'cget') else ModernTheme.BACKGROUND_PRIMARY
        self.configure(bg=parent_bg)

        # 绘制高端圆角矩形（带阴影效果）
        # 阴影层（使用深灰色模拟阴影）
        shadow_offset = 1
        shadow_color = "#1a1a1a"  # 深灰色阴影
        self._draw_rounded_rect(shadow_offset, shadow_offset, width-2+shadow_offset, height-2+shadow_offset,
                               self.radius, shadow_color)

        # 主按钮层
        self._draw_rounded_rect(1, 1, width-1, height-1, self.radius, current_color)

        # 高光层（增加立体感）
        if not self.is_pressed:
            highlight_color = self._lighten_color(current_color, 0.15)
            self._draw_rounded_rect(1, 1, width-1, height//2+2, self.radius, highlight_color, top_only=True)

        # 绘制文本
        display_text = f"{self.icon} {self.text}" if self.icon else self.text
        text_y = height//2 + (1 if self.is_pressed else 0)  # 按下时文字微移
        self.create_text(width//2, text_y,
                        text=display_text, fill=self.text_color,
                        font=(ModernTheme.FONT_FAMILY_PRIMARY, self.font_size, "bold"))

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius, fill_color, top_only=False):
        """绘制高端圆角矩形"""
        # 绘制主体矩形
        if top_only:
            # 只绘制上半部分
            self.create_rectangle(x1 + radius, y1, x2 - radius, y1 + radius, fill=fill_color, outline="")
            self.create_rectangle(x1, y1 + radius, x2, y1 + radius, fill=fill_color, outline="")
            # 只绘制上面两个圆角
            self.create_oval(x1, y1, x1 + 2*radius, y1 + 2*radius, fill=fill_color, outline="")
            self.create_oval(x2 - 2*radius, y1, x2, y1 + 2*radius, fill=fill_color, outline="")
        else:
            # 绘制完整的圆角矩形
            self.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill_color, outline="")
            self.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill_color, outline="")

            # 绘制四个圆角
            self.create_oval(x1, y1, x1 + 2*radius, y1 + 2*radius, fill=fill_color, outline="")
            self.create_oval(x2 - 2*radius, y1, x2, y1 + 2*radius, fill=fill_color, outline="")
            self.create_oval(x1, y2 - 2*radius, x1 + 2*radius, y2, fill=fill_color, outline="")
            self.create_oval(x2 - 2*radius, y2 - 2*radius, x2, y2, fill=fill_color, outline="")

    def _lighten_color(self, color, factor):
        """颜色变亮处理"""
        try:
            # 移除#号
            color = color.lstrip('#')
            # 转换为RGB
            r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            # 变亮
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            # 转换回十六进制
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color

    def _on_click(self, event):
        """点击事件处理"""
        if self.command:
            try:
                self.command()
            except Exception as e:
                print(f"按钮点击错误: {e}")
                import traceback
                traceback.print_exc()

    def _on_enter(self, event):
        """鼠标进入事件"""
        self.is_hovered = True
        self.configure(cursor="hand2")
        self._draw_button()

    def _on_leave(self, event):
        """鼠标离开事件"""
        self.is_hovered = False
        self.configure(cursor="")
        self._draw_button()

    def _on_press(self, event):
        """鼠标按下事件"""
        self.is_pressed = True
        self._draw_button()

    def _on_release(self, event):
        """鼠标释放事件"""
        self.is_pressed = False
        self._draw_button()

class ModernButton(tk.Button):
    """商业级现代化按钮组件 - 深色主题专业设计（兼容性版本）"""

    def __init__(self, parent, text="", command=None, style="primary", size="medium", icon="", **kwargs):
        # 根据样式设置颜色 - 企业级专业配色
        if style == "primary":
            bg_color = ModernTheme.PRIMARY  # 企业蓝
            hover_color = ModernTheme.PRIMARY_HOVER  # 悬停时更深
            active_color = ModernTheme.PRIMARY_ACTIVE  # 按下时最深
            text_color = "#ffffff"  # 白色文字确保对比度
            border_color = ModernTheme.PRIMARY
            glow_color = ModernTheme.PRIMARY_GLOW
        elif style == "secondary":
            bg_color = ModernTheme.SECONDARY  # 企业青绿
            hover_color = ModernTheme.SECONDARY_HOVER  # 悬停时更深
            active_color = ModernTheme.SECONDARY_ACTIVE  # 按下时最深
            text_color = "#ffffff"  # 白色文字
            border_color = ModernTheme.SECONDARY
            glow_color = ModernTheme.SECONDARY_GLOW
        elif style == "success":
            bg_color = ModernTheme.SUCCESS  # 企业成功绿
            hover_color = ModernTheme.SUCCESS_HOVER  # 悬停时更深
            active_color = ModernTheme.SUCCESS_ACTIVE  # 按下时最深
            text_color = "#ffffff"  # 白色文字
            border_color = ModernTheme.SUCCESS
            glow_color = ModernTheme.SUCCESS_GLOW
        elif style == "danger":
            bg_color = ModernTheme.DANGER  # 企业危险红
            hover_color = ModernTheme.DANGER_HOVER  # 悬停时更深
            active_color = ModernTheme.DANGER_ACTIVE  # 按下时最深
            text_color = "#ffffff"  # 白色文字
            border_color = ModernTheme.DANGER
            glow_color = ModernTheme.DANGER_GLOW
        elif style == "outline":
            bg_color = ModernTheme.BACKGROUND_PRIMARY  # 使用主背景色
            hover_color = ModernTheme.PRIMARY  # 悬停时填充企业蓝
            active_color = ModernTheme.PRIMARY_ACTIVE  # 按下时更深
            text_color = ModernTheme.PRIMARY  # 企业蓝文字
            border_color = ModernTheme.PRIMARY  # 企业蓝边框
            glow_color = ModernTheme.PRIMARY_GLOW
        elif style == "ghost":
            bg_color = ModernTheme.BACKGROUND_PRIMARY  # 使用主背景色
            hover_color = ModernTheme.BACKGROUND_ELEVATED  # 悬停时微妙填充
            active_color = ModernTheme.BACKGROUND_TERTIARY  # 按下时更深
            text_color = ModernTheme.TEXT_SECONDARY  # 次要文字色
            border_color = ModernTheme.BACKGROUND_PRIMARY  # 与背景同色
            glow_color = ModernTheme.PRIMARY_GLOW
        else:  # default
            bg_color = ModernTheme.BACKGROUND_ELEVATED  # 企业级中性色
            hover_color = ModernTheme.BACKGROUND_TERTIARY  # 悬停时更深
            active_color = ModernTheme.CARD_BACKGROUND  # 按下时最深
            text_color = ModernTheme.TEXT_PRIMARY  # 主要文字色
            border_color = ModernTheme.CARD_BORDER
            glow_color = ModernTheme.PRIMARY_GLOW

        # 根据大小设置字体和间距 - 现代化尺寸系统
        if size == "small":
            font_size = ModernTheme.FONT_SIZE_SM
            padx, pady = ModernTheme.SPACING_SM + 4, ModernTheme.SPACING_XS + 2
            font_weight = ModernTheme.FONT_WEIGHT_MEDIUM
        elif size == "large":
            font_size = ModernTheme.FONT_SIZE_LG
            padx, pady = ModernTheme.SPACING_LG, ModernTheme.SPACING_MD
            font_weight = ModernTheme.FONT_WEIGHT_BOLD
        elif size == "xl":
            font_size = ModernTheme.FONT_SIZE_XL
            padx, pady = ModernTheme.SPACING_XL, ModernTheme.SPACING_LG
            font_weight = ModernTheme.FONT_WEIGHT_BOLD
        else:  # medium
            font_size = ModernTheme.FONT_SIZE_BASE
            padx, pady = ModernTheme.SPACING_MD, ModernTheme.SPACING_SM
            font_weight = ModernTheme.FONT_WEIGHT_MEDIUM

        # 处理图标和文本
        display_text = f"{icon} {text}" if icon else text

        # 现代化无边框按钮样式 - 扁平化设计
        default_style = {
            "bg": bg_color,
            "fg": text_color,
            "font": (ModernTheme.FONT_FAMILY_PRIMARY, font_size, font_weight),
            "relief": tk.FLAT,  # 现代化扁平设计
            "bd": 0,  # 完全无边框
            "cursor": "hand2",
            "padx": padx + 4,  # 增加内边距
            "pady": pady + 2,
            "activebackground": hover_color,
            "activeforeground": text_color,
            "highlightthickness": 0,  # 无高亮边框
            "highlightbackground": bg_color,  # 与背景同色
            "highlightcolor": bg_color,  # 与背景同色
            "borderwidth": 0,  # 无边框
            "overrelief": tk.FLAT  # 悬停时保持扁平
        }

        # 合并用户提供的样式
        default_style.update(kwargs)

        super().__init__(parent, text=display_text, command=command, **default_style)

        # 保存颜色状态用于动画效果
        self.normal_bg = bg_color
        self.hover_bg = hover_color
        self.active_bg = active_color
        self.text_color = text_color
        self.border_color = border_color
        self.glow_color = glow_color
        self.style_type = style

        # 动画状态
        self.is_pressed = False
        self.animation_id = None

        # 绑定现代化交互事件
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_enter(self, event):
        """鼠标悬停效果 - 现代化无边框微交互"""
        if not self.is_pressed:
            # 平滑颜色过渡动画
            self._animate_color_transition(self.hover_bg, duration=150)
            # 微妙的缩放效果（无边框）
            self._animate_scale(1.02)

    def _on_leave(self, event):
        """鼠标离开效果 - 现代化平滑恢复"""
        if not self.is_pressed:
            # 平滑恢复动画
            self._animate_color_transition(self.normal_bg, duration=200)
            self._animate_scale(1.0)

    def _on_press(self, event):
        """按下效果 - 现代化扁平按压反馈"""
        self.is_pressed = True
        # 快速按压动画（无边框）
        self._animate_color_transition(self.active_bg, duration=50)
        self._animate_scale(0.98)

    def _on_release(self, event):
        """释放效果 - 现代化无边框恢复"""
        self.is_pressed = False
        # 检查鼠标是否还在按钮上
        x, y = event.x, event.y
        if 0 <= x <= self.winfo_width() and 0 <= y <= self.winfo_height():
            # 悬停状态（无边框）
            self.config(bg=self.hover_bg, relief=tk.FLAT, bd=0, highlightthickness=0)
        else:
            # 正常状态（无边框）
            self.config(bg=self.normal_bg, relief=tk.FLAT, bd=0, highlightthickness=0)

    def _on_focus_in(self, event):
        """获得焦点时的视觉反馈 - 现代化无边框发光效果"""
        # 使用微妙的背景色变化替代边框
        if self.style_type == "outline":
            self.config(bg=self.hover_bg)
        else:
            # 为主要按钮添加微妙的亮度变化
            self.config(bg=self.hover_bg)

    def _on_focus_out(self, event):
        """失去焦点时恢复 - 无边框设计"""
        self.config(bg=self.normal_bg)

    def set_loading(self, loading=True):
        """设置加载状态"""
        if loading:
            self.config(text="⏳ 处理中...", state=tk.DISABLED)
        else:
            # 恢复原始文本需要在外部处理
            self.config(state=tk.NORMAL)

    def _animate_color_transition(self, target_color, duration=150):
        """前端专家级颜色过渡动画"""
        try:
            self.config(bg=target_color)
        except:
            pass

    def _animate_scale(self, scale_factor=1.02):
        """现代化无边框缩放效果（模拟）"""
        # tkinter限制，通过调整padding模拟缩放
        try:
            current_padx = self.cget("padx")
            current_pady = self.cget("pady")
            if scale_factor > 1:
                self.config(padx=current_padx + 2, pady=current_pady + 1)
            else:
                self.config(padx=max(0, current_padx - 2), pady=max(0, current_pady - 1))
        except:
            pass

    def pulse_effect(self):
        """现代化无边框脉冲效果动画"""
        def animate_pulse():
            # 第一阶段：放大 + 变亮（无边框）
            self._animate_scale(1.05)
            self._animate_color_transition(self.hover_bg)

            # 第二阶段：恢复（无边框）
            self.animation_id = self.after(200, lambda: [
                self._animate_scale(1.0),
                self._animate_color_transition(self.normal_bg)
            ])

        animate_pulse()

class RoundedFrame(tk.Frame):
    """高端圆角卡片组件 - 奢华质感设计"""

    def __init__(self, parent, radius=12, shadow=True, **kwargs):
        # 提取背景色
        bg_color = kwargs.pop('bg', ModernTheme.CARD_BACKGROUND)

        super().__init__(parent, bg=parent.cget('bg') if hasattr(parent, 'cget') else ModernTheme.BACKGROUND_PRIMARY,
                        relief=tk.FLAT, bd=0, highlightthickness=0)

        self.radius = radius
        self.bg_color = bg_color
        self.shadow = shadow

        # 创建Canvas来绘制圆角
        self.canvas = tk.Canvas(self, highlightthickness=0, **kwargs)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 内容框架
        self.content_frame = tk.Frame(self.canvas, bg=bg_color, relief=tk.FLAT, bd=0)

        # 绑定事件
        self.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_configure(self, event):
        """窗口大小改变时重绘"""
        self._draw_rounded_background()

    def _on_canvas_configure(self, event):
        """Canvas大小改变时重绘"""
        self._draw_rounded_background()

    def _draw_rounded_background(self):
        """绘制高端圆角背景"""
        self.canvas.delete("background")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        # 设置Canvas背景
        parent_bg = self.master.cget('bg') if hasattr(self.master, 'cget') else ModernTheme.BACKGROUND_PRIMARY
        self.canvas.configure(bg=parent_bg)

        # 绘制阴影（如果启用）
        if self.shadow:
            shadow_offset = 2
            shadow_color = "#0f0f0f"  # 深色阴影
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

        # 更新内容框架位置
        self.canvas.create_window(
            self.radius//2 + 4, self.radius//2 + 4,
            window=self.content_frame, anchor="nw",
            width=width - self.radius - 8,
            height=height - self.radius - 8
        )

    def _draw_rounded_rect_on_canvas(self, x1, y1, x2, y2, radius, fill_color, tag):
        """在Canvas上绘制圆角矩形"""
        # 绘制主体矩形
        self.canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2,
                                   fill=fill_color, outline="", tags=tag)
        self.canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius,
                                   fill=fill_color, outline="", tags=tag)

        # 绘制四个圆角
        self.canvas.create_oval(x1, y1, x1 + 2*radius, y1 + 2*radius,
                              fill=fill_color, outline="", tags=tag)
        self.canvas.create_oval(x2 - 2*radius, y1, x2, y1 + 2*radius,
                              fill=fill_color, outline="", tags=tag)
        self.canvas.create_oval(x1, y2 - 2*radius, x1 + 2*radius, y2,
                              fill=fill_color, outline="", tags=tag)
        self.canvas.create_oval(x2 - 2*radius, y2 - 2*radius, x2, y2,
                              fill=fill_color, outline="", tags=tag)

class FeedbackDialog:
    def __init__(self, work_summary: str = "", timeout_seconds: int = DIALOG_TIMEOUT):
        self.result_queue = queue.Queue()
        self.root = None
        self.work_summary = work_summary
        self.timeout_seconds = timeout_seconds
        self.selected_images = []  # 改为支持多张图片
        self.image_preview_frame = None
        self.text_widget = None

    def show_dialog(self):
        """在新线程中显示反馈收集对话框"""
        def run_dialog():
            self.root = tk.Tk()
            self.root.title("🎯 AI工作汇报与反馈收集 - 专业版")
            self.root.geometry("1400x1100")  # 进一步增加高度确保底部可见
            self.root.resizable(True, True)
            self.root.configure(bg=ModernTheme.BACKGROUND_PRIMARY)

            # 设置窗口图标和样式
            try:
                self.root.iconbitmap(default="")
            except:
                pass

            # 设置最小窗口大小（适应商业级布局）
            self.root.minsize(1200, 900)  # 进一步增加最小高度

            # 居中显示窗口
            self.root.eval('tk::PlaceWindow . center')

            # 设置窗口属性 - 现代化外观
            try:
                # Windows 10/11 深色标题栏
                self.root.wm_attributes('-alpha', 0.98)  # 微妙的透明度
            except:
                pass

            # 创建界面
            self.create_widgets()

            # 运行主循环
            self.root.mainloop()

        # 在新线程中运行对话框
        dialog_thread = threading.Thread(target=run_dialog)
        dialog_thread.daemon = True
        dialog_thread.start()

        # 等待结果
        try:
            result = self.result_queue.get(timeout=self.timeout_seconds)
            return result
        except queue.Empty:
            return None

    def create_widgets(self):
        """创建商业级深色主题的现代化界面组件"""
        # === 顶部标题区域 - 专业设计 ===
        header_frame = tk.Frame(self.root, bg=ModernTheme.BACKGROUND_PRIMARY)
        header_frame.pack(fill=tk.X, padx=ModernTheme.SPACING_XL, pady=(ModernTheme.SPACING_XL, ModernTheme.SPACING_LG))

        # 主标题 - 调整字体大小
        title_label = tk.Label(
            header_frame,
            text="🎯 AI工作汇报与反馈收集",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_2XL, ModernTheme.FONT_WEIGHT_BOLD),
            bg=ModernTheme.BACKGROUND_PRIMARY,
            fg=ModernTheme.TEXT_PRIMARY
        )
        title_label.pack()

        # 副标题 - 调整字体大小
        subtitle_label = tk.Label(
            header_frame,
            text="专业级反馈收集系统 • 请查看AI完成的工作内容，并提供您的宝贵意见",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_SM),
            bg=ModernTheme.BACKGROUND_PRIMARY,
            fg=ModernTheme.TEXT_SECONDARY
        )
        subtitle_label.pack(pady=(ModernTheme.SPACING_SM, 0))

        # 分隔线 - 微妙的视觉分隔
        separator = tk.Frame(self.root, height=1, bg=ModernTheme.BORDER_MUTED)
        separator.pack(fill=tk.X, padx=ModernTheme.SPACING_XL, pady=(ModernTheme.SPACING_LG, 0))

        # === 主内容区域 - 水平分割布局 ===
        content_frame = tk.Frame(self.root, bg=ModernTheme.BACKGROUND_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=ModernTheme.SPACING_XL, pady=(ModernTheme.SPACING_LG, 0))

        # 使用grid布局来精确控制宽度比例
        content_frame.grid_columnconfigure(0, weight=2)  # 左侧占40%权重
        content_frame.grid_columnconfigure(1, weight=3)  # 右侧占60%权重
        content_frame.grid_rowconfigure(0, weight=1)

        # 左侧区域 - AI工作汇报（占40%宽度）
        left_frame = tk.Frame(content_frame, bg=ModernTheme.BACKGROUND_PRIMARY)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, ModernTheme.SPACING_MD))

        # 右侧区域 - 用户反馈（占60%宽度）
        right_frame = tk.Frame(content_frame, bg=ModernTheme.BACKGROUND_PRIMARY)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(ModernTheme.SPACING_MD, 0))

        # === 左侧区域：AI工作汇报 - 高端圆角卡片设计 ===
        # 工作汇报卡片 - 奢华圆角设计
        report_card = RoundedFrame(left_frame, radius=ModernTheme.RADIUS_LG, shadow=True,
                                  bg=ModernTheme.CARD_BACKGROUND)
        report_card.pack(fill=tk.BOTH, expand=True)

        # 卡片标题区域 - 专业头部设计
        report_header = tk.Frame(report_card.content_frame, bg=ModernTheme.CARD_BACKGROUND)
        report_header.pack(fill=tk.X, padx=ModernTheme.SPACING_LG, pady=(ModernTheme.SPACING_LG, 0))

        # 标题图标和文字
        title_container = tk.Frame(report_header, bg=ModernTheme.CARD_BACKGROUND)
        title_container.pack(fill=tk.X)

        # 状态指示器 - 调整字体大小
        status_indicator = tk.Label(
            title_container,
            text="●",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_BASE),
            bg=ModernTheme.CARD_BACKGROUND,
            fg=ModernTheme.SUCCESS
        )
        status_indicator.pack(side=tk.LEFT, padx=(0, ModernTheme.SPACING_SM))

        # 主标题 - 调整字体大小
        tk.Label(
            title_container,
            text="AI工作完成汇报",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_BASE, ModernTheme.FONT_WEIGHT_BOLD),
            bg=ModernTheme.CARD_BACKGROUND,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(side=tk.LEFT, anchor="w")

        # 副标题 - 调整字体大小
        tk.Label(
            report_header,
            text="详细的工作内容和完成情况",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_XS),
            bg=ModernTheme.CARD_BACKGROUND,
            fg=ModernTheme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(ModernTheme.SPACING_XS, 0))

        # 工作汇报内容区域 - 现代化无边框设计
        report_text = ModernScrolledText(
            report_card.content_frame,
            wrap=tk.WORD,
            font=(ModernTheme.FONT_FAMILY_SECONDARY, ModernTheme.FONT_SIZE_SM),
            padx=ModernTheme.SPACING_MD,
            pady=ModernTheme.SPACING_MD,
            state=tk.DISABLED,
            cursor="arrow"
        )
        report_text.pack(fill=tk.BOTH, expand=True, padx=ModernTheme.SPACING_LG, pady=(ModernTheme.SPACING_MD, ModernTheme.SPACING_LG))

        # 使用Markdown渲染器显示工作汇报内容
        markdown_renderer = SimpleMarkdownRenderer(report_text, ModernTheme)

        # 默认内容或用户提供的内容
        content = self.work_summary or """# 📝 AI工作汇报

## ✨ 系统状态
正在准备详细的工作汇报...

### 📋 工作内容
- 本次对话中完成的工作内容将在这里显示
- 支持 **Markdown** 格式显示
- 包含 *丰富的* 文本格式

> 💡 提示：AI将在这里展示详细的工作完成情况"""

        markdown_renderer.render(content)

        # === 右侧区域：用户反馈 - 专业双区域设计 ===
        # 右侧上半部分：文字反馈 - 高端圆角卡片
        text_feedback_card = RoundedFrame(right_frame, radius=ModernTheme.RADIUS_LG, shadow=True,
                                         bg=ModernTheme.CARD_BACKGROUND)
        text_feedback_card.pack(fill=tk.BOTH, expand=True, pady=(0, ModernTheme.SPACING_MD))

        # 文字反馈标题区域 - 专业头部
        text_feedback_header = tk.Frame(text_feedback_card.content_frame, bg=ModernTheme.CARD_BACKGROUND)
        text_feedback_header.pack(fill=tk.X, padx=ModernTheme.SPACING_LG, pady=(ModernTheme.SPACING_LG, 0))

        # 标题容器
        text_title_container = tk.Frame(text_feedback_header, bg=ModernTheme.CARD_BACKGROUND)
        text_title_container.pack(fill=tk.X)

        # 反馈图标
        feedback_icon = tk.Label(
            text_title_container,
            text="💭",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_LG),
            bg=ModernTheme.CARD_BACKGROUND,
            fg=ModernTheme.TEXT_PRIMARY
        )
        feedback_icon.pack(side=tk.LEFT, padx=(0, ModernTheme.SPACING_SM))

        # 主标题
        tk.Label(
            text_title_container,
            text="您的文字反馈",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_LG, ModernTheme.FONT_WEIGHT_BOLD),
            bg=ModernTheme.CARD_BACKGROUND,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(side=tk.LEFT, anchor="w")

        # 可选标签
        tk.Label(
            text_title_container,
            text="可选",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_SM),
            bg=ModernTheme.CARD_BACKGROUND,
            fg=ModernTheme.TEXT_MUTED
        ).pack(side=tk.RIGHT)

        # 副标题
        tk.Label(
            text_feedback_header,
            text="请分享您的想法、建议或问题",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_SM),
            bg=ModernTheme.CARD_BACKGROUND,
            fg=ModernTheme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(ModernTheme.SPACING_XS, 0))

        # 前端专家级增强文本输入框
        self.text_widget = ModernScrolledText(
            text_feedback_card.content_frame,
            height=8,
            wrap=tk.WORD,
            font=(ModernTheme.FONT_FAMILY_SECONDARY, ModernTheme.FONT_SIZE_BASE),
            padx=ModernTheme.SPACING_MD,
            pady=ModernTheme.SPACING_MD
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=ModernTheme.SPACING_LG, pady=(ModernTheme.SPACING_MD, ModernTheme.SPACING_LG))
        self.text_widget.insert(tk.END, "💡 请在此输入您的反馈、建议或问题...\n\n✨ 您的意见对我们非常宝贵")
        self.text_widget.bind("<FocusIn>", self.clear_placeholder)

        # 右侧下半部分：图片反馈 - 高端圆角媒体区域
        image_feedback_card = RoundedFrame(right_frame, radius=ModernTheme.RADIUS_LG, shadow=True,
                                          bg=ModernTheme.CARD_BACKGROUND)
        image_feedback_card.pack(fill=tk.BOTH, expand=True, pady=(ModernTheme.SPACING_MD, 0))

        # 图片反馈标题区域 - 专业头部
        image_feedback_header = tk.Frame(image_feedback_card.content_frame, bg=ModernTheme.CARD_BACKGROUND)
        image_feedback_header.pack(fill=tk.X, padx=ModernTheme.SPACING_LG, pady=(ModernTheme.SPACING_LG, 0))

        # 标题容器
        image_title_container = tk.Frame(image_feedback_header, bg=ModernTheme.CARD_BACKGROUND)
        image_title_container.pack(fill=tk.X)

        # 图片图标
        image_icon = tk.Label(
            image_title_container,
            text="🖼️",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_LG),
            bg=ModernTheme.CARD_BACKGROUND,
            fg=ModernTheme.TEXT_PRIMARY
        )
        image_icon.pack(side=tk.LEFT, padx=(0, ModernTheme.SPACING_SM))

        # 主标题
        tk.Label(
            image_title_container,
            text="图片反馈",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_LG, ModernTheme.FONT_WEIGHT_BOLD),
            bg=ModernTheme.CARD_BACKGROUND,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(side=tk.LEFT, anchor="w")

        # 多张支持标签
        tk.Label(
            image_title_container,
            text="支持多张",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_SM),
            bg=ModernTheme.CARD_BACKGROUND,
            fg=ModernTheme.TEXT_MUTED
        ).pack(side=tk.RIGHT)

        # 副标题
        tk.Label(
            image_feedback_header,
            text="上传截图、照片或其他相关图片",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_SM),
            bg=ModernTheme.CARD_BACKGROUND,
            fg=ModernTheme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(ModernTheme.SPACING_XS, 0))

        # 图片操作按钮区域 - 现代化按钮组
        btn_frame = tk.Frame(image_feedback_card.content_frame, bg=ModernTheme.CARD_BACKGROUND)
        btn_frame.pack(fill=tk.X, padx=ModernTheme.SPACING_LG, pady=(ModernTheme.SPACING_MD, 0))

        # 使用功能完整的现代化按钮（临时回退到ModernButton确保功能正常）
        ModernButton(
            btn_frame,
            text="选择文件",
            icon="📁",
            command=self.select_image_file,
            style="primary",
            size="medium"
        ).pack(side=tk.LEFT, padx=(0, ModernTheme.SPACING_SM))

        ModernButton(
            btn_frame,
            text="剪贴板",
            icon="📋",
            command=self.paste_from_clipboard,
            style="secondary",
            size="medium"
        ).pack(side=tk.LEFT, padx=(0, ModernTheme.SPACING_SM))

        ModernButton(
            btn_frame,
            text="清除",
            icon="🗑️",
            command=self.clear_all_images,
            style="danger",
            size="medium"
        ).pack(side=tk.LEFT)

        # 图片预览区域 - 现代化媒体展示
        preview_container = tk.Frame(image_feedback_card.content_frame, bg=ModernTheme.CARD_BACKGROUND)
        preview_container.pack(fill=tk.BOTH, expand=True, padx=ModernTheme.SPACING_LG, pady=(ModernTheme.SPACING_MD, ModernTheme.SPACING_LG))

        # 创建现代化无边框滚动画布
        canvas = tk.Canvas(
            preview_container,
            height=160,
            bg=ModernTheme.INPUT_BACKGROUND,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,  # 完全移除边框
            highlightbackground=ModernTheme.INPUT_BACKGROUND,
            highlightcolor=ModernTheme.INPUT_BACKGROUND
        )

        # 完全隐藏滚动条 - 只保留滚动功能
        self.image_preview_frame = tk.Frame(canvas, bg=ModernTheme.INPUT_BACKGROUND)

        self.image_preview_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.image_preview_frame, anchor="nw")

        # 绑定鼠标滚轮事件实现滚动
        def _on_mousewheel(event):
            canvas.xview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", lambda e: canvas.xview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.xview_scroll(1, "units"))

        canvas.pack(side="top", fill="both", expand=True)

        # 初始化图片预览
        self.update_image_preview()

        # === 底部操作区域 - 专业级操作栏 ===
        # 分隔线
        bottom_separator = tk.Frame(self.root, height=1, bg=ModernTheme.BORDER_MUTED)
        bottom_separator.pack(fill=tk.X, padx=ModernTheme.SPACING_XL, pady=(ModernTheme.SPACING_LG, 0))

        # 底部操作按钮区域（横跨整个窗口）
        bottom_frame = tk.Frame(self.root, bg=ModernTheme.BACKGROUND_PRIMARY)
        bottom_frame.pack(fill=tk.X, padx=ModernTheme.SPACING_XL, pady=(ModernTheme.SPACING_LG, ModernTheme.SPACING_XL))

        # 左侧说明文字
        info_container = tk.Frame(bottom_frame, bg=ModernTheme.BACKGROUND_PRIMARY)
        info_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

        info_label = tk.Label(
            info_container,
            text="💡 您可以只提供文字反馈、只提供图片，或者两者都提供",
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_SM),
            fg=ModernTheme.TEXT_MUTED,
            bg=ModernTheme.BACKGROUND_PRIMARY
        )
        info_label.pack(anchor="w")

        # 右侧按钮容器
        button_container = tk.Frame(bottom_frame, bg=ModernTheme.BACKGROUND_PRIMARY)
        button_container.pack(side=tk.RIGHT)

        # 主要操作按钮 - 功能完整的现代化设计
        ModernButton(
            button_container,
            text="提交反馈",
            icon="✅",
            command=self.submit_feedback,
            style="success",
            size="large"
        ).pack(side=tk.LEFT, padx=(0, ModernTheme.SPACING_MD))

        ModernButton(
            button_container,
            text="取消",
            icon="❌",
            command=self.cancel,
            style="outline",
            size="large"
        ).pack(side=tk.LEFT)

    def clear_placeholder(self, event):
        """清除占位符文本"""
        current_text = self.text_widget.get(1.0, tk.END).strip()
        if current_text in ["请在此输入您的反馈、建议或问题...", "💡 请在此输入您的反馈、建议或问题...\n\n✨ 您的意见对我们非常宝贵"]:
            self.text_widget.delete(1.0, tk.END)

    def select_image_file(self):
        """选择图片文件（支持多选）"""
        file_types = [
            ("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
            ("PNG文件", "*.png"),
            ("JPEG文件", "*.jpg *.jpeg"),
            ("所有文件", "*.*")
        ]

        file_paths = filedialog.askopenfilenames(
            title="选择图片文件（可多选）",
            filetypes=file_types
        )

        for file_path in file_paths:
            try:
                # 读取并验证图片
                with open(file_path, 'rb') as f:
                    image_data = f.read()

                img = Image.open(io.BytesIO(image_data))
                self.selected_images.append({
                    'data': image_data,
                    'source': f'文件: {Path(file_path).name}',
                    'size': img.size,
                    'image': img
                })

            except Exception as e:
                messagebox.showerror("错误", f"无法读取图片文件 {Path(file_path).name}: {str(e)}")

        self.update_image_preview()

    def paste_from_clipboard(self):
        """从剪贴板粘贴图片"""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()

            if img:
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                image_data = buffer.getvalue()

                self.selected_images.append({
                    'data': image_data,
                    'source': '剪贴板',
                    'size': img.size,
                    'image': img
                })

                self.update_image_preview()
            else:
                messagebox.showwarning("警告", "剪贴板中没有图片数据")

        except Exception as e:
            messagebox.showerror("错误", f"无法从剪贴板获取图片: {str(e)}")

    def clear_all_images(self):
        """清除所有选择的图片"""
        self.selected_images = []
        self.update_image_preview()

    def update_image_preview(self):
        """更新图片预览显示 - 现代化深色主题"""
        # 清除现有预览
        for widget in self.image_preview_frame.winfo_children():
            widget.destroy()

        if not self.selected_images:
            # 显示现代化空状态提示
            empty_container = tk.Frame(self.image_preview_frame, bg=ModernTheme.INPUT_BACKGROUND)
            empty_container.pack(expand=True, fill=tk.BOTH)

            # 空状态图标
            empty_icon = tk.Label(
                empty_container,
                text="🖼️",
                bg=ModernTheme.INPUT_BACKGROUND,
                fg=ModernTheme.TEXT_MUTED,
                font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_3XL)
            )
            empty_icon.pack(pady=(ModernTheme.SPACING_XL, ModernTheme.SPACING_SM))

            # 空状态文字
            no_image_label = tk.Label(
                empty_container,
                text="暂无图片",
                bg=ModernTheme.INPUT_BACKGROUND,
                fg=ModernTheme.TEXT_SECONDARY,
                font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_LG, ModernTheme.FONT_WEIGHT_MEDIUM)
            )
            no_image_label.pack()

            # 提示文字
            hint_label = tk.Label(
                empty_container,
                text="点击上方按钮添加图片",
                bg=ModernTheme.INPUT_BACKGROUND,
                fg=ModernTheme.TEXT_MUTED,
                font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_SM)
            )
            hint_label.pack(pady=(ModernTheme.SPACING_XS, ModernTheme.SPACING_XL))
        else:
            # 显示所有图片预览 - 现代化卡片设计
            for i, img_info in enumerate(self.selected_images):
                try:
                    # 创建现代化图片预览卡片
                    img_container = tk.Frame(
                        self.image_preview_frame,
                        bg=ModernTheme.CARD_BACKGROUND,
                        relief=tk.FLAT,
                        bd=0,
                        highlightthickness=1,
                        highlightbackground=ModernTheme.CARD_BORDER
                    )
                    img_container.pack(side=tk.LEFT, padx=ModernTheme.SPACING_SM, pady=ModernTheme.SPACING_SM)

                    # 创建更大的缩略图
                    img_copy = img_info['image'].copy()
                    img_copy.thumbnail((140, 105), Image.Resampling.LANCZOS)

                    # 转换为tkinter可用的格式
                    photo = ImageTk.PhotoImage(img_copy)

                    # 图片标签 - 现代化样式
                    img_label = tk.Label(
                        img_container,
                        image=photo,
                        bg=ModernTheme.CARD_BACKGROUND,
                        relief=tk.FLAT,
                        bd=0
                    )
                    img_label.image = photo  # 保持引用
                    img_label.pack(padx=ModernTheme.SPACING_SM, pady=(ModernTheme.SPACING_SM, ModernTheme.SPACING_XS))

                    # 图片信息 - 现代化排版
                    info_frame = tk.Frame(img_container, bg=ModernTheme.CARD_BACKGROUND)
                    info_frame.pack(fill=tk.X, padx=ModernTheme.SPACING_SM)

                    # 文件来源
                    source_label = tk.Label(
                        info_frame,
                        text=img_info['source'],
                        font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_XS, ModernTheme.FONT_WEIGHT_MEDIUM),
                        bg=ModernTheme.CARD_BACKGROUND,
                        fg=ModernTheme.TEXT_PRIMARY,
                        justify=tk.CENTER
                    )
                    source_label.pack()

                    # 尺寸信息
                    size_label = tk.Label(
                        info_frame,
                        text=f"{img_info['size'][0]} × {img_info['size'][1]}",
                        font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_XS),
                        bg=ModernTheme.CARD_BACKGROUND,
                        fg=ModernTheme.TEXT_MUTED,
                        justify=tk.CENTER
                    )
                    size_label.pack(pady=(0, ModernTheme.SPACING_XS))

                    # 删除按钮 - 现代化圆角设计
                    del_btn = RoundedButton(
                        img_container,
                        text="移除",
                        icon="🗑️",
                        command=lambda idx=i: self.remove_image(idx),
                        style="danger",
                        size="small",
                        radius=ModernTheme.RADIUS_SM,
                        bg=ModernTheme.CARD_BACKGROUND
                    )
                    del_btn.pack(pady=(0, ModernTheme.SPACING_SM))

                except Exception as e:
                    print(f"预览更新失败: {e}")

    def remove_image(self, index):
        """删除指定索引的图片"""
        if 0 <= index < len(self.selected_images):
            self.selected_images.pop(index)
            self.update_image_preview()

    def submit_feedback(self):
        """提交反馈"""
        # 获取文本内容
        text_content = self.text_widget.get(1.0, tk.END).strip()
        if text_content == "请在此输入您的反馈、建议或问题...":
            text_content = ""

        # 检查是否有内容
        has_text = bool(text_content)
        has_images = bool(self.selected_images)

        if not has_text and not has_images:
            messagebox.showwarning("警告", "请至少提供文字反馈或图片反馈")
            return

        # 准备结果数据
        result = {
            'success': True,
            'text_feedback': text_content if has_text else None,
            'images': [img['data'] for img in self.selected_images] if has_images else None,
            'image_sources': [img['source'] for img in self.selected_images] if has_images else None,
            'has_text': has_text,
            'has_images': has_images,
            'image_count': len(self.selected_images),
            'timestamp': datetime.now().isoformat()
        }

        self.result_queue.put(result)
        self.root.destroy()

    def cancel(self):
        """取消操作"""
        self.result_queue.put({
            'success': False,
            'message': '用户取消了反馈提交'
        })
        self.root.destroy()


@mcp.tool()
def collect_feedback(work_summary: str = "", timeout_seconds: int = DIALOG_TIMEOUT) -> list:
    """
    收集用户反馈的交互式工具。AI可以汇报完成的工作，用户可以提供文字和/或图片反馈。

    Args:
        work_summary: AI完成的工作内容汇报
        timeout_seconds: 对话框超时时间（秒），默认300秒（5分钟）

    Returns:
        包含用户反馈内容的列表，可能包含文本和图片
    """
    dialog = FeedbackDialog(work_summary, timeout_seconds)
    result = dialog.show_dialog()

    if result is None:
        raise Exception(f"操作超时（{timeout_seconds}秒），请重试")

    if not result['success']:
        raise Exception(result.get('message', '用户取消了反馈提交'))

    # 构建返回内容列表
    feedback_items = []

    # 添加文字反馈
    if result['has_text']:
        from mcp.types import TextContent
        feedback_items.append(TextContent(
            type="text",
            text=f"用户文字反馈：{result['text_feedback']}\n提交时间：{result['timestamp']}"
        ))

    # 添加图片反馈
    if result['has_images']:
        for image_data, source in zip(result['images'], result['image_sources']):
            feedback_items.append(MCPImage(data=image_data, format='png'))

    return feedback_items


@mcp.tool()
def pick_image() -> MCPImage:
    """
    弹出图片选择对话框，让用户选择图片文件或从剪贴板粘贴图片。
    用户可以选择本地图片文件，或者先截图到剪贴板然后粘贴。
    """
    # 使用简化的对话框只选择图片
    dialog = FeedbackDialog()
    dialog.work_summary = "请选择一张图片"

    # 创建简化版本的图片选择对话框
    def simple_image_dialog():
        root = tk.Tk()
        root.title("选择图片")
        root.geometry("400x300")
        root.resizable(False, False)
        root.eval('tk::PlaceWindow . center')

        selected_image = {'data': None}

        def select_file():
            file_path = filedialog.askopenfilename(
                title="选择图片文件",
                filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp *.webp")]
            )
            if file_path:
                try:
                    with open(file_path, 'rb') as f:
                        selected_image['data'] = f.read()
                    root.destroy()
                except Exception as e:
                    messagebox.showerror("错误", f"无法读取图片: {e}")

        def paste_clipboard():
            try:
                from PIL import ImageGrab
                img = ImageGrab.grabclipboard()
                if img:
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    selected_image['data'] = buffer.getvalue()
                    root.destroy()
                else:
                    messagebox.showwarning("警告", "剪贴板中没有图片")
            except Exception as e:
                messagebox.showerror("错误", f"剪贴板操作失败: {e}")

        def cancel():
            root.destroy()

        # 界面
        tk.Label(root, text="请选择图片来源", font=("Arial", 14, "bold")).pack(pady=20)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="📁 选择图片文件", font=("Arial", 12),
                 width=20, height=2, command=select_file).pack(pady=10)
        tk.Button(btn_frame, text="📋 从剪贴板粘贴", font=("Arial", 12),
                 width=20, height=2, command=paste_clipboard).pack(pady=10)
        tk.Button(btn_frame, text="❌ 取消", font=("Arial", 12),
                 width=20, height=1, command=cancel).pack(pady=10)

        root.mainloop()
        return selected_image['data']

    image_data = simple_image_dialog()

    if image_data is None:
        raise Exception("未选择图片或操作被取消")

    return MCPImage(data=image_data, format='png')


@mcp.tool()
def get_image_info(image_path: str) -> str:
    """
    获取指定路径图片的信息（尺寸、格式等）

    Args:
        image_path: 图片文件路径
    """
    try:
        path = Path(image_path)
        if not path.exists():
            return f"文件不存在: {image_path}"

        with Image.open(path) as img:
            info = {
                "文件名": path.name,
                "格式": img.format,
                "尺寸": f"{img.width} x {img.height}",
                "模式": img.mode,
                "文件大小": f"{path.stat().st_size / 1024:.1f} KB"
            }

        return "\n".join([f"{k}: {v}" for k, v in info.items()])

    except Exception as e:
        return f"获取图片信息失败: {str(e)}"


if __name__ == "__main__":
    mcp.run()


def main():
    """Main entry point for the mcp-feedback-collector command."""
    mcp.run()