# 钉钉日会自动化系统 - 完全自动化指南

## ✅ 一次设置，永久自动化

### 📋 初次设置步骤（只需一次）

#### 1. 设置 Mac 自动唤醒
```bash
bash ~/dingtalk_checker/scripts/setup_auto_wake.sh
```
- 需要输入管理员密码
- 设置后，Mac 将每天 9:55 自动唤醒

#### 2. 登录钉钉（只需一次）
- Chrome 会自动启动（已配置为开机自动启动）
- 在 Chrome 中访问钉钉文档
- 手动登录一次
- **之后不要退出登录，Chrome 会保持会话**

#### 3. 验证自动化状态
```bash
bash ~/dingtalk_checker/scripts/check_status.sh
```

### 🔄 自动化工作流程

```
每天 9:55
    ↓
Mac 自动唤醒
    ↓
等待 5 分钟
    ↓
每天 10:00 - 定时任务触发
    ↓
run_daily_check.sh 启动
    ↓
1. prepare_chrome.py - 环境预检查
   - ✅ Chrome 进程运行
   - ✅ 有可用页面
   - ✅ 导航到钉钉
   - ✅ 检查登录状态
   - ✅ 刷新页面
    ↓
2. daily_check.py - 核心检查
   - 检查 6 个业务单元
   - 提取听记内容
   - AI 智能分析
    ↓
3. generate_pdf_report.py - 生成报告
   - 生成 TXT 报告
   - 生成 PDF 报告
    ↓
4. 发送通知
   - ✅ 成功："成功提取 X 个业务单元"
   - ❌ 失败："检查失败，请查看日志"
```

### 📊 报告位置

- **文本报告**：`~/dingtalk_checker/daily_reports/report_YYYY-MM-DD.txt`
- **PDF 报告**：`~/dingtalk_checker/daily_reports/report_YYYY-MM-DD.pdf`
- **日志文件**：`~/dingtalk_checker/logs/daily_check.log`

### 🔔 通知说明

#### 通知位置
- **Mac 通知中心**（屏幕右上角）
- 会有声音提示（Glass 音效）

#### 通知类型

1. **✅ 成功通知**
   ```
   标题：钉钉日会检查完成
   内容：成功提取 6 个业务单元的数据
   ```

2. **❌ 失败通知**
   ```
   标题：钉钉日会检查失败
   内容：Chrome 环境预检查失败，请检查 Chrome 是否运行和登录状态
   ```

3. **⚠️ 警告通知**
   ```
   标题：钉钉日会检查警告
   内容：所有业务单元均无数据
   ```

### 🛠️ 日常维护命令

#### 查看系统状态
```bash
bash ~/dingtalk_checker/scripts/check_status.sh
```

#### 手动运行一次
```bash
bash ~/dingtalk_checker/scripts/run_daily_check.sh
```

#### 查看最近日志
```bash
tail -50 ~/dingtalk_checker/logs/daily_check.log
```

#### 查看今天的报告
```bash
open ~/dingtalk_checker/daily_reports/
```

### ⚠️ 常见问题

#### 1. 收到"Chrome 环境预检查失败"通知
**原因**：Chrome 未运行或钉钉未登录

**解决**：
```bash
# 启动 Chrome 调试模式
bash ~/dingtalk_checker/chrome/start_chrome_debug.sh

# 在 Chrome 中重新登录钉钉
# 然后手动运行测试
bash ~/dingtalk_checker/scripts/run_daily_check.sh
```

#### 2. 收到"所有业务单元均无数据"通知
**原因**：钉钉表格里确实没有今天的数据

**解决**：这是正常情况，等数据填入后会自动提取

#### 3. Mac 在 10:00 时是关机状态
**后果**：定时任务不会执行

**解决**：
- 确保设置了自动唤醒（见上文）
- 或者保持 Mac 开机/睡眠状态

#### 4. 钉钉会话过期
**症状**：收到"未登录"的失败通知

**解决**：
- 打开 Chrome
- 重新登录钉钉
- 会话会保持数周或数月

### 📈 自动化维护周期

| 项目 | 频率 | 说明 |
|------|------|------|
| 重新登录钉钉 | 1-3个月 | 仅当会话过期时 |
| 检查系统状态 | 1周 | 运行 check_status.sh |
| 查看报告 | 每天 | 自动生成，随时查看 |
| 系统重启后 | 手动一次 | Chrome 自动启动，重新登录钉钉 |

### 🎯 完全自动化达成条件

✅ Mac 每天 9:55 自动唤醒
✅ Chrome 开机自动启动
✅ 钉钉保持登录状态
✅ 定时任务每天 10:00 执行
✅ 环境预检查确保状态正确
✅ 失败自动通知

**只要满足以上条件，系统可以无人值守运行数周甚至数月！** 🎉

### 📞 故障排查流程

1. 收到失败通知
   ↓
2. 运行状态检查
   ```bash
   bash ~/dingtalk_checker/scripts/check_status.sh
   ```
   ↓
3. 查看日志找原因
   ```bash
   tail -50 ~/dingtalk_checker/logs/daily_check.log
   ```
   ↓
4. 根据错误信息修复
   - Chrome 未运行 → 启动 Chrome
   - 未登录 → 重新登录钉钉
   - 无数据 → 等待数据填入
   ↓
5. 手动测试
   ```bash
   bash ~/dingtalk_checker/scripts/run_daily_check.sh
   ```

---

## 📝 更新日志

- **2026-03-03**: 添加 Chrome 环境预检查
- **2026-03-03**: 添加失败通知机制
- **2026-03-03**: 添加自动唤醒设置脚本
- **2026-03-03**: 添加系统状态检查工具
