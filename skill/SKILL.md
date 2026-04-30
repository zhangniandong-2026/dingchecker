---
name: ding-checker
description: DingTalk daily meeting quality analysis with a fixed summary document. Opens the fixed DingTalk AI transcript summary page, lets managers manually open the transcript pages they want to analyze, then extracts transcripts and generates JSON/HTML reports.
---

# DingTalk Daily Check Skill

自动化分析钉钉日会听记内容，提取业务单元转写，生成业务单元横向比较报告。

默认推荐使用 `collect` 半自动模式：系统自动打开固定钉钉 AI 听记汇总页，管理者只需要在浏览器里手动点击想分析的 AI 听记链接，dingchecker 负责后续的转写提取、质量评分和 HTML 报告生成。

## 核心特性

- 🔗 **固定汇总页**：所有人默认使用同一个钉钉 AI 听记汇总页，无需提供链接
- 🧭 **半自动收集（推荐）**：自动打开汇总页，管理者人工点击要分析的听记页
- 🤖 **自动分析**：自动提取转写、识别业务单元、AI 评分并生成报告
- 🎯 **交互式选择**：灵活选择要检查的业务单元（全部、按战队、部分）
- 📊 **HTML/JSON 报告**：默认生成结构化 JSON 和可视化 HTML，TXT/PDF 仅兼容保留
- 🔍 **风险检测**：自动识别关键风险点
- 📅 **历史管理**：查看、搜索历史报告
- ⚡ **实时反馈**：清晰的执行状态和错误提示

## 快速开始

### 推荐使用方式

```bash
/ding-check collect 华北东北战区
```

**执行流程**：
1. ✓ 自动启动Chrome调试模式（如未运行）
2. ✓ 自动打开固定的钉钉 AI 听记汇总页
3. ✓ 管理者在浏览器中筛选日期，手动点击想分析的 AI 听记链接
4. ✓ dingchecker 收集已打开的听记页并识别业务单元
5. ✓ 提取转写、AI 评分并生成 HTML 横向比较报告

## 使用方法

### 1. 推荐：半自动收集已打开听记页

```bash
# 检查今天
/ding-check collect 华北东北战区

# 检查指定日期
/ding-check collect 华北东北战区 2026-04-21
```

系统会自动打开固定汇总页：

```text
https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm
```

管理者只需要：

- 在汇总页筛选或定位当天日期
- 人工判断哪些业务单元今天实际开会
- 手动点击这些业务单元的 AI 听记链接
- 确认听记页能正常打开且有权限
- 回到对话或终端继续，让 dingchecker 自动生成报告

### 2. 兼容：全自动检查功能（不推荐作为默认）

```bash
# 检查今天（弹出菜单选择单元）
/ding-check

# 检查指定日期（也会弹出菜单）
/ding-check 2026-03-02
```

全自动模式会尝试自动切换钉钉工作表、定位日期行和听记链接。由于钉钉文档 DOM 和权限状态不稳定，日常管理建议优先使用 `collect`。

**交互式菜单示例**：
```
🔍 选择要检查的业务单元

[1] 全部检查（33个单元）

按战队分组：
[2] 华北东北战区（7个单元）
[3] 政府头部战队（4个单元）
[4] 能源央企头部战队（2个单元）

单个业务单元：
  • 北京非金一组
  • 北京非金二组
  • 北京金融分战队
  • 东北组
  • 华北一组
  • 华北二组
  • 北京商业组
  • 媒体军工组
  • 交通行业组
  • 政府行业一组
  • 政府行业二组
  • 能源组
  • 央企组

请选择：
  - 输入数字选择快捷选项（如：1 表示全部，2 表示第一个战队）
  - 输入单元名称（逗号分隔）选择特定单元
  - 按 Enter 检查全部

您的选择: _
```

**选择示例**：
- 输入 `1` - 检查所有33个单元
- 输入 `2` - 检查华北东北战区的7个单元
- 输入 `北京非金一组,东北组` - 只检查这两个单元
- 直接按Enter - 默认检查所有单元

### 3. 查看历史报告

```bash
# 查看今天的报告
/ding-check view

# 查看昨天的报告
/ding-check view 昨天

# 查看指定日期
/ding-check view 2026-03-02
```

### 4. 搜索报告内容

在所有历史报告中搜索关键词：

```bash
# 搜索包含"风险"的内容
/ding-check search 风险

# 搜索未完成的任务
/ding-check search 未完成

# 搜索特定业务单元
/ding-check search 北京非金
```

### 5. 列出历史报告

```bash
/ding-check list
```

显示所有历史报告的列表，包括日期、标题和文件类型。

### 6. 检查系统状态

```bash
/ding-check status
```

