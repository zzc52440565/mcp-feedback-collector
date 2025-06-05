"""
配置管理模块
提供应用程序的配置管理功能
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class UIConfig:
    """UI配置"""
    window_width: int = 1400
    window_height: int = 1100
    min_width: int = 1200
    min_height: int = 900
    window_alpha: float = 0.98
    enable_shadows: bool = True
    enable_animations: bool = True


@dataclass
class TimeoutConfig:
    """超时配置"""
    default_dialog_timeout: int = 300
    image_load_timeout: int = 30
    clipboard_timeout: int = 10


@dataclass
class ImageConfig:
    """图片配置"""
    max_image_size: int = 10 * 1024 * 1024  # 10MB
    thumbnail_width: int = 100
    thumbnail_height: int = 80
    supported_formats: tuple = ("PNG", "JPG", "JPEG", "GIF", "BMP", "WEBP")
    quality: int = 85


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    enable_file_logging: bool = True
    log_file: str = "mcp_feedback_collector.log"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class Settings:
    """应用程序设置"""
    ui: UIConfig
    timeout: TimeoutConfig
    image: ImageConfig
    log: LogConfig
    
    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> "Settings":
        """从文件加载配置"""
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return cls.from_dict(config_data)
            except Exception as e:
                print(f"加载配置文件失败: {e}，使用默认配置")
        
        return cls.default()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """从字典创建配置"""
        ui_data = data.get('ui', {})
        timeout_data = data.get('timeout', {})
        image_data = data.get('image', {})
        log_data = data.get('log', {})
        
        return cls(
            ui=UIConfig(**ui_data),
            timeout=TimeoutConfig(**timeout_data),
            image=ImageConfig(**image_data),
            log=LogConfig(**log_data)
        )
    
    @classmethod
    def default(cls) -> "Settings":
        """创建默认配置"""
        return cls(
            ui=UIConfig(),
            timeout=TimeoutConfig(),
            image=ImageConfig(),
            log=LogConfig()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def save_to_file(self, config_path: Path) -> None:
        """保存配置到文件"""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置实例"""
    global _settings
    if _settings is None:
        # 尝试从环境变量获取配置路径
        config_path = os.getenv('MCP_CONFIG_PATH')
        if config_path:
            config_path = Path(config_path)
        else:
            # 默认配置路径
            config_path = Path.home() / '.mcp_feedback_collector' / 'config.json'
        
        _settings = Settings.load_from_file(config_path)
        
        # 应用环境变量覆盖
        _apply_env_overrides(_settings)
    
    return _settings


def _apply_env_overrides(settings: Settings) -> None:
    """应用环境变量覆盖"""
    # 超时配置
    if timeout := os.getenv('MCP_DIALOG_TIMEOUT'):
        try:
            settings.timeout.default_dialog_timeout = int(timeout)
        except ValueError:
            pass
    
    # UI配置
    if width := os.getenv('MCP_WINDOW_WIDTH'):
        try:
            settings.ui.window_width = int(width)
        except ValueError:
            pass
    
    if height := os.getenv('MCP_WINDOW_HEIGHT'):
        try:
            settings.ui.window_height = int(height)
        except ValueError:
            pass
    
    # 日志配置
    if log_level := os.getenv('MCP_LOG_LEVEL'):
        settings.log.level = log_level.upper()


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = None
    return get_settings()
