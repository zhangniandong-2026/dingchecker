---
name: ding-check
description: 钉钉晨会质量分析。用 dws CLI 拉取业务单元的早会听记数据（转写+发言时长），输出 JSON；Claude 读 JSON 按四维度（昨日战果/今日计划/协同效率/点评效率）评分，生成 Markdown 报告到 Obsidian vault。覆盖 35 个业务单元、9 个战队/战区。
---

# ding-check (v4.1)

钉钉晨会听记的两阶段分析工具：

1. **数据收集**（skill 自动）：`dws minutes` 拉听记 → JSON
2. **质量分析**（Claude 本地）：读 JSON → 按 [[meeting_guidelines_v4]] 评分 → Markdown 报告

## 命令清单

| 命令 | 用途 |
|------|------|
| `collect <范围> [日期]` | 拉数据。范围: 单元名 / 战队名 / 战区名 / `全部`；日期默认今天 |
| `view [日期]` | 查看已生成的报告（`ai-output/dingtalk-minutes/report_<date>.md`） |
| `list-units` | 列出 35 个业务单元和 9 个战队/战区 |
| `help` | 显示帮助 |

**示例**：
```bash
/ding-check collect 东北组              # 单个业务单元
/ding-check collect 政府头部战队 2026-04-29   # 整个战队 + 指定日期
/ding-check collect 华北东北战区          # 整个战区
/ding-check collect 全部                # 全部 35 个单元
/ding-check view 2026-04-30             # 看历史报告
```

## 工作流（关键）

`collect` 跑完后会输出 `[CLAUDE-ANALYZE]` 提示块——**这是给 Claude 的指令，不是给用户的**。Claude 看到这个标记必须接手做分析：

1. 读取 `~/repos/dingchecker/data/daily_reports/minutes_<date>.json`
2. 对每个有完整转写的单元，按四维度（每维 1-5 分，总 20 分）评分
3. 生成 Markdown 报告写入 `~/.claude/Obsidian Vault/ai-output/dingtalk-minutes/report_<date>.md`
4. 报告必须包含：三类预警 + 综合排名表格 + 详细评分 + 改进建议
5. frontmatter 含 `tags: [ai-generated, dingtalk, daily-companion]`，引用评分标准用 `[[meeting_guidelines_v4]]`

详细评分标准见 `~/repos/dingchecker/docs/meeting_guidelines_v4.md`。

## 评分维度

| 维度 | 权重 | 看什么 |
|------|------|--------|
| 昨日战果 | 1-5 | 客户名 + 动作 + 结果 + 数据 |
| 今日计划 | 1-5 | 客户名 + 动作 + deadline |
| 协同效率 | 1-5 | 管理者响应 + 协同方反馈 |
| 点评效率 | 1-5 | 管理者发言占比 20-30% + 实质指导 |

**评级**：18-20 优秀 / 15-17 良好 / 12-14 及格 / 9-11 需改进 / <9 不合格

## 三类预警

| 标记 | 含义 | 判定 |
|------|------|------|
| 🔴 未开会 | 当日无任何听记记录 | `meeting_count = 0` |
| 🟡 有听记无转写 | 听记存在但未生成转写 | `paragraph_count = 0` |
| 🟣 无访问权限 | dws 调用返回 no permission | `_permission_error = true` |

## 依赖与安装

- **dws CLI**：未安装时 skill 自动安装到 `~/.local/bin/dws`；token 失效自动触发 `dws auth login`
- **Python 3**：用于运行 `scripts/collect_minutes_dws.py`
- **Obsidian vault**：默认 `~/.claude/Obsidian Vault`，可用 `DINGCHECK_VAULT_PATH` 覆盖

无需 Chrome / Playwright / Gemini API（v3 的依赖已全部移除）。

## 目录结构

源代码全部在 `~/repos/dingchecker/`，`~/.claude/skills/ding-check` 是它的 symlink：

```
~/repos/dingchecker/
├── skill/
│   ├── skill.sh                       # 主入口（300 行）
│   └── SKILL.md                       # 本文件
├── scripts/
│   └── collect_minutes_dws.py         # 数据收集
├── config/
│   └── unit_to_table.json             # 35 个单元的映射
├── docs/
│   └── meeting_guidelines_v4.md       # 评分标准
└── data/daily_reports/                # JSON 输出
    └── minutes_<date>.json
```

报告输出：`~/.claude/Obsidian Vault/ai-output/dingtalk-minutes/report_<date>.md`

## 常见情况

**今天没数据**：早会通常 8:30-9:00 开，听记需会议结束后才生成，建议 9:30 后跑

**大量"未开会"**：节假日次日、周末后首日属正常；连续多天则需检查听记是否真的开了/有没有上传

**权限错误集中**：分析账号需被加入对应单元的 AiTable 协作者，或调整听记分享权限

## 业务单元（35 个，分 9 个战队/战区）

- **政府头部战队**(4)：媒体军工组 / 交通行业组 / 政府行业一组 / 政府行业二组
- **华北东北战区**(7)：北京非金一组 / 北京非金二组 / 北京金融分战队 / 东北组 / 华北一组 / 华北二组 / 北京商业组
- **华东战区**(10)：安徽组 / 山东组 / 浙江组 / 江苏非金组 / 苏皖金融组 / 华东通信组 / 上海金融一组 / 上海金融二组 / 上海政企一组 / 上海政企二组
- **华中战区**(3)：河南组 / 湖南组 / 湖北江西组
- **金融头部战队**(1)：金融头部战队
- **华南战区**(5)：南区行业分战队 / 南区金融分战队 / 深圳分战队 / 粤港澳分战队 / 福建组
- **西南西北战区**(1)：西南西北战区
- **通信头部战队**(2)：移动组 / 联通组
- **能源央企头部战队**(2)：能源组 / 央企组

## 版本历史

- **v4.1** (2026-05-05)：单一报告输出到 vault，取消对外发布版
- **v4.0** (2026-04-30)：从 Chrome/CDP 迁移到 dws CLI；取消 Gemini，改用 Claude 本地分析；代码精简 80%（1500→300 行）
- **v3.x** 及以前：Chrome+Playwright+Gemini+PDF 路线，已废弃（备份在 `skill_v3_backup.sh`）
