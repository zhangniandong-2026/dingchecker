# ding-check Skill 配置指南

## 快速开始

### 1. 配置 Gemini API Key（必需）

Skill 需要 Gemini API Key 来进行 AI 智能分析。有三种配置方式：

#### 方式 1：环境变量（推荐，临时有效）

```bash
export GEMINI_API_KEY='your-api-key-here'
```

适合：测试或临时使用

#### 方式 2：配置文件（推荐，持久化）

```bash
# 复制示例配置
cp config.example.sh config.sh

# 编辑配置文件，填入您的 API Key
# config.sh 会被自动加载
```

适合：长期使用，skill 专用配置

#### 方式 3：Shell 配置文件（全局有效）

```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
echo "export GEMINI_API_KEY='your-api-key-here'" >> ~/.zshrc
source ~/.zshrc
```

适合：全局使用，所有项目共享

### 2. 获取 API Key

访问：https://aistudio.google.com/app/apikey

免费版额度：
- 每分钟 15 次请求
- 每天 1500 次请求

### 3. 首次运行配置

如果未配置 API Key，首次运行时会提示引导配置：

```bash
/ding-check

# 会提示：
⚠️  未找到 Gemini API Key

💡 配置方式（三选一）：
...

是否现在配置？(y/n)
```

选择 `y` 后输入 API Key，会自动保存到 `config.sh`。

## 配置优先级

1. **环境变量** `GEMINI_API_KEY` - 最高优先级
2. **配置文件** `~/.claude/skills/ding-check/config.sh` - 次优先级
3. **交互式配置** - 首次运行时提示

## 安全说明

- `config.sh` 文件权限自动设置为 `600`（仅用户可读写）
- 不要将包含真实 API Key 的 `config.sh` 提交到 Git
- 可以安全分享 `config.example.sh` 模板文件

## 无 API Key 使用

如果不配置 API Key，skill 仍可正常运行，但会跳过 AI 分析：

- ✅ 数据提取正常
- ✅ 生成文本报告
- ✅ 生成 PDF 报告
- ✅ 生成 HTML 可视化报告
- ⚠️ 跳过 AI 智能分析部分

## 其他配置

### 代理设置

如果需要通过代理访问 Gemini API，可在 `config.sh` 中添加：

```bash
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
```

### 钉钉文档 URL

修改 `skill.sh` 第 28 行：

```bash
DINGTALK_URL="your-dingtalk-url-here"
```

## 故障排查

### 问题：提示 "未找到 API Key"

**解决**：
1. 检查环境变量：`echo $GEMINI_API_KEY`
2. 检查配置文件：`cat ~/.claude/skills/ding-check/config.sh`
3. 尝试重新配置：删除 `config.sh` 后重新运行

### 问题：API 调用失败

**解决**：
1. 验证 API Key 有效性
2. 检查网络连接和代理设置
3. 查看是否超出免费额度限制

### 问题：配置文件权限错误

**解决**：
```bash
chmod 600 ~/.claude/skills/ding-check/config.sh
```

## 分享给其他用户

如果要将 skill 分享给其他用户：

1. **分享文件**：
   - `skill.sh` - 主脚本
   - `SKILL.md` - 使用文档
   - `config.example.sh` - 配置示例
   - `README.md` - 本文件

2. **不要分享**：
   - `config.sh` - 包含您的 API Key

3. **用户配置步骤**：
   - 复制 `config.example.sh` 为 `config.sh`
   - 填入自己的 API Key
   - 运行 `/ding-check` 开始使用

## 更多帮助

运行查看完整文档：
```bash
/ding-check help
```

或查看：`SKILL.md`
