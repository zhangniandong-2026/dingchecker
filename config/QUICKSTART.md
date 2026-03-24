# 业务单元配置 - 快速上手

## 🚀 5分钟快速开始

### 1. 查看当前配置

```bash
bash ~/dingtalk_checker/scripts/manage_units.sh list
```

### 2. 添加新业务单元

```bash
# 方法1：交互式添加
bash ~/dingtalk_checker/scripts/manage_units.sh add

# 方法2：直接添加
bash ~/dingtalk_checker/scripts/manage_units.sh add "金融组"
```

### 3. 编辑配置文件

```bash
bash ~/dingtalk_checker/scripts/manage_units.sh edit
```

## 📝 常用命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `list` | 列出所有单元 | `bash manage_units.sh list` |
| `add` | 添加新单元 | `bash manage_units.sh add "新单元"` |
| `edit` | 编辑配置 | `bash manage_units.sh edit` |
| `show` | 显示文件内容 | `bash manage_units.sh show` |
| `backup` | 备份配置 | `bash manage_units.sh backup` |
| `reset` | 重置为默认 | `bash manage_units.sh reset` |

## 💡 使用技巧

### 快速添加多个单元

```bash
cd ~/dingtalk_checker/scripts

# 添加多个单元
./manage_units.sh add "金融组"
./manage_units.sh add "医疗组"
./manage_units.sh add "教育组"
```

### 分组管理

编辑配置文件，用注释分组：

```txt
# 核心业务
媒体军工组
交通行业组

# 政府行业
政府行业一组
政府行业二组

# 新兴领域
金融组
医疗组
```

### 临时禁用单元

在单元名称前加 `#`：

```txt
媒体军工组
# 交通行业组  ← 临时禁用
政府行业一组
```

### 验证配置

运行检查时会显示加载的单元数：

```bash
python3 ~/dingtalk_checker/scripts/daily_check.py

# 输出：
# ✓ 从配置文件加载了 10 个业务单元
```

## 🔧 配置文件位置

- **配置文件**：`~/dingtalk_checker/config/business_units.txt`
- **说明文档**：`~/dingtalk_checker/config/README.md`
- **管理工具**：`~/dingtalk_checker/scripts/manage_units.sh`

## ✅ 完整工作流程

### 场景1：添加新业务单元

```bash
# 1. 查看当前配置
bash ~/dingtalk_checker/scripts/manage_units.sh list

# 2. 备份配置（可选）
bash ~/dingtalk_checker/scripts/manage_units.sh backup

# 3. 添加新单元
bash ~/dingtalk_checker/scripts/manage_units.sh add "金融组"

# 4. 验证配置
bash ~/dingtalk_checker/scripts/manage_units.sh list

# 5. 测试运行
python3 ~/dingtalk_checker/scripts/daily_check.py 2026-03-03
```

### 场景2：批量修改

```bash
# 1. 备份
bash ~/dingtalk_checker/scripts/manage_units.sh backup

# 2. 编辑
bash ~/dingtalk_checker/scripts/manage_units.sh edit

# 3. 保存后验证
bash ~/dingtalk_checker/scripts/manage_units.sh list
```

### 场景3：恢复配置

```bash
# 如果改错了，恢复最近的备份
bash ~/dingtalk_checker/scripts/manage_units.sh restore
```

## ⚠️ 注意事项

1. **单元名称必须完全一致**
   - 与钉钉文档中的工作表名称一字不差
   - 区分大小写
   - 不能有多余空格

2. **文件编码**
   - 必须是 UTF-8 编码
   - 使用 `manage_units.sh edit` 自动处理

3. **备份习惯**
   - 重大修改前先备份
   - 自动备份文件保留时间戳

4. **性能考虑**
   - 10个以内：快速
   - 10-20个：正常
   - 20个以上：需要更多时间

## 🎯 实战示例

### 从6个扩展到12个单元

```bash
cd ~/dingtalk_checker/scripts

# 1. 备份现有配置
./manage_units.sh backup

# 2. 添加新单元
./manage_units.sh add "金融组"
./manage_units.sh add "医疗组"
./manage_units.sh add "教育组"
./manage_units.sh add "零售组"
./manage_units.sh add "科技组"
./manage_units.sh add "制造组"

# 3. 查看结果
./manage_units.sh list

# 4. 测试运行
cd ~/dingtalk_checker
python3 scripts/daily_check.py 2026-03-03
```

### 按优先级重新排序

```bash
# 编辑配置文件
bash ~/dingtalk_checker/scripts/manage_units.sh edit

# 把重要的单元放在前面，例如：
# 1. 政府行业一组  ← 最重要
# 2. 交通行业组
# 3. 央企组
# ...
# 10. 其他组       ← 不太重要

# 保存后，检查会按这个顺序执行
```

## 📞 故障排除

### Q: 添加单元后没有效果？

```bash
# 检查配置是否正确
bash ~/dingtalk_checker/scripts/manage_units.sh show

# 验证 Python 是否正确加载
python3 -c "
import sys
sys.path.insert(0, '/Users/zhangniandong/dingtalk_checker/scripts')
from daily_check import ALL_SHEETS
print(f'已加载 {len(ALL_SHEETS)} 个单元')
print(ALL_SHEETS)
"
```

### Q: 配置文件损坏？

```bash
# 恢复最近的备份
bash ~/dingtalk_checker/scripts/manage_units.sh restore

# 或者重置为默认
bash ~/dingtalk_checker/scripts/manage_units.sh reset
```

### Q: 单元名称不确定？

打开钉钉文档，底部标签的名称就是单元名称：

```
[媒体军工组] [交通行业组] [政府行业一组] ...
     ↑              ↑              ↑
   这些就是单元名称，复制粘贴到配置文件
```

## 🎉 快速参考

**最常用的3个命令**：

```bash
# 1. 列出单元
bash ~/dingtalk_checker/scripts/manage_units.sh list

# 2. 添加单元
bash ~/dingtalk_checker/scripts/manage_units.sh add "新单元"

# 3. 编辑配置
bash ~/dingtalk_checker/scripts/manage_units.sh edit
```

**配置文件路径**：`~/dingtalk_checker/config/business_units.txt`

**支持命令简写**：

```bash
./manage_units.sh ls      # = list
./manage_units.sh e       # = edit
./manage_units.sh bak     # = backup
```

---

**更多信息**：查看 `~/dingtalk_checker/config/README.md`
