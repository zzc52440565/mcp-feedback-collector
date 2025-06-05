"""
对话框模块
提供各种用户交互对话框
"""

import io
import base64
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

from .theme import ModernTheme
from .components import RoundedFrame, ModernScrolledText, ModernButton, ImagePreview
from ..core.image_handler import ImageHandler
from ..config import get_settings
from ..utils.logger import get_logger
from ..utils.helpers import center_window, safe_thread_run


class FeedbackDialog:
    """反馈收集对话框"""
    
    def __init__(self, work_summary: str = "", timeout_seconds: int = 300,
                 result_queue: Optional[queue.Queue] = None):
        """
        初始化反馈对话框
        
        Args:
            work_summary: AI工作汇报内容
            timeout_seconds: 超时时间
            result_queue: 结果队列
        """
        self.work_summary = work_summary
        self.timeout_seconds = timeout_seconds
        self.result_queue = result_queue or queue.Queue()
        
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.image_handler = ImageHandler()
        
        # UI组件
        self.root: Optional[tk.Tk] = None
        self.text_widget: Optional[ModernScrolledText] = None
        self.image_preview_frame: Optional[tk.Frame] = None
        
        # 数据
        self.selected_images: List[Dict[str, Any]] = []
        self.timeout_timer: Optional[threading.Timer] = None
    
    def show_dialog(self) -> Optional[Dict[str, Any]]:
        """显示对话框并返回结果"""
        try:
            self._create_window()
            self._create_widgets()
            self._setup_timeout()
            
            # 运行主循环
            self.root.mainloop()
            
            # 获取结果
            if not self.result_queue.empty():
                return self.result_queue.get_nowait()
            return None
            
        except Exception as e:
            self.logger.error(f"显示对话框失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            self._cleanup()
    
    def _create_window(self):
        """创建主窗口"""
        self.root = tk.Tk()
        self.root.title("🎯 AI工作汇报与反馈收集 - 专业版")
        
        # 设置窗口大小和位置
        width = self.settings.ui.window_width
        height = self.settings.ui.window_height
        center_window(self.root, width, height)
        
        # 设置窗口属性
        self.root.resizable(True, True)
        self.root.configure(bg=ModernTheme.BACKGROUND_PRIMARY)
        self.root.minsize(self.settings.ui.min_width, self.settings.ui.min_height)
        
        # 设置窗口透明度
        try:
            self.root.wm_attributes('-alpha', self.settings.ui.window_alpha)
        except:
            pass
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主容器
        main_container = tk.Frame(self.root, bg=ModernTheme.BACKGROUND_PRIMARY)
        main_container.pack(fill=tk.BOTH, expand=True, padx=ModernTheme.SPACING_XL, 
                           pady=ModernTheme.SPACING_XL)
        
        # 创建标题区域
        self._create_header(main_container)
        
        # 创建内容区域
        self._create_content_area(main_container)
        
        # 创建按钮区域
        self._create_button_area(main_container)
    
    def _create_header(self, parent):
        """创建标题区域"""
        header_frame = tk.Frame(parent, bg=ModernTheme.BACKGROUND_PRIMARY)
        header_frame.pack(fill=tk.X, pady=(0, ModernTheme.SPACING_LG))
        
        # 主标题
        title_label = tk.Label(
            header_frame,
            text="🎯 AI工作汇报与反馈收集",
            **ModernTheme.get_label_style("title"),
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_2XL, ModernTheme.FONT_WEIGHT_BOLD)
        )
        title_label.pack()
        
        # 副标题
        subtitle_label = tk.Label(
            header_frame,
            text="专业级反馈收集系统 • 请查看AI完成的工作内容，并提供您的宝贵意见",
            **ModernTheme.get_label_style("secondary"),
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_SM)
        )
        subtitle_label.pack(pady=(ModernTheme.SPACING_SM, 0))
    
    def _create_content_area(self, parent):
        """创建内容区域"""
        content_frame = tk.Frame(parent, bg=ModernTheme.BACKGROUND_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, ModernTheme.SPACING_LG))
        
        # 配置网格权重
        content_frame.grid_columnconfigure(0, weight=2)  # 左侧40%
        content_frame.grid_columnconfigure(1, weight=3)  # 右侧60%
        content_frame.grid_rowconfigure(0, weight=1)
        
        # 左侧：AI工作汇报
        self._create_work_report_area(content_frame)
        
        # 右侧：用户反馈
        self._create_feedback_area(content_frame)
    
    def _create_work_report_area(self, parent):
        """创建工作汇报区域"""
        left_frame = tk.Frame(parent, bg=ModernTheme.BACKGROUND_PRIMARY)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, ModernTheme.SPACING_MD))
        
        # 工作汇报卡片
        report_card = RoundedFrame(
            left_frame, 
            radius=ModernTheme.RADIUS_LG, 
            shadow=self.settings.ui.enable_shadows,
            bg=ModernTheme.CARD_BACKGROUND
        )
        report_card.pack(fill=tk.BOTH, expand=True)
        
        # 卡片标题
        title_label = tk.Label(
            report_card.content_frame,
            text="📋 AI工作汇报",
            **ModernTheme.get_label_style("title"),
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_LG, ModernTheme.FONT_WEIGHT_BOLD)
        )
        title_label.pack(anchor="w", padx=ModernTheme.SPACING_LG, pady=(ModernTheme.SPACING_LG, ModernTheme.SPACING_SM))
        
        # 工作内容显示
        work_text = ModernScrolledText(
            report_card.content_frame,
            height=15,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        work_text.pack(fill=tk.BOTH, expand=True, padx=ModernTheme.SPACING_LG, 
                      pady=(0, ModernTheme.SPACING_LG))
        
        # 插入工作汇报内容
        work_text.configure(state=tk.NORMAL)
        if self.work_summary:
            work_text.insert(tk.END, self.work_summary)
        else:
            work_text.insert(tk.END, "AI暂未提供工作汇报内容。")
        work_text.configure(state=tk.DISABLED)
    
    def _create_feedback_area(self, parent):
        """创建反馈区域"""
        right_frame = tk.Frame(parent, bg=ModernTheme.BACKGROUND_PRIMARY)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(ModernTheme.SPACING_MD, 0))
        
        # 配置网格权重
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # 文字反馈区域
        self._create_text_feedback_area(right_frame)
        
        # 图片反馈区域
        self._create_image_feedback_area(right_frame)
    
    def _create_text_feedback_area(self, parent):
        """创建文字反馈区域"""
        text_card = RoundedFrame(
            parent,
            radius=ModernTheme.RADIUS_LG,
            shadow=self.settings.ui.enable_shadows,
            bg=ModernTheme.CARD_BACKGROUND
        )
        text_card.grid(row=0, column=0, sticky="nsew", pady=(0, ModernTheme.SPACING_MD))
        
        # 标题
        title_label = tk.Label(
            text_card.content_frame,
            text="💬 文字反馈",
            **ModernTheme.get_label_style("title"),
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_LG, ModernTheme.FONT_WEIGHT_BOLD)
        )
        title_label.pack(anchor="w", padx=ModernTheme.SPACING_LG, pady=(ModernTheme.SPACING_LG, ModernTheme.SPACING_SM))
        
        # 文本输入框
        self.text_widget = ModernScrolledText(
            text_card.content_frame,
            height=8,
            wrap=tk.WORD,
            placeholder="💡 请在此输入您的反馈、建议或问题...\n\n✨ 您的意见对我们非常宝贵"
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=ModernTheme.SPACING_LG, 
                             pady=(ModernTheme.SPACING_MD, ModernTheme.SPACING_LG))
    
    def _create_image_feedback_area(self, parent):
        """创建图片反馈区域"""
        image_card = RoundedFrame(
            parent,
            radius=ModernTheme.RADIUS_LG,
            shadow=self.settings.ui.enable_shadows,
            bg=ModernTheme.CARD_BACKGROUND
        )
        image_card.grid(row=1, column=0, sticky="nsew")
        
        # 标题和按钮区域
        header_frame = tk.Frame(image_card.content_frame, bg=ModernTheme.CARD_BACKGROUND)
        header_frame.pack(fill=tk.X, padx=ModernTheme.SPACING_LG, pady=(ModernTheme.SPACING_LG, ModernTheme.SPACING_SM))
        
        # 标题
        title_label = tk.Label(
            header_frame,
            text="📷 图片反馈",
            **ModernTheme.get_label_style("title"),
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_LG, ModernTheme.FONT_WEIGHT_BOLD)
        )
        title_label.pack(side=tk.LEFT)
        
        # 按钮区域
        button_frame = tk.Frame(header_frame, bg=ModernTheme.CARD_BACKGROUND)
        button_frame.pack(side=tk.RIGHT)
        
        # 添加图片按钮
        add_file_btn = ModernButton(
            button_frame,
            text="📁 选择文件",
            button_type="primary",
            command=self._add_image_from_file
        )
        add_file_btn.pack(side=tk.LEFT, padx=(0, ModernTheme.SPACING_SM))
        
        add_clipboard_btn = ModernButton(
            button_frame,
            text="📋 粘贴图片",
            button_type="secondary",
            command=self._add_image_from_clipboard
        )
        add_clipboard_btn.pack(side=tk.LEFT, padx=(0, ModernTheme.SPACING_SM))
        
        clear_btn = ModernButton(
            button_frame,
            text="🗑️ 清空",
            button_type="danger",
            command=self._clear_all_images
        )
        clear_btn.pack(side=tk.LEFT)
        
        # 图片预览区域
        self._create_image_preview_area(image_card.content_frame)

    def _create_image_preview_area(self, parent):
        """创建图片预览区域"""
        # 预览容器
        preview_container = tk.Frame(parent, bg=ModernTheme.CARD_BACKGROUND)
        preview_container.pack(fill=tk.BOTH, expand=True, padx=ModernTheme.SPACING_LG,
                              pady=(0, ModernTheme.SPACING_LG))

        # 滚动区域
        canvas = tk.Canvas(
            preview_container,
            bg=ModernTheme.INPUT_BACKGROUND,
            highlightthickness=0,
            relief='flat',
            height=120
        )
        scrollbar = ttk.Scrollbar(preview_container, orient="horizontal", command=canvas.xview)
        self.image_preview_frame = tk.Frame(canvas, bg=ModernTheme.INPUT_BACKGROUND)

        self.image_preview_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.image_preview_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)

        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")

        # 提示文字
        hint_label = tk.Label(
            self.image_preview_frame,
            text="📸 暂无图片，点击上方按钮添加图片",
            **ModernTheme.get_label_style("muted"),
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_SM)
        )
        hint_label.pack(expand=True, pady=ModernTheme.SPACING_XL)

    def _create_button_area(self, parent):
        """创建按钮区域"""
        button_frame = tk.Frame(parent, bg=ModernTheme.BACKGROUND_PRIMARY)
        button_frame.pack(fill=tk.X, pady=(ModernTheme.SPACING_LG, 0))

        # 右侧按钮组
        right_buttons = tk.Frame(button_frame, bg=ModernTheme.BACKGROUND_PRIMARY)
        right_buttons.pack(side=tk.RIGHT)

        # 取消按钮
        cancel_btn = ModernButton(
            right_buttons,
            text="❌ 取消",
            button_type="secondary",
            command=self._cancel_feedback,
            width=12
        )
        cancel_btn.pack(side=tk.LEFT, padx=(0, ModernTheme.SPACING_MD))

        # 提交按钮
        submit_btn = ModernButton(
            right_buttons,
            text="✅ 提交反馈",
            button_type="success",
            command=self._submit_feedback,
            width=15
        )
        submit_btn.pack(side=tk.LEFT)

        # 左侧状态信息
        status_frame = tk.Frame(button_frame, bg=ModernTheme.BACKGROUND_PRIMARY)
        status_frame.pack(side=tk.LEFT)

        timeout_label = tk.Label(
            status_frame,
            text=f"⏱️ 超时时间: {self.timeout_seconds}秒",
            **ModernTheme.get_label_style("muted"),
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_SM)
        )
        timeout_label.pack(side=tk.LEFT)

    def _setup_timeout(self):
        """设置超时定时器"""
        if self.timeout_seconds > 0:
            self.timeout_timer = threading.Timer(
                self.timeout_seconds,
                self._on_timeout
            )
            self.timeout_timer.start()

    def _on_timeout(self):
        """超时处理"""
        self.logger.warning("反馈收集超时")
        if self.root:
            self.root.after(0, lambda: self._close_with_result({
                "success": False,
                "message": f"操作超时（{self.timeout_seconds}秒）"
            }))

    def _on_window_close(self):
        """窗口关闭事件"""
        self._close_with_result({
            "success": False,
            "message": "用户关闭了对话框"
        })

    def _cancel_feedback(self):
        """取消反馈"""
        self._close_with_result({
            "success": False,
            "message": "用户取消了反馈提交"
        })

    def _submit_feedback(self):
        """提交反馈"""
        try:
            # 获取文字反馈
            text_feedback = self.text_widget.get_text() if self.text_widget else ""

            # 检查是否有内容
            has_text = bool(text_feedback.strip())
            has_images = bool(self.selected_images)

            if not has_text and not has_images:
                messagebox.showwarning("警告", "请至少提供文字反馈或图片反馈")
                return

            # 准备结果数据
            result = {
                'success': True,
                'text_feedback': text_feedback if has_text else None,
                'images': [img['data'] for img in self.selected_images] if has_images else None,
                'image_sources': [img['source'] for img in self.selected_images] if has_images else None,
                'has_text': has_text,
                'has_images': has_images,
                'image_count': len(self.selected_images),
                'timestamp': datetime.now().isoformat()
            }

            self.logger.info(f"提交反馈: 文字={has_text}, 图片={len(self.selected_images)}张")
            self._close_with_result(result)

        except Exception as e:
            self.logger.error(f"提交反馈失败: {e}")
            messagebox.showerror("错误", f"提交反馈失败: {str(e)}")

    def _close_with_result(self, result: Dict[str, Any]):
        """关闭对话框并返回结果"""
        try:
            self.result_queue.put(result)
        except:
            pass

        if self.root:
            self.root.quit()
            self.root.destroy()

    def _cleanup(self):
        """清理资源"""
        try:
            if self.timeout_timer:
                self.timeout_timer.cancel()

            if self.image_handler:
                self.image_handler.clear_cache()

        except Exception as e:
            self.logger.warning(f"清理资源时出错: {e}")

    def _add_image_from_file(self):
        """从文件添加图片"""
        try:
            file_types = [
                ("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("所有文件", "*.*")
            ]

            file_paths = filedialog.askopenfilenames(
                title="选择图片文件",
                filetypes=file_types
            )

            if file_paths:
                for file_path in file_paths:
                    self._load_image_file(file_path)

        except Exception as e:
            self.logger.error(f"选择图片文件失败: {e}")
            messagebox.showerror("错误", f"选择图片文件失败: {str(e)}")

    def _add_image_from_clipboard(self):
        """从剪贴板添加图片"""
        try:
            result = self.image_handler.load_image_from_clipboard()
            if result:
                image_data, source = result
                self._add_image_to_preview(image_data, source)
                self.logger.info("成功从剪贴板添加图片")
            else:
                messagebox.showinfo("提示", "剪贴板中没有图片数据")

        except Exception as e:
            self.logger.error(f"从剪贴板添加图片失败: {e}")
            messagebox.showerror("错误", f"从剪贴板添加图片失败: {str(e)}")

    def _load_image_file(self, file_path: str):
        """加载图片文件"""
        try:
            result = self.image_handler.load_image_from_file(file_path)
            if result:
                image_data, source = result
                self._add_image_to_preview(image_data, source)
                self.logger.info(f"成功加载图片文件: {file_path}")
            else:
                messagebox.showerror("错误", f"无法加载图片文件: {file_path}")

        except Exception as e:
            self.logger.error(f"加载图片文件失败: {e}")
            messagebox.showerror("错误", f"加载图片文件失败: {str(e)}")

    def _add_image_to_preview(self, image_data: bytes, source: str):
        """添加图片到预览区域"""
        try:
            # 检查图片数量限制
            if len(self.selected_images) >= 10:
                messagebox.showwarning("警告", "最多只能添加10张图片")
                return

            # 创建缩略图
            thumbnail = self.image_handler.create_thumbnail(image_data)
            if not thumbnail:
                messagebox.showerror("错误", "无法创建图片缩略图")
                return

            # 添加到列表
            image_info = {
                'data': image_data,
                'source': source,
                'thumbnail': thumbnail
            }
            self.selected_images.append(image_info)

            # 更新预览界面
            self._update_image_preview()

        except Exception as e:
            self.logger.error(f"添加图片预览失败: {e}")
            messagebox.showerror("错误", f"添加图片预览失败: {str(e)}")

    def _update_image_preview(self):
        """更新图片预览界面"""
        try:
            # 清空现有预览
            for widget in self.image_preview_frame.winfo_children():
                widget.destroy()

            if not self.selected_images:
                # 显示提示文字
                hint_label = tk.Label(
                    self.image_preview_frame,
                    text="📸 暂无图片，点击上方按钮添加图片",
                    **ModernTheme.get_label_style("muted"),
                    font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_SM)
                )
                hint_label.pack(expand=True, pady=ModernTheme.SPACING_XL)
            else:
                # 显示图片预览
                for i, image_info in enumerate(self.selected_images):
                    self._create_image_preview_item(i, image_info)

        except Exception as e:
            self.logger.error(f"更新图片预览失败: {e}")

    def _create_image_preview_item(self, index: int, image_info: Dict[str, Any]):
        """创建单个图片预览项"""
        try:
            # 预览容器
            preview_frame = tk.Frame(self.image_preview_frame, bg=ModernTheme.INPUT_BACKGROUND)
            preview_frame.pack(side=tk.LEFT, padx=ModernTheme.SPACING_SM, pady=ModernTheme.SPACING_SM)

            # 图片显示
            image_label = tk.Label(
                preview_frame,
                image=image_info['thumbnail'],
                bg=ModernTheme.CARD_BACKGROUND,
                relief='solid',
                borderwidth=1
            )
            image_label.pack()

            # 删除按钮
            remove_btn = ModernButton(
                preview_frame,
                text="×",
                button_type="danger",
                font=(ModernTheme.FONT_FAMILY_PRIMARY, 10, "bold"),
                width=2,
                height=1,
                command=lambda idx=index: self._remove_image(idx)
            )
            remove_btn.pack(pady=(2, 0))

            # 来源标签
            source_text = image_info['source']
            if len(source_text) > 15:
                source_text = source_text[:12] + "..."

            source_label = tk.Label(
                preview_frame,
                text=source_text,
                **ModernTheme.get_label_style("muted"),
                font=(ModernTheme.FONT_FAMILY_PRIMARY, 8)
            )
            source_label.pack(pady=(2, 0))

        except Exception as e:
            self.logger.error(f"创建图片预览项失败: {e}")

    def _remove_image(self, index: int):
        """删除指定索引的图片"""
        try:
            if 0 <= index < len(self.selected_images):
                removed = self.selected_images.pop(index)
                self.logger.info(f"删除图片: {removed['source']}")
                self._update_image_preview()

        except Exception as e:
            self.logger.error(f"删除图片失败: {e}")

    def _clear_all_images(self):
        """清空所有图片"""
        try:
            if self.selected_images:
                if messagebox.askyesno("确认", "确定要清空所有图片吗？"):
                    self.selected_images.clear()
                    self._update_image_preview()
                    self.logger.info("清空所有图片")

        except Exception as e:
            self.logger.error(f"清空图片失败: {e}")


