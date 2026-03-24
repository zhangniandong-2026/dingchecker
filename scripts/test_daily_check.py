#!/usr/bin/env python3
"""快速测试版本 - 只检查前3个业务单元"""
import asyncio
import sys
import os
from datetime import datetime, date

# 添加scripts目录到path
sys.path.insert(0, os.path.expanduser('~/dingtalk_checker/scripts'))

# 导入主模块
from daily_check import batch_check_auto, ALL_SHEETS

# 临时替换为只测试3个单元
import daily_check
original_sheets = daily_check.ALL_SHEETS
daily_check.ALL_SHEETS = original_sheets[:3]  # 只取前3个

print("🧪 快速测试模式 - 只检查前3个业务单元")
print(f"测试单元: {daily_check.ALL_SHEETS}")
print("="*80)
print()

if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime('%Y-%m-%d')
    asyncio.run(batch_check_auto(target_date))
