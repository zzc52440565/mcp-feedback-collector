"""
MCP Feedback Collector - Interactive user feedback collection for MCP servers.

This package provides a modern GUI-based feedback collection system for
Model Context Protocol (MCP) servers, allowing AI assistants to gather
user feedback through an intuitive interface.

Version 3.0.0 - 重构优化版
- 模块化架构设计
- 现代化UI组件
- 完善的配置管理
- 增强的错误处理
- 优化的性能表现
"""

__version__ = "3.0.0"
__author__ = "MCP Feedback Collector Team"
__email__ = "feedback@mcp-collector.com"

from .server import main
from .config import get_settings
from .core import FeedbackCollector, ImageHandler
from .ui import ModernTheme

__all__ = [
    "main",
    "get_settings",
    "FeedbackCollector",
    "ImageHandler",
    "ModernTheme"
]