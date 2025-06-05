"""
工具函数模块
提供各种实用的辅助函数
"""

import os
import sys
import threading
import functools
from pathlib import Path
from typing import Any, Callable, Optional, Union, List, Tuple
import tkinter as tk

from .logger import get_logger


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化后的大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_image_format(file_path: Union[str, Path]) -> bool:
    """
    验证图片格式
    
    Args:
        file_path: 图片文件路径
        
    Returns:
        是否为支持的图片格式
    """
    try:
        from PIL import Image
        from ..config import get_settings
        
        settings = get_settings()
        
        with Image.open(file_path) as img:
            return img.format in settings.image.supported_formats
    except Exception:
        return False


def safe_thread_run(target: Callable, args: tuple = (), kwargs: dict = None, 
                   daemon: bool = True, name: str = None) -> threading.Thread:
    """
    安全地运行线程
    
    Args:
        target: 目标函数
        args: 位置参数
        kwargs: 关键字参数
        daemon: 是否为守护线程
        name: 线程名称
        
    Returns:
        线程对象
    """
    if kwargs is None:
        kwargs = {}
    
    logger = get_logger(__name__)
    
    def safe_target():
        try:
            target(*args, **kwargs)
        except Exception as e:
            logger.exception(f"线程 {name or 'unnamed'} 执行失败: {e}")
    
    thread = threading.Thread(
        target=safe_target,
        daemon=daemon,
        name=name
    )
    thread.start()
    return thread


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        Path对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_app_data_dir() -> Path:
    """
    获取应用数据目录
    
    Returns:
        应用数据目录路径
    """
    if sys.platform == "win32":
        base_dir = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        base_dir = Path.home() / ".local" / "share"
    
    app_dir = base_dir / "mcp_feedback_collector"
    return ensure_directory(app_dir)


def center_window(window: tk.Tk, width: int = None, height: int = None):
    """
    将窗口居中显示
    
    Args:
        window: tkinter窗口对象
        width: 窗口宽度
        height: 窗口高度
    """
    # 更新窗口以获取实际尺寸
    window.update_idletasks()
    
    if width is None:
        width = window.winfo_width()
    if height is None:
        height = window.winfo_height()
    
    # 获取屏幕尺寸
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # 计算居中位置
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    # 设置窗口位置
    window.geometry(f"{width}x{height}+{x}+{y}")


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, 
                      exceptions: Tuple[Exception, ...] = (Exception,)):
    """
    异常重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} 重试 {max_retries} 次后仍然失败: {e}")
                        raise
                    
                    logger.warning(f"{func.__name__} 第 {attempt + 1} 次尝试失败: {e}，{delay}秒后重试")
                    import time
                    time.sleep(delay)
            
        return wrapper
    return decorator


def debounce(wait_time: float):
    """
    防抖装饰器
    
    Args:
        wait_time: 等待时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        timer = None
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal timer
            
            def call_func():
                func(*args, **kwargs)
            
            if timer:
                timer.cancel()
            
            timer = threading.Timer(wait_time, call_func)
            timer.start()
        
        return wrapper
    return decorator


def throttle(interval: float):
    """
    节流装饰器
    
    Args:
        interval: 间隔时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        last_called = [0.0]
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            now = time.time()
            
            if now - last_called[0] >= interval:
                last_called[0] = now
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def singleton(cls):
    """
    单例装饰器
    """
    instances = {}
    lock = threading.Lock()
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


def memoize(maxsize: int = 128):
    """
    记忆化装饰器
    
    Args:
        maxsize: 最大缓存大小
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_order = []
        lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = str(args) + str(sorted(kwargs.items()))
            
            with lock:
                if key in cache:
                    # 移动到最前面（LRU）
                    cache_order.remove(key)
                    cache_order.append(key)
                    return cache[key]
                
                # 计算结果
                result = func(*args, **kwargs)
                
                # 添加到缓存
                cache[key] = result
                cache_order.append(key)
                
                # 清理旧缓存
                while len(cache) > maxsize:
                    old_key = cache_order.pop(0)
                    del cache[old_key]
                
                return result
        
        return wrapper
    return decorator


def is_dark_mode() -> bool:
    """
    检测系统是否为深色模式
    
    Returns:
        是否为深色模式
    """
    try:
        if sys.platform == "win32":
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
        elif sys.platform == "darwin":
            import subprocess
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True
            )
            return "Dark" in result.stdout
    except Exception:
        pass
    
    return False  # 默认返回False
