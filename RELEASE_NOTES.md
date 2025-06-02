# 📋 发布说明

## 🎯 MCP Feedback Collector v2.0.0

### 项目简介
交互式反馈收集器 MCP 服务器 - 为AI助手提供现代化的图形界面反馈收集功能。

### ✨ 主要特性

#### 🎨 现代化UI设计
- 美观的图形用户界面，采用微软雅黑字体
- 直观的区域划分，彩色按钮和图标
- 700x800像素窗口，支持调整大小
- 丰富的提示信息和状态反馈

#### 📷 强大的图片功能
- 支持同时选择和提交多张图片
- 支持文件选择和剪贴板粘贴两种方式
- 实时缩略图预览（100x80像素）
- 每张图片独立删除，一键清除所有图片

#### 💬 灵活的反馈方式
- 纯文字反馈：多行文本输入
- 纯图片反馈：只提交图片
- 混合反馈：文字+多张图片组合
- 自动时间戳记录

### 🔧 核心功能

1. **collect_feedback()** - 主要的反馈收集功能
2. **pick_image()** - 简化的图片选择功能  
3. **get_image_info()** - 获取图片详细信息

### 🚀 安装方式

#### 推荐：使用uvx（零配置）
```bash
# 安装uvx
pip install uvx

# 配置Claude Desktop
{
  "mcpServers": {
    "mcp-feedback-collector": {
      "command": "uvx",
      "args": ["mcp-feedback-collector"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "MCP_DIALOG_TIMEOUT": "600"
      }
    }
  }
}
```

### 💻 技术栈
- **MCP协议**：FastMCP框架
- **GUI框架**：tkinter + scrolledtext
- **图片处理**：PIL/Pillow + ImageTk
- **多线程**：threading + queue
- **数据格式**：TextContent + MCPImage

### 🎯 使用场景
- AI助手完成任务后收集用户反馈
- 收集包含图片的详细用户意见
- 获取用户对AI工作的评价和建议
- 收集相关的截图或图片资料

### 📦 包含文件
- `src/mcp_feedback_collector/server.py` - 主服务器代码（598行）
- `src/mcp_feedback_collector/__init__.py` - 包初始化
- `pyproject.toml` - 项目配置
- `README.md` - 详细文档
- `LICENSE` - MIT开源许可证

### 🎉 首次发布
这是MCP Feedback Collector的首次正式发布，提供了完整的功能和美观的用户界面。

---

**开发者**: MCP Feedback Collector Team  
**许可证**: MIT License  
**Python要求**: >=3.8  
**依赖包**: mcp, pillow>=8.0.0 