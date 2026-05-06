# DingChecker v4.0

钉钉晨会听记分析工具 - 基于 dws CLI + Claude Code 本地分析

**核心改进**：
- ✅ 无需 Chrome/CDP（代码量减少80%）
- ✅ 无需 Gemini API Key（本地 Claude 分析）
- ✅ 完整逐字稿分析（148段 vs 旧版仅摘要）
- ✅ 精确发言时长统计（毫秒级）
- ✅ 四维度评分体系（总分20分）

## 评分体系

**四维度（总分20分）**：
1. **昨日战果** (1-5分) - 是否清晰汇报昨天成果
2. **今日计划** (1-5分) - 是否有明确的今日任务
3. **协同效率** (1-5分) - 管理者+协同方响应是否及时
4. **点评效率** (1-5分) - 管理者指导是否有力（20-30%时长占比）

详细标准：[docs/meeting_guidelines_v4.md](docs/meeting_guidelines_v4.md)

## 技术架构

**数据流**：
```
AiTable (29业务单元) → dws CLI API → 完整转写(148段) 
  → 发言人时长统计 → Claude Code 分析 → Markdown 报告
```

**优势**：
- 数据完整可控（原始转写 vs AI摘要）
- 无外部依赖（无需 Gemini API Key）
- 可精确量化（发言时长、关键词频率）
- 成本为零（本地 Claude 分析）

## 快速开始

### 1. 前置条件

系统会自动安装和认证 dws CLI，无需手动配置。

### 2. 推荐使用方式：collect

```bash
# 分析单个业务单元今天的早会
/ding-check collect 东北组

# 分析整个战队昨天的早会
/ding-check collect 政府头部战队 2026-04-29

# 分析战区所有单元
/ding-check collect 华北东北战区

# 分析所有业务单元
/ding-check collect 全部
```

### 3. 查看报告

报告自动保存到 Obsidian vault：
```
~/.claude/Obsidian Vault/ai-output/dingtalk-minutes/report_YYYY-MM-DD.md
```

也可以用命令查看：
```bash
/ding-check view 2026-04-30
```

## 仓库结构

```text
dingchecker/
├── skill/
│   ├── skill.sh
│   ├── SKILL.md
│   └── README_GITHUB.md
├── scripts/
│   ├── daily_check.py
│   ├── generate_html_report.py
│   ├── report_data.py
│   ├── gemini_sdk.py
│   ├── cdp_helper.py
│   └── check_cdp_connection.py
├── chrome/
│   └── start_chrome_debug.sh
├── config/
│   └── business_units.txt
├── docs/
└── data/
    ├── chrome_profiles/
    └── daily_reports/
```

## 环境要求

- macOS + Google Chrome
- Python `3.10+` 推荐
- `playwright`
- `google-genai`
- 可用的 Gemini API Key

安装依赖示例：

```bash
pip3 install playwright pandas google-genai
playwright install chromium
```

## 快速开始

### 1. 配置 API Key

```bash
export GEMINI_API_KEY='your-api-key'
```

也可以使用 [config.example.sh](/Users/zhangniandong/repos/dingchecker/skill/config.example.sh) 的方式落到本地配置文件。

### 2. 启动项目自管 Chrome 实例

推荐使用独立端口和独立 profile：

```bash
DINGCHECK_CDP_PORT=9333 \
bash /Users/zhangniandong/repos/dingchecker/chrome/start_chrome_debug.sh --port 9333
```

首次启动后，请在这个 Chrome 实例里手动登录钉钉，登录态会保存在 `data/chrome_profiles/`。

### 3. 推荐运行方式：collect 半自动收集

所有管理者默认使用同一个固定钉钉 AI 听记汇总页：

```text
https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm
```

运行：

```bash
DINGCHECK_CDP_PORT=9333 \
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh collect 华北东北战区 2026-04-21
```

流程：

1. 程序自动打开固定钉钉汇总页。
2. 管理者在浏览器里筛选/定位日期。
3. 管理者人工判断哪些业务单元开会，并手动点击要分析的 AI 听记链接。
4. 确认听记页可访问后，回到终端或对话继续。
5. dingchecker 扫描已打开的听记页，提取转写并生成横向比较报告。

也可以通过 Codex Skill 自然语言调用，例如：

```text
用 ding-checker 检查今天华北东北战区早会
```

### 4. 兼容运行方式：全自动检查

全自动模式仍保留，但不再作为推荐主路径，因为钉钉文档目录、日期行和链接列的 DOM 结构不稳定。

```bash
DINGCHECK_CDP_PORT=9333 \
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh 政府头部战队 2026-03-25
```

### 5. 查看结果

```bash
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh view 2026-03-25
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh list
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh search 风险
```

## 输出说明

默认输出到 `data/daily_reports/`：

- latest JSON: `report_YYYY-MM-DD.json`
- latest HTML: `report_YYYY-MM-DD.html`
- archive JSON: `report_YYYY-MM-DD__RUN_ID.json`
- archive HTML: `report_YYYY-MM-DD__RUN_ID.html`

兼容输出默认关闭：

- `DINGCHECK_GENERATE_TXT=1` 开启 TXT
- `DINGCHECK_GENERATE_PDF=1` 开启 PDF

## 报告内容

当前 HTML 报告包含：

- 固定开篇模块“业务单元每日晨会建议”
- 采集分组概览
- 采集结果明细
- 详细评分表
- 业务单元详细诊断
- 原始 AI 文本追溯区

战队 / 战区报告标题会自动带上范围名，例如：

- `政府头部战队业务单元横向比较报告（媒体军工组、交通行业组、政府行业一组、政府行业二组）`
- `北京非金一组 早会质量评估报告`

## 已知边界

- 当前依赖 Chrome CDP 和已登录钉钉会话
- Python `3.9` 虽可运行，但会出现 `google-auth` 的 EOL warning，建议升级到 `3.10+`
- 少数 AI 听记页面的“转写正文” DOM 结构仍可能不一致，正文提取已明显增强，但不是所有页面都完全同构
- “单人发言超过 2 分钟”提醒能力已接入结构化链路，但依赖转写页时间轴是否可稳定提取，不保证每个页面都能识别到

## 相关文档

- [skill/SKILL.md](/Users/zhangniandong/repos/dingchecker/skill/SKILL.md)
- [skill/README_GITHUB.md](/Users/zhangniandong/repos/dingchecker/skill/README_GITHUB.md)
- [docs/AI_ANALYSIS_SETUP.md](/Users/zhangniandong/repos/dingchecker/docs/AI_ANALYSIS_SETUP.md)
- [docs/使用指南.md](/Users/zhangniandong/repos/dingchecker/docs/使用指南.md)

## 建议的 push 前检查

```bash
python3 -m py_compile scripts/daily_check.py scripts/generate_html_report.py scripts/report_data.py scripts/gemini_sdk.py
bash -n skill/skill.sh
git status
```