检查：
- 项目目录和脚本是否存在
- Chrome调试模式是否运行
- Python依赖是否安装
- 业务单元配置
- 历史报告数量
- 固定URL配置

## 前置条件

### 1. Chrome调试模式（自动启动）

Skill会**自动启动**Chrome调试模式，无需手动运行！

如果需要手动启动：
```bash
bash ~/dingtalk_checker/chrome/start_chrome_debug.sh
```

**检查是否运行**：
```bash
/ding-check status
```

### 2. Python依赖

需要安装以下Python包：
- `playwright` - 浏览器自动化
- `pandas` - 数据处理
- `reportlab` - PDF生成

```bash
# 安装依赖
cd ~/dingtalk_checker
pip3 install -r requirements.txt

# 安装playwright浏览器
playwright install chromium
```

### 3. 项目结构

```
~/dingtalk_checker/
├── scripts/
│   ├── daily_check.py           # 检查核心脚本
│   ├── generate_pdf_report.py   # PDF生成
│   └── run_daily_check.sh       # 定时任务脚本（skill不使用）
├── config/
│   └── business_units.txt       # 业务单元配置
├── daily_reports/               # 报告输出目录
├── chrome/
│   └── start_chrome_debug.sh    # Chrome启动脚本
└── requirements.txt
```

## 配置说明

### 固定URL

URL固定配置在skill中：
```bash
DINGTALK_URL="https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm..."
```

**修改URL**：编辑 `~/.claude/skills/ding-check/skill.sh` 的第22行。

### 业务单元配置

配置文件：`~/dingtalk_checker/config/business_units.txt`

```
# 华北东北战区
北京非金一组
北京非金二组
北京金融分战队
东北组
华北一组
华北二组
北京商业组

# 政府头部战队
媒体军工组
交通行业组
政府行业一组
政府行业二组

# 能源央企头部战队
能源组
央企组
```

**注释行（#开头）**：表示战队分组，用于交互式菜单中的快捷选项。

## 工作原理

### 检查流程

1. **Chrome管理**：
   - 检测Chrome是否在调试模式运行
   - 如未运行，自动启动并等待5秒
   - 验证启动成功

2. **URL打开**：
   - 使用Playwright通过CDP连接Chrome
   - 打开固定的钉钉文档URL
   - 等待页面加载完成

3. **交互式选择**：
   - 解析配置文件，提取战队和单元信息
   - 显示交互式菜单
   - 用户选择要检查的单元

4. **临时配置**：
   - 备份原配置文件
   - 创建临时配置（只包含选择的单元）
   - 使用trap确保异常退出时恢复配置

5. **数据提取**：
   - 调用 `daily_check.py` 提取选择的单元数据
   - 清洗和格式化数据
   - 识别关键风险点

6. **报告生成**：
   - 恢复原配置文件
   - 生成文本报告（`.txt`）
   - 生成PDF报告（`.pdf`）
   - 自动打开PDF

### 报告格式

**文件命名**：
- 文本：`report_2026-03-02.txt`
- PDF：`report_2026-03-02.pdf`

**内容结构**：
```
===============================================
钉钉日会听记检查 - 2026-03-02
===============================================

检查时间: 2026-03-02 15:30:45
业务单元数: 3

【业务单元1】北京非金一组
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
今日工作:
- 完成需求评审
- 更新产品文档

明日计划:
- 开始新功能设计
- 会议：产品规划讨论

风险/问题:
- 需求变更频繁

【业务单元2】东北组
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
```

## 错误处理

### Chrome启动失败

```
❌ Chrome启动失败
```

**解决**：
- 检查 `~/dingtalk_checker/chrome/start_chrome_debug.sh` 是否存在
- 手动运行启动脚本测试
- 查看Chrome是否已在其他端口运行

### 未找到数据

```
⚠️  未找到 2026-03-02 的数据

💡 可能的原因：
   1. 今天还没有数据
   2. 页面中没有识别到有效的业务单元
   3. 数据提取失败
```

**解决**：
- 确认钉钉文档中有对应日期的数据
- 检查业务单元名称是否与工作表名称匹配
- 尝试其他日期：`/ding-check view 2026-03-01`

### 页面打开失败

```
❌ 页面打开失败
✗ 打开页面失败: Timeout 60000ms exceeded
```

**解决**：
- 检查网络连接
- 确认URL是否可访问
- 检查代理设置（skill使用7890端口）
- 增加超时时间（修改skill.sh中的timeout值）

### Python依赖缺失

```
✗ playwright
✗ reportlab
```

**解决**：
```bash
cd ~/dingtalk_checker
pip3 install -r requirements.txt
playwright install chromium
```

### 配置文件损坏

如果skill异常退出导致配置文件未恢复：

