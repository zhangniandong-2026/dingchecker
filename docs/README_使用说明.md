# 钉钉 AI 听记链接提取与内容抓取工具

## 方案：Chrome 远程调试模式

### 第一步：启动 Chrome 远程调试模式（只需一次）

在终端运行：
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=~/chrome_debug_profile
```

启动后：
1. 在浏览器中登录钉钉文档
2. 打开目标表格页面：https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm
3. 点击左侧目录进入你需要的工作表（如"河南分战队"、"媒体军工组"等）
4. 保持浏览器窗口打开

### 第二步：提取链接或内容

#### 功能1：提取链接（get_link_from_current_page.py）

```bash
# 详细输出模式
source .venv/bin/activate
python get_link_from_current_page.py "2026-02-24"

# 快捷模式（直接打开链接）
./get_and_open.sh 2026-02-24
```

#### 功能2：提取正文内容（get_content.py）✨新增

```bash
source .venv/bin/activate
python get_content.py "2026-02-24"
```

**功能说明：**
- 自动查找指定日期的链接
- 跳转到 AI 听记页面
- 等待页面动态加载完成
- 提取并清理正文内容
- 如果没找到链接，返回 "无"
- 如果无权访问，返回 "无权限"

## 支持的表格格式

✅ **格式1**：链接列显示会议名称（如"2626.2.24河南早会"）
- 使用文本匹配策略

✅ **格式2**：链接列显示URL（如媒体军工组）
- 使用冻结列架构策略，通过行索引匹配

## 使用示例

```bash
# 1. 只提取链接
python get_link_from_current_page.py "2026-02-24"

# 2. 提取链接并打开
./get_and_open.sh 2026-02-24

# 3. 提取正文内容
python get_content.py "2026-02-24"
```

## 输出示例

### 提取链接成功：
```
找到链接: https://shanji.dingtalk.com/app/transcribes/...
```

### 提取内容成功：
```
结果: 内容已提取（2036 字符）
============================================================

完整内容:

AI 纪要
主题: 项目进展与行业运营规划
时间: 2026-02-25 08:30:26
参与人: 徐鑫, 崔贵海, 韩齐, 韩昕哲, 阿镇, 陈永海
...
```

### 未找到链接：
```
结果: 无
```

### 无权访问：
```
结果: 无权限
```

## 注意事项

1. Chrome 远程调试窗口需要保持打开
2. 切换不同的工作表时，需要在浏览器中手动点击左侧目录
3. 脚本会自动识别表格格式并使用对应的匹配策略
4. 内容提取会自动清理页面导航元素，只保留正文
5. 如果找不到链接或内容，检查：
   - Chrome 是否在远程调试模式运行
   - 浏览器是否在正确的工作表页面
   - 日期格式是否正确（YYYY-MM-DD）
   - 是否有该日期的听记权限

## 文件说明

- `get_content.py` - **主要功能**：提取指定日期的AI听记正文内容
- `get_link_from_current_page.py` - 从当前页面提取链接
- `get_and_open.sh` - 快捷脚本，提取并自动打开链接
- `get_link.py` - 备用方案，使用配置文件（手动维护）
- `links_config.txt` - 配置文件示例
- `README_使用说明.md` - 本文档

## 自动化定时任务 ✨新增

### 功能4：每日自动检查（daily_check.py）

每天上午10点自动执行，检查所有32个业务单元的AI听记执行情况，生成日报。

**快速安装：**
```bash
# 1. 一键安装定时任务
./install_schedule.sh

# 2. (可选) 设置Chrome开机自启动
cp ~/com.chrome.debugmode.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.chrome.debugmode.plist
```

**手动启动Chrome：**
```bash
./start_chrome_debug.sh
```

**查看执行日志：**
```bash
tail -f ~/daily_check.log
```

**详细说明：** 查看 `定时任务安装说明.md`

## 技术说明

### 内容提取流程：
1. 在表格页面查找指定日期的 shanji 链接
2. 创建新标签页访问链接
3. 等待页面动态加载（含 .canvas-editor 等容器）
4. 检查访问权限
5. 提取正文内容并清理无关元素（导航、按钮等）
6. 返回纯净的会议纪要内容

### 支持的内容清理：
- 自动移除页面导航元素
- 移除AI问答、分享按钮等交互元素
- 移除时间戳、播放控制等媒体元素
- 保留核心会议纪要内容（主题、时间、参与人、正文、待办等）

