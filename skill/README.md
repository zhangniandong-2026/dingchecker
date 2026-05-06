# ding-check

钉钉晨会质量分析 skill。两阶段工作流：

1. **数据收集**（自动）：`dws minutes` 拉听记 → JSON
2. **质量分析**（Claude 本地）：JSON → 四维度评分 → Markdown 报告写入 Obsidian vault

完整说明见 [SKILL.md](./SKILL.md)。

## 快速开始

通过 `~/.claude/skills/ding-check`（symlink 到本目录）调用：

```bash
/ding-check collect 全部                  # 拉今天 35 个单元
/ding-check collect 政府头部战队 2026-04-30  # 指定战队 + 日期
/ding-check view 2026-04-30               # 查报告
/ding-check list-units                    # 列单元
/ding-check help
```

## 依赖

- **dws CLI** — 未装时 skill 自动安装到 `~/.local/bin/dws`，token 失效自动 `dws auth login`
- **Python 3** — 跑 `scripts/collect_minutes_dws.py`
- **Obsidian vault** — 默认 `~/.claude/Obsidian Vault`，`DINGCHECK_VAULT_PATH` 可覆盖

无 Chrome / Playwright / Gemini API（v3 全部移除）。

## 关键路径

| 用途 | 路径 |
|------|------|
| skill 入口 | `~/repos/dingchecker/skill/skill.sh` |
| 数据收集脚本 | `~/repos/dingchecker/scripts/collect_minutes_dws.py` |
| 单元映射 | `~/repos/dingchecker/config/unit_to_table.json` |
| 评分标准 | `~/repos/dingchecker/docs/meeting_guidelines_v4.md` |
| JSON 输出 | `~/repos/dingchecker/data/daily_reports/minutes_<date>.json` |
| 报告输出 | `~/.claude/Obsidian Vault/ai-output/dingtalk-minutes/report_<date>.md` |

## 版本

- **v4.1** (2026-05-05)：单一报告输出到 vault
- **v4.0** (2026-04-30)：Chrome/CDP → dws CLI；Gemini → Claude 本地分析；代码精简 80%
- **v3.x**：Chrome+Playwright+Gemini+PDF（已废弃，备份在 `skill_v3_backup.sh`）