class ImagePickerDialog:
    """简化的图片选择对话框"""

    def __init__(self, result_queue: Optional[queue.Queue] = None):
        self.result_queue = result_queue or queue.Queue()
        self.logger = get_logger(__name__)
        self.image_handler = ImageHandler()
        self.root: Optional[tk.Tk] = None

    def show_dialog(self) -> Optional[Dict[str, Any]]:
        """显示图片选择对话框"""
        try:
            self._create_simple_dialog()
            self.root.mainloop()

            if not self.result_queue.empty():
                return self.result_queue.get_nowait()
            return None

        except Exception as e:
            self.logger.error(f"显示图片选择对话框失败: {e}")
            return {"success": False, "message": str(e)}

    def _create_simple_dialog(self):
        """创建简单的图片选择对话框"""
        self.root = tk.Tk()
        self.root.title("选择图片")
        self.root.geometry("400x300")
        self.root.configure(bg=ModernTheme.BACKGROUND_PRIMARY)
        center_window(self.root, 400, 300)

        # 标题
        title_label = tk.Label(
            self.root,
            text="请选择图片来源",
            **ModernTheme.get_label_style("title"),
            font=(ModernTheme.FONT_FAMILY_PRIMARY, ModernTheme.FONT_SIZE_LG, ModernTheme.FONT_WEIGHT_BOLD)
        )
        title_label.pack(pady=ModernTheme.SPACING_XL)

        # 按钮区域
        button_frame = tk.Frame(self.root, bg=ModernTheme.BACKGROUND_PRIMARY)
        button_frame.pack(pady=ModernTheme.SPACING_XL)

        # 选择文件按钮
        file_btn = ModernButton(
            button_frame,
            text="📁 选择图片文件",
            button_type="primary",
            width=20,
            height=2,
            command=self._select_file
        )
        file_btn.pack(pady=ModernTheme.SPACING_MD)

        # 剪贴板按钮
        clipboard_btn = ModernButton(
            button_frame,
            text="📋 从剪贴板粘贴",
            button_type="secondary",
            width=20,
            height=2,
            command=self._paste_clipboard
        )
        clipboard_btn.pack(pady=ModernTheme.SPACING_MD)

        # 取消按钮
        cancel_btn = ModernButton(
            button_frame,
            text="❌ 取消",
            button_type="danger",
            width=20,
            height=1,
            command=self._cancel
        )
        cancel_btn.pack(pady=ModernTheme.SPACING_MD)

    def _select_file(self):
        """选择文件"""
        try:
            file_types = [
                ("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("所有文件", "*.*")
            ]

            file_path = filedialog.askopenfilename(
                title="选择图片文件",
                filetypes=file_types
            )

            if file_path:
                result = self.image_handler.load_image_from_file(file_path)
                if result:
                    image_data, source = result
                    self._close_with_result({
                        "success": True,
                        "image_data": image_data,
                        "source": source
                    })
                else:
                    messagebox.showerror("错误", "无法加载选择的图片文件")

        except Exception as e:
            self.logger.error(f"选择图片文件失败: {e}")
            messagebox.showerror("错误", f"选择图片文件失败: {str(e)}")

    def _paste_clipboard(self):
        """从剪贴板粘贴"""
        try:
            result = self.image_handler.load_image_from_clipboard()
            if result:
                image_data, source = result
                self._close_with_result({
                    "success": True,
                    "image_data": image_data,
                    "source": source
                })
            else:
                messagebox.showinfo("提示", "剪贴板中没有图片数据")

        except Exception as e:
            self.logger.error(f"从剪贴板粘贴失败: {e}")
            messagebox.showerror("错误", f"从剪贴板粘贴失败: {str(e)}")

    def _cancel(self):
        """取消选择"""
        self._close_with_result({
            "success": False,
            "message": "用户取消了图片选择"
        })

    def _close_with_result(self, result: Dict[str, Any]):
        """关闭对话框并返回结果"""
        try:
            self.result_queue.put(result)
        except:
            pass

        if self.root:
            self.root.quit()
            self.root.destroy()
