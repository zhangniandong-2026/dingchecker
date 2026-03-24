# 🚀 DingCheck - 钉钉日会检查自动化

钉钉日会听记自动化检查工具，支持 AI 智能分析。

## 📁 项目结构

```
dingcheck/
├── skill/              # Claude Code Skill
│   ├── skill.sh        # 主脚本
│   ├── SKILL.md        # Skill 文档
│   └── README.md       # Skill 配置说明
├── scripts/            # Python 脚本
│   ├── daily_check.py  # 核心检查脚本
│   └── generate_pdf_report.py  # PDF 生成
├── config/             # 配置文件
│   └── business_units.txt      # 业务单元配置
├── chrome/             # Chrome 启动脚本
├── docs/               # 文档
└── data/               # 数据目录（不提交到 Git）
    ├── daily_reports/  # 报告输出
    └── logs/           # 日志文件
```

## 🎯 核心特性

- 🔗 **固定URL** - 自动使用配置的钉钉文档
- 🤖 **全自动化** - 自动启动 Chrome、自动检查
- 🎯 **交互式选择** - 灵活选择业务单元
- 📊 **多格式报告** - TXT + PDF
- 🤖 **AI 智能分析** - 基于 Gemini 的 5 维度评估
- 📅 **历史管理** - 查看、搜索历史报告

## 🚀 快速开始

详见 `skill/README.md`

## 📖 文档

- `skill/SKILL.md` - 完整使用文档
- `skill/README.md` - 配置指南
- `docs/` - 其他技术文档

## 🔗 软链接

Claude Code Skill 通过软链接访问：
```
~/.claude/skills/ding-check -> ~/repos/dingcheck/skill/
```

## 📝 许可证

MIT License
