"""
日志管理模块
提供统一的日志记录功能
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from ..config import get_settings


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        
        return super().format(record)


def setup_logging(name: str = "mcp_feedback_collector") -> logging.Logger:
    """
    设置日志系统
    
    Args:
        name: 日志器名称
        
    Returns:
        配置好的日志器
    """
    settings = get_settings()
    
    # 创建日志器
    logger = logging.getLogger(name)
    
    # 避免重复配置
    if logger.handlers:
        return logger
    
    # 设置日志级别
    level = getattr(logging, settings.log.level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    colored_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果启用）
    if settings.log.enable_file_logging:
        try:
            # 创建日志目录
            log_dir = Path.home() / '.mcp_feedback_collector' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / settings.log.log_file
            
            # 使用RotatingFileHandler进行日志轮转
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=settings.log.max_log_size,
                backupCount=settings.log.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            logger.warning(f"无法创建文件日志处理器: {e}")
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称，如果为None则使用调用模块名
        
    Returns:
        日志器实例
    """
    if name is None:
        # 获取调用者的模块名
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    # 确保根日志器已配置
    root_logger = logging.getLogger("mcp_feedback_collector")
    if not root_logger.handlers:
        setup_logging()
    
    # 返回子日志器
    return logging.getLogger(f"mcp_feedback_collector.{name}")


class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, logger: logging.Logger, level: int = logging.INFO):
        self.logger = logger
        self.level = level
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.log(self.level, f"操作完成，耗时: {duration:.3f}秒")
        else:
            self.logger.error(f"操作失败，耗时: {duration:.3f}秒，错误: {exc_val}")
    
    def log(self, message: str, level: int = None):
        """记录日志"""
        if level is None:
            level = self.level
        self.logger.log(level, message)


def log_performance(func):
    """性能日志装饰器"""
    def wrapper(*args, **kwargs):
        import time
        import functools
        
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} 执行完成，耗时: {duration:.3f}秒")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败，耗时: {duration:.3f}秒，错误: {e}")
            raise
    
    return wrapper


def log_exception(logger: Optional[logging.Logger] = None):
    """异常日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"{func.__name__} 发生异常: {e}")
                raise
        
        return wrapper
    return decorator
