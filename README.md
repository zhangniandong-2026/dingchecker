# DingChecker

钉钉晨会听记检查与 AI 评估工具。

当前主链已经收敛为：

`DingTalk / AI 听记 -> 结构化 JSON -> HTML 报告`

默认产物是 `HTML + JSON`，`TXT/PDF` 仅作为兼容产物保留。

## 当前能力

- 自动连接 Chrome CDP，会话内复用已登录的钉钉状态
- 支持按单业务单元、战队、战区批量检查
- 自动提取 AI 听记内容，生成战队/战区横向比较报告
- 使用 `google-genai` 做 5 维度晨会质量评估
- 默认生成结构化 `JSON` 与可视化 `HTML`
- 支持报告归档 `run_id`，避免同日重跑互相覆盖

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

### 3. 运行检查

直接运行 skill 脚本：

```bash
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh
```

指定战队 / 战区：

```bash
DINGCHECK_CDP_PORT=9333 \
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh 政府头部战队 2026-03-25
```

指定单业务单元：

```bash
DINGCHECK_CDP_PORT=9333 \
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh 交通行业组 2026-03-25
```

### 4. 查看结果

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
