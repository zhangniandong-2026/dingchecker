# 🚀 DingCheck - Claude Code Skill

> 钉钉日会听记自动化检查工具 | DingTalk Daily Meeting Check Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blue)](https://claude.ai/claude-code)

一个用于自动检查钉钉日会听记内容、提取业务单元报告、生成 AI 智能分析的 Claude Code Skill。

## ✨ 核心特性

- 🔗 **固定URL**：自动使用配置的钉钉文档，无需每次输入
- 🤖 **全自动化**：自动启动Chrome、自动打开URL、自动检查
- 🎯 **交互式选择**：灵活选择要检查的业务单元（全部、按战队、部分）
- 📊 **多格式报告**：生成文本、PDF 和 HTML 三种格式
- 🤖 **AI 智能分析**：基于 Gemini API 的 5 维度晨会评估
- 🔍 **风险检测**：自动识别关键风险点
- 📅 **历史管理**：查看、搜索历史报告
- ⚡ **实时反馈**：清晰的执行状态和错误提示

## 📋 AI 分析维度

使用 Google Gemini API 对早会内容进行 5 个维度的专业评估：

1. **目标清晰度 🎯** - 识别量化指标、客户名、时间节点
2. **复盘闭环率 🔄** - 检查计划→执行→复盘的完整闭环
3. **协作敏捷度 🤝** - 识别求助触发词与响应配对
4. **问题聚焦度 🔍** - 计算议题篇幅占比，避免细节陷阱
5. **信息增量 📈** - 评估信息密度和价值

## 📦 安装

### 前置条件

1. **Claude Code CLI** - 安装 [Claude Code](https://claude.ai/claude-code)
2. **Python 3.8+** - 带有以下依赖：
   ```bash
   pip3 install playwright pandas reportlab google-generativeai
   playwright install chromium
   ```
3. **Chrome 浏览器** - 用于调试模式
4. **Gemini API Key** (可选) - 用于 AI 分析 [获取地址](https://aistudio.google.com/app/apikey)

### Skill 安装

```bash
# 克隆到 Claude Skills 目录
cd ~/.claude/skills/
git clone https://github.com/your-username/ding-check.git

# 或直接下载解压
mkdir -p ~/.claude/skills/ding-check
cd ~/.claude/skills/ding-check
# 将文件复制到此目录
```

### 项目结构设置

创建工作目录：

```bash
mkdir -p ~/dingtalk_checker/{scripts,config,daily_reports,chrome}
```

将核心脚本放到项目目录（参见 [项目依赖](#项目依赖)）。

## ⚙️ 配置

### 1. 配置 Gemini API Key（可选）

有三种配置方式：

**方式 1：配置文件（推荐）**
```bash
cd ~/.claude/skills/ding-check
cp config.example.sh config.sh
# 编辑 config.sh，填入你的 API Key
```

**方式 2：环境变量**
```bash
export GEMINI_API_KEY='your-api-key-here'
```

**方式 3：交互式配置**
首次运行 `/ding-check` 时会提示配置。

### 2. 配置钉钉文档 URL

编辑 `skill.sh` 第 30 行：

```bash
DINGTALK_URL="https://alidocs.dingtalk.com/i/nodes/YOUR_DOCUMENT_ID"
```

### 3. 配置业务单元

编辑 `~/dingtalk_checker/config/business_units.txt`：

```
# 华北东北战区
北京非金一组
北京非金二组
东北组

# 政府头部战队
媒体军工组
交通行业组
```

**注释行（#开头）** 表示战队分组，用于交互式菜单。

## 🚀 使用方法

### 主检查功能

```bash
# 检查今天（交互式选择单元）
/ding-check

# 检查指定日期
/ding-check 2026-03-02
```

**交互式菜单**：
- 输入 `1` - 检查所有单元
- 输入 `2` - 检查第一个战队的所有单元
- 输入 `北京非金一组,东北组` - 只检查指定单元
- 直接按 Enter - 默认检查所有单元

### 查看历史报告

```bash
/ding-check view              # 查看今天
/ding-check view 昨天         # 查看昨天
/ding-check view 2026-03-02   # 查看指定日期
```

### 搜索报告内容

```bash
/ding-check search 风险       # 搜索关键词
/ding-check search 未完成     # 搜索任务状态
```

### 列出历史报告

```bash
/ding-check list
```

### 检查系统状态

```bash
/ding-check status
```

## 📊 报告内容

生成的报告包含：

1. **总体统计** - 成功/失败/无权限等
2. **分组统计** - 按战队统计
3. **详细内容** - 每个单元的完整会议转写
4. **AI 智能分析**（如果配置了 API Key）：
   - 5 个维度的专业评估（每个维度 1-5 分）
   - 综合评分排名
   - 各维度表现最好的单元
   - 3-5 条可操作的改进建议

### 报告格式

- **TXT** - `report_2026-03-20.txt` - 纯文本，易搜索
- **PDF** - `report_2026-03-20.pdf` - 美化排版，自动打开

报告保存在：`~/dingtalk_checker/daily_reports/`

## 🔧 项目依赖

需要在 `~/dingtalk_checker/` 目录下包含以下脚本：

### `scripts/daily_check.py`
核心检查脚本，负责：
- 连接 Chrome 调试模式
- 提取钉钉听记内容
- 生成文本报告

### `scripts/generate_pdf_report.py`
PDF 生成脚本，负责：
- 将文本报告转换为美化的 PDF
- 支持中文字体
- 专业排版

### `chrome/start_chrome_debug.sh`
Chrome 启动脚本：
```bash
#!/bin/bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-debug-profile" \
  > /dev/null 2>&1 &
```

这些脚本不包含在本仓库中，需要根据你的实际环境自行创建。

## 🔐 安全说明

- `config.sh` 包含 API Key，已在 `.gitignore` 中排除
- 不要将真实 API Key 提交到 Git
- 分享时使用 `config.example.sh` 模板

## 🤝 与定时任务的关系

**Skill（手动检查）**：
- 交互式选择单元
- 灵活选择日期
- 自动启动 Chrome
- 适合随时手动检查

**定时任务（自动运行）**：
- 使用 `scripts/run_daily_check.sh`
- 每天固定时间自动运行
- 检查所有单元
- 适合每日固定检查

两者独立运行，互不影响！

## 📖 常见问题

### Q: 为什么需要 Gemini API？
A: 用于 AI 智能分析功能。如果不配置，仍可正常提取内容和生成报告，只是会跳过 AI 分析部分。

### Q: Chrome 调试模式是什么？
A: Skill 通过 Chrome DevTools Protocol (CDP) 控制浏览器。需要 Chrome 在 9222 端口开启调试模式。

### Q: 可以同时运行多个检查吗？
A: 不建议。所有检查使用同一个 Chrome 实例和配置文件，并发运行可能导致冲突。

### Q: 报告保存在哪里？
A: `~/dingtalk_checker/daily_reports/` 目录。

### Q: 如何删除旧报告？
A: 直接删除 `daily_reports/` 目录下的文件即可。

## 📝 更新历史

- **v3.0** (2026-03-05)
  - 固定 URL 配置
  - 自动启动 Chrome
  - 交互式业务单元选择
  - 按战队分组显示
  - 临时配置 + trap 机制
  - 与定时任务完全隔离

- **v2.0** (2026-03-03)
  - 重新设计命令结构
  - 新增 status 命令

- **v1.0** (Initial)
  - 基础功能实现

## 📄 许可证

MIT License

## 🙋 贡献

欢迎提交 Issue 和 Pull Request！

## 🔗 相关链接

- [Claude Code 文档](https://docs.anthropic.com/claude/docs)
- [Google Gemini API](https://ai.google.dev/)
- [Playwright 文档](https://playwright.dev/)

---

Made with ❤️ by [Your Name]
