#!/usr/bin/env python3
"""查看点击业务单元后表格中的所有日期"""
import asyncio
import re
from playwright.async_api import async_playwright

async def check_table_dates():
    """点击业务单元，查看表格中所有日期"""

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]

            print("="*80)
            print("查看业务单元表格中的日期")
            print("="*80)

            # 导航到主页面
            main_url = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"
            print(f"\n1. 导航到主页面...")
            await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)

            # 测试单元：使用之前成功的"政府行业一组"
            test_units = ["政府行业一组", "安徽组", "移动组"]

            for unit_name in test_units:
                print(f"\n{'='*80}")
                print(f"测试: {unit_name}")
                print(f"{'='*80}")

                # 查找并点击
                print(f"  1. 查找链接...")
                frames = page.frames
                clicked = False

                for frame in frames:
                    try:
                        element = await frame.query_selector(f'text="{unit_name}"')
                        if element:
                            print(f"     ✓ 在某个frame中找到")
                            await element.click()
                            await page.wait_for_timeout(5000)
                            clicked = True
                            break
                    except:
                        pass

                if not clicked:
                    print(f"     ✗ 未找到链接")
                    continue

                print(f"  2. 查找表格...")
                # 查找包含表格的frame
                table_frame = None
                frames = page.frames

                for frame in frames:
                    try:
                        content = await frame.content()
                        if '提交日期' in content or 'AI听记' in content or '链接' in content:
                            table_frame = frame
                            print(f"     ✓ 找到包含表格的frame")
                            break
                    except:
                        pass

                if not table_frame:
                    print(f"     ✗ 未找到表格")
                    # 返回主页面
                    await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(2000)
                    continue

                # 提取所有文本
                print(f"  3. 提取表格内容...")
                text = await table_frame.evaluate('() => document.body ? document.body.innerText : ""')

                # 查找所有日期
                dates = re.findall(r'(202[0-9]-[0-1][0-9]-[0-3][0-9])', text)
                unique_dates = sorted(set(dates), reverse=True)

                if unique_dates:
                    print(f"     ✓ 找到 {len(unique_dates)} 个日期:")
                    for date in unique_dates:
                        count = dates.count(date)
                        print(f"        {date} ({count}次)")
                else:
                    print(f"     ⚠ 未找到任何日期")

                # 查找表格中的所有文本内容（前30行）
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                print(f"\n  4. 表格内容前30行:")
                for i, line in enumerate(lines[:30], 1):
                    print(f"     {i:2d}. {line[:70]}")

                # 查找链接
                print(f"\n  5. 查找听记链接...")
                urls = re.findall(r'(https://shanji\.dingtalk\.com/[^\s<>"\']+)', text)
                if urls:
                    print(f"     ✓ 找到 {len(urls)} 个听记链接")
                    for i, url in enumerate(urls[:3], 1):
                        print(f"        {i}. {url[:80]}...")
                else:
                    print(f"     ⚠ 未找到听记链接")

                # 返回主页面准备下一个
                print(f"\n  6. 返回主页面...")
                await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(2000)

            print("\n" + "="*80)
            print("✓ 检查完成")

        except Exception as e:
            print(f"\n✗ 检查失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_table_dates())
