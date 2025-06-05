"""
交互式反馈收集器 MCP 服务器
AI调用时会汇报工作内容，用户可以提供文本反馈和/或图片反馈
"""

import os
from pathlib import Path
from typing import List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Image as MCPImage
from mcp.types import TextContent

from .config import get_settings
from .core import FeedbackCollector, ImageHandler
from .utils.logger import setup_logging, get_logger

# 初始化日志系统
logger = setup_logging()

# 创建MCP服务器
mcp = FastMCP(
    "交互式反馈收集器",
    dependencies=["pillow", "tkinter"]
)

# 全局实例
feedback_collector: Optional[FeedbackCollector] = None
image_handler: Optional[ImageHandler] = None


def get_feedback_collector() -> FeedbackCollector:
    """获取反馈收集器实例"""
    global feedback_collector
    if feedback_collector is None:
        feedback_collector = FeedbackCollector()
    return feedback_collector


def get_image_handler() -> ImageHandler:
    """获取图片处理器实例"""
    global image_handler
    if image_handler is None:
        image_handler = ImageHandler()
    return image_handler


@mcp.tool()
def collect_feedback(work_summary: str = "", timeout_seconds: Optional[int] = None) -> List:
    """
    收集用户反馈的交互式工具。AI可以汇报完成的工作，用户可以提供文字和/或图片反馈。

    Args:
        work_summary: AI完成的工作内容汇报
        timeout_seconds: 对话框超时时间（秒），默认使用配置中的值

    Returns:
        包含用户反馈内容的列表，可能包含文本和图片
    """
    try:
        collector = get_feedback_collector()
        result = collector.collect_feedback(work_summary, timeout_seconds)
        
        if not result.success:
            raise Exception(result.message)
        
        # 构建返回内容列表
        feedback_items = []
        
        # 添加文字反馈
        if result.has_text:
            feedback_items.append(TextContent(
                type="text",
                text=f"用户文字反馈：{result.text_feedback}\n提交时间：{result.timestamp}"
            ))
        
        # 添加图片反馈
        if result.has_images:
            for image_data, source in zip(result.images, result.image_sources):
                feedback_items.append(MCPImage(data=image_data, format='png'))
        
        return feedback_items
        
    except Exception as e:
        logger.error(f"收集反馈失败: {e}")
        raise Exception(f"收集反馈失败: {str(e)}")


@mcp.tool()
def pick_image() -> MCPImage:
    """
    弹出图片选择对话框，让用户选择图片文件或从剪贴板粘贴图片。
    用户可以选择本地图片文件，或者先截图到剪贴板然后粘贴。
    """
    try:
        collector = get_feedback_collector()
        image_data = collector.pick_image()
        
        if image_data is None:
            raise Exception("未选择图片或操作被取消")
        
        return MCPImage(data=image_data, format='png')
        
    except Exception as e:
        logger.error(f"选择图片失败: {e}")
        raise Exception(f"选择图片失败: {str(e)}")


@mcp.tool()
def get_image_info(image_path: str) -> str:
    """
    获取指定路径图片的信息（尺寸、格式等）

    Args:
        image_path: 图片文件路径
    """
    try:
        handler = get_image_handler()
        
        # 加载图片
        result = handler.load_image_from_file(image_path)
        if not result:
            return f"无法加载图片文件: {image_path}"
        
        image_data, source = result
        info = handler.get_image_info(image_data)
        
        if not info:
            return f"无法获取图片信息: {image_path}"
        
        # 格式化信息
        path = Path(image_path)
        formatted_info = {
            "文件名": path.name,
            "格式": info.get("format", "未知"),
            "尺寸": f"{info.get('width', 0)} x {info.get('height', 0)}",
            "模式": info.get("mode", "未知"),
            "文件大小": f"{info.get('data_size', 0) / 1024:.1f} KB",
            "是否透明": "是" if info.get("has_transparency", False) else "否"
        }
        
        return "\n".join([f"{k}: {v}" for k, v in formatted_info.items()])
        
    except Exception as e:
        logger.error(f"获取图片信息失败: {e}")
        return f"获取图片信息失败: {str(e)}"


if __name__ == "__main__":
    mcp.run()


def main():
    """Main entry point for the mcp-feedback-collector command."""
    mcp.run()
