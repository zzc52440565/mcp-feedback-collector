"""
现代化主题配置
定义应用程序的视觉样式和主题
"""

from typing import Dict, Any


class ModernTheme:
    """现代化深色主题配置"""
    
    # === 颜色配置 ===
    # 主要背景色
    BACKGROUND_PRIMARY = "#1a1a1a"      # 深灰色主背景
    BACKGROUND_SECONDARY = "#2d2d2d"    # 次要背景
    CARD_BACKGROUND = "#2a2a2a"         # 卡片背景
    
    # 文字颜色
    TEXT_PRIMARY = "#ffffff"            # 主要文字
    TEXT_SECONDARY = "#b0b0b0"          # 次要文字
    TEXT_MUTED = "#808080"              # 弱化文字
    TEXT_ACCENT = "#4a9eff"             # 强调文字
    
    # 按钮颜色
    BUTTON_PRIMARY = "#4a9eff"          # 主要按钮
    BUTTON_PRIMARY_HOVER = "#3d8bef"    # 主要按钮悬停
    BUTTON_SECONDARY = "#6c757d"        # 次要按钮
    BUTTON_SECONDARY_HOVER = "#5a6268"  # 次要按钮悬停
    BUTTON_SUCCESS = "#28a745"          # 成功按钮
    BUTTON_SUCCESS_HOVER = "#218838"    # 成功按钮悬停
    BUTTON_DANGER = "#dc3545"           # 危险按钮
    BUTTON_DANGER_HOVER = "#c82333"     # 危险按钮悬停
    
    # 输入框颜色
    INPUT_BACKGROUND = "#3a3a3a"        # 输入框背景
    INPUT_BORDER = "#555555"            # 输入框边框
    INPUT_FOCUS = "#4a9eff"             # 输入框焦点
    
    # 边框和分割线
    BORDER_COLOR = "#404040"            # 边框颜色
    DIVIDER_COLOR = "#333333"           # 分割线颜色
    
    # 状态颜色
    SUCCESS_COLOR = "#28a745"           # 成功状态
    WARNING_COLOR = "#ffc107"           # 警告状态
    ERROR_COLOR = "#dc3545"             # 错误状态
    INFO_COLOR = "#17a2b8"              # 信息状态
    
    # === 字体配置 ===
    FONT_FAMILY_PRIMARY = "Microsoft YaHei UI"     # 主要字体
    FONT_FAMILY_SECONDARY = "Consolas"             # 次要字体（代码）
    FONT_FAMILY_MONOSPACE = "Courier New"          # 等宽字体
    
    # 字体大小
    FONT_SIZE_XS = 10       # 极小
    FONT_SIZE_SM = 11       # 小
    FONT_SIZE_BASE = 12     # 基础
    FONT_SIZE_LG = 14       # 大
    FONT_SIZE_XL = 16       # 特大
    FONT_SIZE_2XL = 20      # 超大
    FONT_SIZE_3XL = 24      # 巨大
    
    # 字体粗细
    FONT_WEIGHT_NORMAL = "normal"
    FONT_WEIGHT_BOLD = "bold"
    
    # === 间距配置 ===
    SPACING_XS = 4          # 极小间距
    SPACING_SM = 8          # 小间距
    SPACING_MD = 12         # 中等间距
    SPACING_LG = 16         # 大间距
    SPACING_XL = 20         # 特大间距
    SPACING_2XL = 24        # 超大间距
    SPACING_3XL = 32        # 巨大间距
    
    # === 圆角配置 ===
    RADIUS_SM = 4           # 小圆角
    RADIUS_MD = 8           # 中等圆角
    RADIUS_LG = 12          # 大圆角
    RADIUS_XL = 16          # 特大圆角
    RADIUS_FULL = 9999      # 完全圆角
    
    # === 阴影配置 ===
    SHADOW_SM = "2 2 4 #000000"        # 小阴影
    SHADOW_MD = "4 4 8 #000000"        # 中等阴影
    SHADOW_LG = "8 8 16 #000000"       # 大阴影
    
    # === 动画配置 ===
    ANIMATION_DURATION_FAST = 150      # 快速动画（毫秒）
    ANIMATION_DURATION_NORMAL = 300    # 正常动画
    ANIMATION_DURATION_SLOW = 500      # 慢速动画
    
    # === 组件特定样式 ===
    @classmethod
    def get_button_style(cls, button_type: str = "primary") -> Dict[str, Any]:
        """获取按钮样式"""
        base_style = {
            "font": (cls.FONT_FAMILY_PRIMARY, cls.FONT_SIZE_BASE, cls.FONT_WEIGHT_NORMAL),
            "relief": "flat",
            "borderwidth": 0,
            "cursor": "hand2",
            "padx": cls.SPACING_LG,
            "pady": cls.SPACING_SM,
        }
        
        if button_type == "primary":
            base_style.update({
                "bg": cls.BUTTON_PRIMARY,
                "fg": cls.TEXT_PRIMARY,
                "activebackground": cls.BUTTON_PRIMARY_HOVER,
                "activeforeground": cls.TEXT_PRIMARY,
            })
        elif button_type == "secondary":
            base_style.update({
                "bg": cls.BUTTON_SECONDARY,
                "fg": cls.TEXT_PRIMARY,
                "activebackground": cls.BUTTON_SECONDARY_HOVER,
                "activeforeground": cls.TEXT_PRIMARY,
            })
        elif button_type == "success":
            base_style.update({
                "bg": cls.BUTTON_SUCCESS,
                "fg": cls.TEXT_PRIMARY,
                "activebackground": cls.BUTTON_SUCCESS_HOVER,
                "activeforeground": cls.TEXT_PRIMARY,
            })
        elif button_type == "danger":
            base_style.update({
                "bg": cls.BUTTON_DANGER,
                "fg": cls.TEXT_PRIMARY,
                "activebackground": cls.BUTTON_DANGER_HOVER,
                "activeforeground": cls.TEXT_PRIMARY,
            })
        
        return base_style
    
    @classmethod
    def get_label_style(cls, label_type: str = "primary") -> Dict[str, Any]:
        """获取标签样式"""
        base_style = {
            "bg": cls.BACKGROUND_PRIMARY,
            "font": (cls.FONT_FAMILY_PRIMARY, cls.FONT_SIZE_BASE, cls.FONT_WEIGHT_NORMAL),
        }
        
        if label_type == "primary":
            base_style["fg"] = cls.TEXT_PRIMARY
        elif label_type == "secondary":
            base_style["fg"] = cls.TEXT_SECONDARY
        elif label_type == "muted":
            base_style["fg"] = cls.TEXT_MUTED
        elif label_type == "accent":
            base_style["fg"] = cls.TEXT_ACCENT
        elif label_type == "title":
            base_style.update({
                "fg": cls.TEXT_PRIMARY,
                "font": (cls.FONT_FAMILY_PRIMARY, cls.FONT_SIZE_XL, cls.FONT_WEIGHT_BOLD),
            })
        elif label_type == "subtitle":
            base_style.update({
                "fg": cls.TEXT_SECONDARY,
                "font": (cls.FONT_FAMILY_PRIMARY, cls.FONT_SIZE_LG, cls.FONT_WEIGHT_NORMAL),
            })
        
        return base_style
    
    @classmethod
    def get_text_widget_style(cls) -> Dict[str, Any]:
        """获取文本组件样式"""
        return {
            "bg": cls.INPUT_BACKGROUND,
            "fg": cls.TEXT_PRIMARY,
            "insertbackground": cls.TEXT_PRIMARY,
            "selectbackground": cls.BUTTON_PRIMARY,
            "selectforeground": cls.TEXT_PRIMARY,
            "relief": "flat",
            "borderwidth": 1,
            "highlightthickness": 2,
            "highlightcolor": cls.INPUT_FOCUS,
            "highlightbackground": cls.INPUT_BORDER,
            "font": (cls.FONT_FAMILY_SECONDARY, cls.FONT_SIZE_BASE),
        }
    
    @classmethod
    def get_frame_style(cls, frame_type: str = "default") -> Dict[str, Any]:
        """获取框架样式"""
        base_style = {
            "relief": "flat",
            "borderwidth": 0,
        }
        
        if frame_type == "default":
            base_style["bg"] = cls.BACKGROUND_PRIMARY
        elif frame_type == "card":
            base_style["bg"] = cls.CARD_BACKGROUND
        elif frame_type == "secondary":
            base_style["bg"] = cls.BACKGROUND_SECONDARY
        
        return base_style