```bash
# 查找备份文件
ls -la ~/dingtalk_checker/config/business_units.txt.bak.*

# 恢复最新备份
cp ~/dingtalk_checker/config/business_units.txt.bak.xxxxx \
   ~/dingtalk_checker/config/business_units.txt
```

## 高级用法

### 自定义报告格式

修改 `~/dingtalk_checker/scripts/generate_pdf_report.py` 可以自定义PDF样式：
- 字体和颜色
- 页面布局
- 标题格式

### 修改固定URL

编辑 `~/.claude/skills/ding-check/skill.sh` 第22行：
```bash
DINGTALK_URL="your_new_url_here"
```

### 批量检查多天

虽然skill不直接支持批量操作，但可以通过循环实现：

```bash
# 检查最近7天
for i in {0..6}; do
    date=$(date -v-${i}d +%Y-%m-%d 2>/dev/null)
    /ding-check "$date"
    # 在交互式菜单中选择要检查的单元
done
```

### 集成到其他工具

报告是标准的文本和PDF格式，可以：
- 发送到邮件
- 上传到云存储
- 集成到CI/CD流程
- 导入到项目管理工具

## 与定时任务的关系

### Skill vs 定时任务

**Skill（手动检查）**：
- 交互式选择单元
- 灵活选择日期
- 自动启动Chrome
- 临时修改配置
- 适合随时手动检查

**定时任务（自动运行）**：
- 使用 `scripts/run_daily_check.sh`
- 每天9:40自动运行
- 检查配置文件中的所有单元
- 不修改配置文件
- 适合每日固定检查

**两者独立运行，互不影响！**

## 常见问题

### Q: 为什么URL是固定的？

A: 根据用户实际使用场景，总是检查同一个钉钉文档。固定URL可以简化操作，避免每次输入。如需修改，编辑skill.sh即可。

### Q: 可以同时运行多个检查吗？

A: 不建议。因为所有检查都使用同一个Chrome实例和配置文件，并发运行可能导致数据混乱。

### Q: 报告保存在哪里？

A: `~/dingtalk_checker/daily_reports/`目录，按日期命名。

### Q: 如何删除旧报告？

A: 直接删除 `daily_reports/` 目录下的文件即可，不影响skill运行。

### Q: 交互式选择会影响定时任务吗？

A: 不会。Skill使用临时配置文件，并在检查完成后自动恢复。定时任务使用原始配置文件。

### Q: 为什么需要代理？

A: 因为使用Gemini API进行报告分析，需要通过代理访问。代理配置在skill中（7890端口）。

### Q: 检查失败但没有明确错误信息？

A: 查看详细日志：
```bash
cd ~/dingtalk_checker
tail -f logs/daily_check.log
```

### Q: Chrome自动启动后浏览器窗口关闭了会怎样？

A: Chrome调试模式在后台运行，关闭窗口不影响。如需重启，skill会自动检测并重新启动。

## 技术细节

### 依赖的底层脚本

- `daily_check.py` - Python核心检查逻辑（支持日期参数）
- `generate_pdf_report.py` - PDF生成
- `chrome/start_chrome_debug.sh` - Chrome启动
- `run_daily_check.sh` - 定时任务使用（skill不使用）

### 数据流

```
固定URL
  ↓
ensure_chrome_debug() - 自动启动Chrome
  ↓
open_dingtalk_url() - 打开钉钉文档
  ↓
select_units_interactive() - 交互式选择单元
  ↓
创建临时配置文件
  ↓
daily_check.py 提取数据
  ↓
恢复原配置文件
  ↓
生成文本报告 (.txt)
  ↓
generate_pdf_report.py
  ↓
生成PDF报告 (.pdf) + 自动打开
```

### 关键技术

- **Chrome DevTools Protocol (CDP)**：远程控制Chrome
- **Playwright**：现代化浏览器自动化
- **Bash trap机制**：确保配置文件恢复
- **关联数组（declare -A）**：解析战队和单元关系
- **临时文件+PID**：避免并发冲突

### 配置安全机制

使用trap确保配置文件恢复：
```bash
cleanup_config() {
    if [[ -n "$config_backup" ]] && [[ -f "$config_backup" ]]; then
        mv "$config_backup" "$CONFIG_FILE"
    fi
}

trap cleanup_config EXIT INT TERM
```

即使skill异常退出（Ctrl+C、错误退出等），配置文件也会自动恢复。

## 更新历史

- **v3.0** (2026-03-05)
  - 固定URL配置
  - 自动启动Chrome
  - 交互式业务单元选择
  - 按战队分组显示
  - 临时配置+trap机制
  - 与定时任务完全隔离
  - 改进错误处理

- **v2.0** (2026-03-03)
  - 重新设计命令结构
  - 默认使用智能模式
  - URL作为参数
  - 新增status命令

- **v1.0** (Initial)
  - 基础功能实现
  - 固定模式检查
