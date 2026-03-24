# 钉钉早会检查器项目

自动检查钉钉文档中各业务单元的AI听记链接，提取会议内容，并进行AI智能分析。

## 📁 目录结构

```
dingtalk_checker/
├── scripts/              # 主要脚本
│   ├── daily_check.py   # 核心脚本：每日自动检查
│   ├── run_daily_check.sh
│   ├── start_chrome_debug.sh
│   └── 其他辅助脚本
│
├── tests/               # 测试脚本
│   ├── test_single.py  # 测试单个业务单元
│   ├── test_single_verbose.py  # 详细测试
│   └── 其他测试文件
│
├── docs/                # 文档
│   ├── AI_ANALYSIS_SETUP.md  # AI分析功能配置
│   ├── README_使用说明.md
│   ├── 项目完整指南.md
│   └── 定时任务安装说明.md
│
├── daily_reports/       # 每日生成的报告
│   ├── report_2026-03-02.txt
│   └── ...
│
├── chrome/              # Chrome调试相关
│   ├── chrome_debug_profile/
│   └── chrome_persistent_profile/
│
├── logs/                # 日志文件
│
├── archives/            # 废弃的旧脚本
│
├── .venv/               # Python虚拟环境
│
└── links_config.txt     # 配置文件

```

## 🚀 快速开始

### 1. 启动Chrome调试模式
```bash
cd ~/dingtalk_checker
./chrome/start_chrome_debug.sh
```

### 2. 运行每日检查
```bash
cd ~/dingtalk_checker
source .venv/bin/activate
python3 scripts/daily_check.py
```

### 3. 测试单个业务单元
```bash
cd ~/dingtalk_checker
source .venv/bin/activate
python3 tests/test_single.py "业务单元名称" "2026-03-02"
```

## ⚙️ 配置

### API密钥配置
```bash
export GEMINI_API_KEY='your-api-key'
```

### 自动任务
每天上午10:00自动运行，配置文件在：
`~/Library/LaunchAgents/com.dingtalk.dailycheck.plist`

## 📊 查看报告

```bash
cd ~/dingtalk_checker
cat daily_reports/report_2026-03-02.txt
```

## 📚 详细文档

请查看 `docs/` 目录下的文档文件。

---

**注意**：此项目依赖Chrome远程调试模式，使用前需要先启动Chrome。
