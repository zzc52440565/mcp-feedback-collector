"""
反馈收集核心模块
提供反馈收集的核心业务逻辑
"""

import queue
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from ..config import get_settings
from ..utils.logger import get_logger


@dataclass
class FeedbackResult:
    """反馈结果数据类"""
    success: bool
    text_feedback: Optional[str] = None
    images: Optional[List[bytes]] = None
    image_sources: Optional[List[str]] = None
    has_text: bool = False
    has_images: bool = False
    image_count: int = 0
    timestamp: str = ""
    message: str = ""


class FeedbackCollector:
    """反馈收集器核心类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self._result_queue = queue.Queue()
        self._dialog_thread: Optional[threading.Thread] = None
        self._dialog_instance = None
    
    def collect_feedback(self, work_summary: str = "", 
                        timeout_seconds: Optional[int] = None) -> FeedbackResult:
        """
        收集用户反馈
        
        Args:
            work_summary: AI工作汇报内容
            timeout_seconds: 超时时间（秒）
            
        Returns:
            反馈结果
        """
        if timeout_seconds is None:
            timeout_seconds = self.settings.timeout.default_dialog_timeout
        
        self.logger.info(f"开始收集反馈，超时时间: {timeout_seconds}秒")
        
        try:
            # 导入对话框类（避免循环导入）
            from ..ui.dialogs import FeedbackDialog
            
            # 创建对话框实例
            dialog = FeedbackDialog(
                work_summary=work_summary,
                timeout_seconds=timeout_seconds,
                result_queue=self._result_queue
            )
            
            # 在新线程中显示对话框
            self._dialog_thread = threading.Thread(
                target=dialog.show_dialog,
                daemon=True
            )
            self._dialog_thread.start()
            
            # 等待结果
            try:
                result_data = self._result_queue.get(timeout=timeout_seconds)
                self.logger.info("成功收集到用户反馈")
                return self._process_result(result_data)
                
            except queue.Empty:
                self.logger.warning(f"反馈收集超时（{timeout_seconds}秒）")
                return FeedbackResult(
                    success=False,
                    message=f"操作超时（{timeout_seconds}秒），请重试"
                )
                
        except Exception as e:
            self.logger.error(f"反馈收集失败: {e}")
            return FeedbackResult(
                success=False,
                message=f"反馈收集失败: {str(e)}"
            )
        finally:
            # 清理资源
            self._cleanup()
    
    def pick_image(self) -> Optional[bytes]:
        """
        选择单张图片
        
        Returns:
            图片数据或None
        """
        self.logger.info("开始图片选择")
        
        try:
            # 导入图片选择对话框
            from ..ui.dialogs import ImagePickerDialog
            
            dialog = ImagePickerDialog(result_queue=self._result_queue)
            
            # 在新线程中显示对话框
            self._dialog_thread = threading.Thread(
                target=dialog.show_dialog,
                daemon=True
            )
            self._dialog_thread.start()
            
            # 等待结果
            try:
                result = self._result_queue.get(timeout=self.settings.timeout.default_dialog_timeout)
                if result and result.get('success') and result.get('image_data'):
                    self.logger.info("成功选择图片")
                    return result['image_data']
                else:
                    self.logger.info("用户取消了图片选择")
                    return None
                    
            except queue.Empty:
                self.logger.warning("图片选择超时")
                return None
                
        except Exception as e:
            self.logger.error(f"图片选择失败: {e}")
            return None
        finally:
            self._cleanup()
    
    def validate_feedback(self, text_feedback: str, images: List[bytes]) -> Tuple[bool, str]:
        """
        验证反馈内容
        
        Args:
            text_feedback: 文字反馈
            images: 图片列表
            
        Returns:
            (是否有效, 错误信息)
        """
        has_text = bool(text_feedback and text_feedback.strip())
        has_images = bool(images)
        
        if not has_text and not has_images:
            return False, "请至少提供文字反馈或图片反馈"
        
        # 验证图片数量
        if len(images) > 10:  # 限制最多10张图片
            return False, "图片数量不能超过10张"
        
        # 验证文字长度
        if has_text and len(text_feedback) > 10000:  # 限制文字长度
            return False, "文字反馈长度不能超过10000字符"
        
        return True, ""
    
    def _process_result(self, result_data: Dict[str, Any]) -> FeedbackResult:
        """
        处理反馈结果
        
        Args:
            result_data: 原始结果数据
            
        Returns:
            处理后的反馈结果
        """
        if not result_data.get('success', False):
            return FeedbackResult(
                success=False,
                message=result_data.get('message', '用户取消了反馈提交')
            )
        
        # 提取数据
        text_feedback = result_data.get('text_feedback', '')
        images = result_data.get('images', [])
        image_sources = result_data.get('image_sources', [])
        
        # 验证反馈内容
        is_valid, error_msg = self.validate_feedback(text_feedback, images)
        if not is_valid:
            return FeedbackResult(
                success=False,
                message=error_msg
            )
        
        # 创建结果
        return FeedbackResult(
            success=True,
            text_feedback=text_feedback if text_feedback.strip() else None,
            images=images if images else None,
            image_sources=image_sources if image_sources else None,
            has_text=bool(text_feedback.strip()),
            has_images=bool(images),
            image_count=len(images),
            timestamp=datetime.now().isoformat()
        )
    
    def _cleanup(self):
        """清理资源"""
        try:
            # 清空队列
            while not self._result_queue.empty():
                try:
                    self._result_queue.get_nowait()
                except queue.Empty:
                    break
            
            # 等待线程结束
            if self._dialog_thread and self._dialog_thread.is_alive():
                self._dialog_thread.join(timeout=1.0)
            
        except Exception as e:
            self.logger.warning(f"清理资源时出错: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "queue_size": self._result_queue.qsize(),
            "thread_active": self._dialog_thread.is_alive() if self._dialog_thread else False,
            "settings": {
                "timeout": self.settings.timeout.default_dialog_timeout,
                "max_image_size": self.settings.image.max_image_size,
                "supported_formats": self.settings.image.supported_formats
            }
        }
