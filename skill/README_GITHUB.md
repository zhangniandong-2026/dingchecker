# DingChecker Skill

钉钉晨会听记检查与 AI 评估 Skill。

当前主链：

`DingTalk / AI 听记 -> 结构化 JSON -> HTML 报告`

默认输出 `HTML + JSON`，`TXT/PDF` 仅作为兼容产物保留。

## 核心能力

- 自动连接 Chrome CDP 并复用已登录钉钉状态
- 支持按单业务单元、战队、战区批量检查
- 自动生成业务单元横向比较报告
- 基于 `google-genai` 做 5 维度晨会质量评估
- 默认保留 latest 报告与带 `run_id` 的归档报告

## 依赖

- macOS + Google Chrome
- Python `3.10+` 推荐
- `playwright`
- `google-genai`
- Gemini API Key

安装示例：

```bash
pip3 install playwright pandas google-genai
playwright install chromium
```

## 启动方式

推荐先启动项目自管 Chrome 实例：

```bash
DINGCHECK_CDP_PORT=9333 \
bash /Users/zhangniandong/repos/dingchecker/chrome/start_chrome_debug.sh --port 9333
```

首次启动后，请在这个实例中手动登录钉钉。

## 使用方法

### 检查今天

```bash
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh
```

### 检查指定战队 / 战区

```bash
DINGCHECK_CDP_PORT=9333 \
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh 政府头部战队 2026-03-25
```

### 检查单业务单元

```bash
DINGCHECK_CDP_PORT=9333 \
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh 交通行业组 2026-03-25
```

### 查看历史报告

```bash
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh view 2026-03-25
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh list
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh search 风险
bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh status
```

## 报告输出

默认输出到 `data/daily_reports/`：

- latest JSON: `report_YYYY-MM-DD.json`
- latest HTML: `report_YYYY-MM-DD.html`
- archive JSON: `report_YYYY-MM-DD__RUN_ID.json`
- archive HTML: `report_YYYY-MM-DD__RUN_ID.html`

兼容输出默认关闭：

```bash
DINGCHECK_GENERATE_TXT=1 bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh
DINGCHECK_GENERATE_PDF=1 bash /Users/zhangniandong/repos/dingchecker/skill/skill.sh
```

## 报告内容

- 固定开篇模块“业务单元每日晨会建议”
- 采集分组概览
- 采集结果明细
- 详细评分表
- 业务单元详细诊断
- 原始 AI 文本追溯区

战队 / 战区运行时，标题会自动带上范围名，例如：

- `政府头部战队业务单元横向比较报告（媒体军工组、交通行业组、政府行业一组、政府行业二组）`
- `华北东北战区业务单元横向比较报告（北京非金一组、北京非金二组、北京金融分战队、东北组等7个业务单元）`

## 已知边界

- 依赖 Chrome CDP 与已登录钉钉会话
- Python `3.9` 仍可运行，但会出现 `google-auth` 的 EOL warning，建议升级到 `3.10+`
- 少数 AI 听记页面的“转写正文” DOM 结构仍可能不同，正文提取已增强，但并非所有页面完全同构
- “单人发言超过 2 分钟”提醒能力已接入结构化链路，但依赖转写页时间轴能否稳定提取

## 仓库内关键文件

- [skill.sh](/Users/zhangniandong/repos/dingchecker/skill/skill.sh)
- [daily_check.py](/Users/zhangniandong/repos/dingchecker/scripts/daily_check.py)
- [generate_html_report.py](/Users/zhangniandong/repos/dingchecker/scripts/generate_html_report.py)
- [report_data.py](/Users/zhangniandong/repos/dingchecker/scripts/report_data.py)
- [gemini_sdk.py](/Users/zhangniandong/repos/dingchecker/scripts/gemini_sdk.py)
