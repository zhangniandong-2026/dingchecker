#!/usr/bin/env python3
"""可视化调试工具 - 详细显示每个步骤"""
import asyncio
import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.expanduser('~/dingtalk_checker/scripts'))

from daily_check import batch_check_auto
import daily_check

# 只测试第一个单元
daily_check.ALL_SHEETS = ['政府行业一组']

print("="*80)
print("🔍 可视化调试模式 - 详细追踪每个步骤")
print("="*80)
print(f"\n测试单元: {daily_check.ALL_SHEETS}")
print("="*80)
print()

if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime('%Y-%m-%d')
    asyncio.run(batch_check_auto(target_date))
