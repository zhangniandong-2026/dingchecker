# 安全警告：API Key已泄露

## ⚠️ 发生了什么

在2026年3月21日的commit `50abcc8`中，Gemini API Key被意外提交到了GitHub仓库。

**泄露的Key**: `[已打码的旧 Gemini API Key]`

**泄露位置**:
- docs/项目状态报告.md
- docs/代理配置说明.md
- scripts/run_daily_check.sh
- scripts/run_daily_check_v2.sh
- scripts/run-claude-gemini.sh

## ✅ 已采取的措施

1. **清理所有文件** - 已将所有硬编码的API Key替换为占位符
2. **创建模板文件** - 添加了 `.env.template` 指导用户配置
3. **更新.gitignore** - 确保不会再次提交敏感信息
4. **提交修复** - 将在下一次commit中删除所有API Key

## 🔥 必须立即执行的操作

### 1. 撤销泄露的API Key

**立即访问**: https://aistudio.google.com/app/apikey

操作步骤：
1. 找到并删除泄露的Key: `[已打码的旧 Gemini API Key]`
2. 创建新的API Key
3. 配置到环境变量（不要写在代码中！）

### 2. 配置新的API Key

```bash
# 添加到 ~/.zshrc
echo 'export GEMINI_API_KEY="your_new_api_key"' >> ~/.zshrc
source ~/.zshrc
```

### 3. 从Git历史中永久删除（可选但推荐）

如果想彻底清理Git历史：

```bash
# 使用 git-filter-repo（推荐）
pip install git-filter-repo
git filter-repo --replace-text <(echo "OLD_GEMINI_API_KEY==>REMOVED")

# 或使用 BFG Repo-Cleaner
# brew install bfg
# bfg --replace-text passwords.txt
```

⚠️ **警告**: 这会重写Git历史，需要force push！

### 4. 检查是否被滥用

访问 Google Cloud Console 检查API使用量是否异常：
https://console.cloud.google.com/apis/dashboard

## 📚 预防措施

1. **永远不要硬编码敏感信息**
2. **使用环境变量**
3. **定期检查**: `git log -p | grep -i "key\|token\|password"`
4. **使用pre-commit hook检测敏感信息**
5. **考虑使用git-secrets工具**

## 🛡️ 后续改进

- [ ] 安装git-secrets防止泄露
- [ ] 配置pre-commit检查
- [ ] 定期轮换API Key
- [ ] 使用Secret管理工具

## 参考资料

- [GitHub - Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [git-filter-repo](https://github.com/newren/git-filter-repo)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
