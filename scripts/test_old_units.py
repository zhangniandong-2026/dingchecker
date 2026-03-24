#!/usr/bin/env python3
"""测试原来成功的单元"""
import asyncio
import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.expanduser('~/dingtalk_checker/scripts'))

from daily_check import batch_check_auto
import daily_check

# 只测试原来成功的2个单元
daily_check.ALL_SHEETS = ['政府行业一组', '政府行业二组']

print("🧪 测试原来成功的单元")
print(f"测试单元: {daily_check.ALL_SHEETS}")
print("="*80)
print()

if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime('%Y-%m-%d')
    asyncio.run(batch_check_auto(target_date))
