# 🎯 MCP反馈收集器

一个现代化的 Model Context Protocol (MCP) 服务器，为AI助手提供交互式用户反馈收集功能。

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 在cursor规则中可以下面这样配置

“Whenever you want to ask a question, always call the MCP .

Whenever you’re about to complete a user request, call the MCP instead of simply ending the process. Keep calling MCP until the user’s feedback is empty, then end the request. mcp-feedback-collector.collect_feedback ”

## 相关教程链接
油管：https://youtu.be/aYtGm1xHNXI
B站：https://www.bilibili.com/video/BV1J6jyzQE8P/

## ✨ 主要特性

- 🎨 **现代化界面** - 美观的700x800像素GUI，支持中文界面
- 📷 **多图片支持** - 同时选择多张图片，支持文件选择和剪贴板粘贴
- 💬 **灵活反馈** - 支持纯文字、纯图片或文字+图片组合反馈
- ⚡ **零配置安装** - 使用uvx一键安装，无需复杂配置
- 🔧 **智能超时** - 可配置的对话框超时时间，避免操作中断

## 🚀 快速开始

### 1. 安装uvx
```bash
pip install uvx
```

### 2. 配置Claude Desktop
在 `claude_desktop_config.json` 中添加：

```json
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

### 3. 重启Claude Desktop
配置完成后重启Claude Desktop即可使用。

## 🛠️ 核心功能

### collect_feedback()
收集用户反馈的主要工具，AI可以汇报工作内容，用户提供文字和图片反馈。

```python
# AI调用示例
result = collect_feedback("我已经完成了代码优化工作...")
```

### pick_image()
快速图片选择工具，用于单张图片选择场景。

### get_image_info()
获取图片文件的详细信息（格式、尺寸、大小等）。

## 🖼️ 界面预览

```
🎯 工作完成汇报与反馈收集
┌─────────────────────────────────────────┐
│ 📋 AI工作完成汇报                        │
│ ┌─────────────────────────────────────┐ │
│ │ [AI汇报的工作内容显示在这里]         │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 💬 您的文字反馈（可选）                  │
│ ┌─────────────────────────────────────┐ │
│ │ [多行文本输入区域]                   │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🖼️ 图片反馈（可选，支持多张）            │
│ [📁选择文件] [📋粘贴] [❌清除]           │
│ [图片缩略图预览区域]                     │
└─────────────────────────────────────────┘

[✅ 提交反馈]  [❌ 取消]
```

## ⚙️ 配置说明

### 超时设置
- `MCP_DIALOG_TIMEOUT`: 对话框等待时间（秒）
  - 默认：300秒（5分钟）
  - 建议：600秒（10分钟）
  - 复杂操作：1200秒（20分钟）

### 支持的图片格式
PNG、JPG、JPEG、GIF、BMP、WebP

## 💡 使用场景

- ✅ AI完成任务后收集用户评价
- ✅ 收集包含截图的详细反馈
- ✅ 获取用户对代码/设计的意见
- ✅ 收集bug报告和改进建议

## 🔧 技术栈

- **MCP框架**: FastMCP
- **GUI**: tkinter + PIL
- **多线程**: threading + queue
- **图片处理**: Pillow

## 📝 更新日志

### v2.0.0 (2025-05-28)
- 🎨 全新现代化UI设计
- 📷 多图片同时提交支持
- 🖼️ 横向滚动图片预览
- 💫 彩色按钮和图标
- 🔧 优化用户体验

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**让AI与用户的交互更高效直观！** 🎯 
## 感谢支持
https://api.ssopen.top/  API中转站，290+AI 大模型，官方成本七分之一，支持高并发！
