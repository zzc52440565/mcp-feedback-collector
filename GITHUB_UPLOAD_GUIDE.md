# 📤 GitHub上传指南

本指南将帮助你将 mcp-feedback-collector 项目上传到GitHub。

## 🛠️ 准备工作

### 1. 安装Git（如果还没安装）
访问 [https://git-scm.com/download/windows](https://git-scm.com/download/windows) 下载并安装Git。

### 2. 创建GitHub账户
如果还没有GitHub账户，请访问 [https://github.com](https://github.com) 注册。

## 📦 上传步骤

### 方法一：使用GitHub网页上传（推荐，适合新手）

1. **登录GitHub** 
   - 访问 [https://github.com](https://github.com)
   - 点击右上角"Sign in"登录

2. **创建新仓库**
   - 点击右上角的"+"号，选择"New repository"
   - Repository name: `mcp-feedback-collector`
   - Description: `交互式反馈收集器 MCP 服务器 - 为AI助手提供图形界面反馈收集功能`
   - 选择"Public"（公开）
   - 不要勾选"Add a README file"（我们已经有了）
   - 点击"Create repository"

3. **上传项目文件**
   - 在新创建的仓库页面，点击"uploading an existing file"
   - 将以下文件拖拽到上传区域：
     ```
     ✅ README.md
     ✅ pyproject.toml
     ✅ LICENSE
     ✅ requirements.txt
     ✅ .gitignore
     ✅ MANIFEST.in
     ✅ src/ (整个文件夹)
     ❌ dist/ (不要上传，这是构建产物)
     ❌ __pycache__/ (不要上传)
     ❌ .cursor/ (不要上传)
     ❌ server.py (根目录的，不需要)
     ❌ test_gui.py (测试文件，不需要)
     ❌ start_server.bat (不需要)
     ❌ claude_config_*.json (配置示例，不需要)
     ```

4. **提交上传**
   - 在页面底部填写提交信息：
     - Commit message: `Initial commit - MCP Feedback Collector v2.0.0`
   - 点击"Commit changes"

### 方法二：使用Git命令行（适合熟悉命令行的用户）

1. **初始化Git仓库**
   ```bash
   cd D:\zhuomian\duihuamcp\image-picker-mcp
   git init
   ```

2. **添加文件到版本控制**
   ```bash
   git add README.md pyproject.toml LICENSE requirements.txt .gitignore MANIFEST.in src/
   ```

3. **首次提交**
   ```bash
   git commit -m "Initial commit - MCP Feedback Collector v2.0.0"
   ```

4. **添加远程仓库**
   ```bash
   git remote add origin https://github.com/你的用户名/mcp-feedback-collector.git
   ```

5. **推送到GitHub**
   ```bash
   git branch -M main
   git push -u origin main
   ```

## 🔧 上传后的配置

### 1. 更新pyproject.toml中的链接
上传完成后，将 `pyproject.toml` 中的 `yourusername` 替换为你的实际GitHub用户名：

```toml
[project.urls]
Homepage = "https://github.com/你的用户名/mcp-feedback-collector"
Repository = "https://github.com/你的用户名/mcp-feedback-collector"
Documentation = "https://github.com/你的用户名/mcp-feedback-collector#readme"
"Bug Tracker" = "https://github.com/你的用户名/mcp-feedback-collector/issues"
```

### 2. 创建Release（可选）
1. 在GitHub仓库页面点击"Releases"
2. 点击"Create a new release"
3. Tag version: `v2.0.0`
4. Release title: `MCP Feedback Collector v2.0.0`
5. 描述发布内容，点击"Publish release"

## 📋 文件清单

### ✅ 需要上传的文件
- `README.md` - 项目说明文档
- `pyproject.toml` - 项目配置文件
- `LICENSE` - 开源许可证
- `requirements.txt` - 依赖列表
- `.gitignore` - Git忽略规则
- `MANIFEST.in` - 打包清单
- `src/mcp_feedback_collector/` - 源代码目录
  - `__init__.py` - 包初始化文件
  - `server.py` - 主服务器代码

### ❌ 不要上传的文件
- `dist/` - 构建产物目录
- `__pycache__/` - Python缓存
- `.cursor/` - 编辑器配置
- `server.py` - 根目录的旧版本文件
- `test_gui.py` - 测试文件
- `start_server.bat` - 本地启动脚本
- `claude_config_*.json` - 配置示例文件

## 🎯 完成后

上传完成后，你的项目将可以通过以下方式安装：

```bash
# 使用uvx安装（推荐）
uvx mcp-feedback-collector

# 或从GitHub直接安装
pip install git+https://github.com/你的用户名/mcp-feedback-collector.git
```

## 💡 提示

1. **保护隐私**：确保不上传包含个人信息的配置文件
2. **定期更新**：项目有更新时记得推送到GitHub
3. **管理Issues**：GitHub的Issues功能可以用来收集用户反馈
4. **文档维护**：保持README文档的更新和准确性

---

🎉 **恭喜！你的项目现在已经在GitHub上了！** 