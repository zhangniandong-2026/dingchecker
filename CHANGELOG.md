# DingChecker 更新日志

## v4.1 - 2026-05-05

- 单一报告输出到 Obsidian vault（`~/.claude/Obsidian Vault/ai-output/dingtalk-minutes/`）
- 钉钉群推送 + 钉钉文档自动化（`scripts/auto_report_and_push.sh`）

## v4.0 - 2026-04-30 - 架构重构

### 技术架构

| | v3 | v4 |
|---|---|---|
| 数据来源 | Chrome CDP + Playwright 抓 AI 摘要 | dws CLI 直连 AiTable，拿完整逐字稿 |
| 分析 | Gemini API（外网+收费） | Claude 本地（免费） |
| 输出 | HTML + PDF | Markdown（写入 vault） |
| 依赖 | Playwright + Gemini SDK + Chrome | 仅 dws CLI |

代码精简：`skill.sh` 1514 → 300 行（-80%），Python 脚本 8 → 1 个。

### 评分标准（25 → 20 分）

| v3 五维度 | v4 四维度 |
|---|---|
| 战果汇报 | **昨日战果** |
| 任务聚焦 | **今日计划** |
| 协同效率 | **协同效率**（新增协同方反馈检测） |
| ~~情报敏感~~ | 删除（避免形式化） |
| 点评效率 | **点评效率**（精确量化时长占比） |

新增量化能力：发言人时长（毫秒级）、单人超 2 分钟标记、管理者发言占比、协同方响应统计。

详细评分标准见 [docs/meeting_guidelines_v4.md](docs/meeting_guidelines_v4.md)。

### 迁移注意

- 旧命令仍可用：`/ding-check collect <战队> <日期>`
- 新增 `list-units` 命令
- 报告格式 HTML → Markdown，写入 vault
- 总分 25 → 20，**新旧版本不可直接对比**

## v3.1 - 2026-03-23 - "3+1" 结构化早会评价体系

- 集成"3+1"结构化早会标准（昨日战果 / 今日头号任务 / 项目协同与求助 + 负责人点评规范）
- 评价维度从通用 5 维度升级为与"3+1"模板对齐
- 新增 HTML 可视化报告（Chart.js 雷达图 + 排名柱状图 + 响应式卡片）
- 一键生成 TXT/PDF/HTML 三种格式

## v3.0 - 初始版本

- Chrome CDP + Playwright 抓取钉钉 AI 听记
- Gemini API 分析
- PDF 报告输出
