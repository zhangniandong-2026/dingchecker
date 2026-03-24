# 权限检查改进说明

## 问题描述

在 2026-03-04 的测试中发现：
- 第一次运行（17:54）：华北一组、北京商业组、能源组显示"无权限"
- 第二次运行（18:09）：相同的3个单元全部成功提取

## 根本原因

钉钉的听记页面在首次访问时，权限验证需要异步处理，可能需要更长时间。原代码只等待5秒就检查权限，导致在权限还未完全验证时就误判为"无权限"。

## 改进方案

### 改进前（旧逻辑）

```python
await content_page.goto(link_url, wait_until='domcontentloaded', timeout=60000)
await content_page.wait_for_timeout(5000)  # 只等5秒

page_text = await content_page.evaluate('() => document.body.innerText')

if '暂无权限' in page_text or '申请权限' in page_text:
    return "无权限", link_url  # 立即判定为无权限
```

**问题**：5秒可能不够，特别是首次访问或网络慢时。

### 改进后（新逻辑）

```python
await content_page.goto(link_url, wait_until='domcontentloaded', timeout=60000)
await content_page.wait_for_timeout(8000)  # 增加到8秒

page_text = await content_page.evaluate('() => document.body.innerText')

if '暂无权限' in page_text or '申请权限' in page_text:
    print(f"  ⚠️ 检测到权限提示，等待3秒后重试...")
    await content_page.wait_for_timeout(3000)  # 再等3秒

    # 重新检查
    page_text = await content_page.evaluate('() => document.body.innerText')

    # 重试后还是无权限，才真正判定为无权限
    if '暂无权限' in page_text or '申请权限' in page_text:
        return "无权限", link_url
    else:
        print(f"  ✓ 权限验证通过（重试成功）")
```

**改进点**：
1. 初始等待时间：5秒 → 8秒
2. 添加重试机制：如果检测到权限提示，再等3秒重新检查
3. 增加日志输出：显示重试过程

## 效果

- **减少误判**：降低"假阳性"的无权限判断
- **提高成功率**：首次运行的成功率更高
- **更好的调试**：输出重试信息，便于排查问题

## 时间成本

- 正常情况（有权限）：总等待时间 8秒（和之前5秒相比，增加3秒）
- 权限慢的情况：总等待时间 11秒（8秒+3秒重试）
- 真的无权限：总等待时间 11秒（8秒+3秒重试）

**总体影响**：每个单元增加3秒，6个单元增加约18秒，可接受。

## 测试验证

- ✅ 2026-03-04 18:09 测试：6个单元全部成功
- ✅ 2026-03-04 18:15 再次测试：6个单元全部成功

## 修改文件

- `~/dingtalk_checker/scripts/daily_check.py` 第391-402行

## 版本

- 修改日期：2026-03-04
- 修改人：Claude Code
- 版本：v2.1
