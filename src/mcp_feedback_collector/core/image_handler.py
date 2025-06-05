"""
图片处理模块
提供图片加载、处理、缓存等功能
"""

import io
import base64
import threading
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import tkinter as tk

from ..config import get_settings
from ..utils.logger import get_logger


class ImageHandler:
    """图片处理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self._cache: Dict[str, Any] = {}
        self._cache_lock = threading.Lock()
    
    def load_image_from_file(self, file_path: str) -> Optional[Tuple[bytes, str]]:
        """
        从文件加载图片
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            (图片数据, 来源信息) 或 None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"图片文件不存在: {file_path}")
                return None
            
            # 检查文件大小
            file_size = path.stat().st_size
            if file_size > self.settings.image.max_image_size:
                self.logger.error(f"图片文件过大: {file_size} bytes")
                return None
            
            # 加载图片
            with Image.open(path) as img:
                # 检查格式
                if img.format not in self.settings.image.supported_formats:
                    self.logger.error(f"不支持的图片格式: {img.format}")
                    return None
                
                # 转换为PNG格式
                img_data = self._image_to_bytes(img)
                source = f"文件: {path.name}"
                
                self.logger.info(f"成功加载图片: {path.name}, 大小: {len(img_data)} bytes")
                return img_data, source
                
        except Exception as e:
            self.logger.error(f"加载图片文件失败: {e}")
            return None
    
    def load_image_from_clipboard(self) -> Optional[Tuple[bytes, str]]:
        """
        从剪贴板加载图片
        
        Returns:
            (图片数据, 来源信息) 或 None
        """
        try:
            # 创建临时窗口获取剪贴板
            temp_root = tk.Tk()
            temp_root.withdraw()
            
            try:
                # 尝试获取剪贴板图片
                img = ImageTk.getimage(temp_root.clipboard_get())
                if img:
                    img_data = self._image_to_bytes(img)
                    source = "剪贴板"
                    
                    self.logger.info(f"成功从剪贴板加载图片, 大小: {len(img_data)} bytes")
                    return img_data, source
            except:
                # 尝试其他方法获取剪贴板图片
                try:
                    from PIL import ImageGrab
                    img = ImageGrab.grabclipboard()
                    if img:
                        img_data = self._image_to_bytes(img)
                        source = "剪贴板"
                        
                        self.logger.info(f"成功从剪贴板加载图片, 大小: {len(img_data)} bytes")
                        return img_data, source
                except ImportError:
                    self.logger.warning("ImageGrab不可用，无法从剪贴板获取图片")
            
            temp_root.destroy()
            return None
            
        except Exception as e:
            self.logger.error(f"从剪贴板加载图片失败: {e}")
            return None
    
    def create_thumbnail(self, image_data: bytes, size: Optional[Tuple[int, int]] = None) -> Optional[ImageTk.PhotoImage]:
        """
        创建缩略图
        
        Args:
            image_data: 图片数据
            size: 缩略图尺寸，默认使用配置中的尺寸
            
        Returns:
            缩略图对象或None
        """
        try:
            if size is None:
                size = (self.settings.image.thumbnail_width, self.settings.image.thumbnail_height)
            
            # 检查缓存
            cache_key = f"thumb_{hash(image_data)}_{size}"
            with self._cache_lock:
                if cache_key in self._cache:
                    return self._cache[cache_key]
            
            # 创建缩略图
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 创建带圆角的缩略图
            thumbnail = self._create_rounded_thumbnail(img, size)
            photo = ImageTk.PhotoImage(thumbnail)
            
            # 缓存结果
            with self._cache_lock:
                self._cache[cache_key] = photo
            
            return photo
            
        except Exception as e:
            self.logger.error(f"创建缩略图失败: {e}")
            return None
    
    def get_image_info(self, image_data: bytes) -> Dict[str, Any]:
        """
        获取图片信息
        
        Args:
            image_data: 图片数据
            
        Returns:
            图片信息字典
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            return {
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height,
                "data_size": len(image_data),
                "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info
            }
        except Exception as e:
            self.logger.error(f"获取图片信息失败: {e}")
            return {}
    
    def _image_to_bytes(self, img: Image.Image) -> bytes:
        """
        将PIL图片转换为字节数据
        
        Args:
            img: PIL图片对象
            
        Returns:
            图片字节数据
        """
        # 确保图片是RGB模式（PNG支持）
        if img.mode not in ('RGB', 'RGBA'):
            if img.mode == 'P' and 'transparency' in img.info:
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
        
        # 转换为字节
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', quality=self.settings.image.quality, optimize=True)
        return buffer.getvalue()
    
    def _create_rounded_thumbnail(self, img: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """
        创建圆角缩略图
        
        Args:
            img: 原始图片
            size: 目标尺寸
            
        Returns:
            圆角缩略图
        """
        # 创建圆角遮罩
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        
        # 绘制圆角矩形
        radius = min(size) // 8  # 圆角半径
        draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
        
        # 创建输出图片
        output = Image.new('RGBA', size, (0, 0, 0, 0))
        
        # 确保输入图片尺寸正确
        if img.size != size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        
        # 应用遮罩
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        output.paste(img, (0, 0))
        output.putalpha(mask)
        
        return output
    
    def clear_cache(self):
        """清除缓存"""
        with self._cache_lock:
            self._cache.clear()
        self.logger.info("图片缓存已清除")
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        with self._cache_lock:
            return len(self._cache)
