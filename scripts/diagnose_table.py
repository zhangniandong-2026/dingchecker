#!/usr/bin/env python3
"""诊断：查看程序实际看到的表格内容"""
import asyncio
from playwright.async_api import async_playwright
import re

async def diagnose():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = browser.contexts[0].pages[0]

        # 导航到主页面
        main_url = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"
        await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)

        # 测试单元：政府行业一组
        unit_name = "政府行业一组"
        target_date = "2026-03-03"

        print("="*80)
        print(f"诊断：{unit_name} - 查找 {target_date}")
        print("="*80)

        # 1. 点击单元
        print(f"\n1. 点击 {unit_name}...")
        frames = page.frames
        for frame in frames:
            try:
                result = await frame.evaluate(f'''
                    () => {{
                        const element = document.evaluate(
                            `//*[text()="{unit_name}"]`,
                            document,
                            null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE,
                            null
                        ).singleNodeValue;
                        if (element) {{
                            element.click();
                            return true;
                        }}
                        return false;
                    }}
                ''')
                if result:
                    print("   ✓ 已点击")
                    await page.wait_for_timeout(5000)
                    break
            except:
                pass

        # 2. 查找表格Frame
        print(f"\n2. 查找表格...")
        table_frame = None
        for frame in page.frames:
            try:
                content = await frame.content()
                if '提交日期' in content and 'AI听记' in content:
                    table_frame = frame
                    print("   ✓ 找到表格Frame")
                    break
            except:
                pass

        if not table_frame:
            print("   ✗ 未找到表格")
            return

        # 3. 提取所有文本
        print(f"\n3. 提取表格内容...")
        text = await table_frame.evaluate('() => document.body.innerText')

        # 4. 查找所有日期
        dates = re.findall(r'(202[0-9]-[0-1][0-9]-[0-3][0-9])', text)
        unique_dates = sorted(set(dates), reverse=True)

        print(f"   找到 {len(unique_dates)} 个唯一日期:")
        for d in unique_dates[:20]:
            count = dates.count(d)
            marker = " ← 目标" if d == target_date else ""
            print(f"     {d} (出现{count}次){marker}")

        # 5. 如果找到目标日期，查看其周围内容
        if target_date in text:
            print(f"\n   ✓ 找到目标日期 {target_date}")

            # 查找目标日期周围的内容
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if target_date in line:
                    print(f"\n   第 {i} 行及前后5行:")
                    start = max(0, i-5)
                    end = min(len(lines), i+6)
                    for j in range(start, end):
                        marker = " ← " if j == i else "    "
                        print(f"     {j:4d}{marker}{lines[j][:80]}")
                    break
        else:
            print(f"\n   ✗ 未找到目标日期 {target_date}")

        # 6. 查找听记链接
        urls = re.findall(r'(https://shanji\.dingtalk\.com/[^\s<>"\']+)', text)
        print(f"\n4. 听记链接:")
        if urls:
            print(f"   找到 {len(urls)} 个链接:")
            for i, url in enumerate(urls[:5], 1):
                print(f"     {i}. {url[:70]}...")
        else:
            print(f"   ✗ 未找到任何听记链接")

        # 7. 查看表格结构（前30行）
        print(f"\n5. 表格前30行内容:")
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for i, line in enumerate(lines[:30], 1):
            print(f"     {i:2d}. {line[:100]}")

        print("\n" + "="*80)

asyncio.run(diagnose())
