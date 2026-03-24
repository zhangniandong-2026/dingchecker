#!/usr/bin/env python3
"""检查每个业务单元中最新的日期"""
import asyncio
from playwright.async_api import async_playwright
import re

async def check_all_units_dates():
    """检查所有业务单元的最新日期"""

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]

            # 6个业务单元
            units = [
                "媒体军工组",
                "交通行业组",
                "政府行业一组",
                "政府行业二组",
                "能源组",
                "央企组",
            ]

            # 主页面URL
            main_url = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"

            print("=" * 80)
            print("检查所有业务单元的最新日期")
            print("=" * 80)

            # 导航到主页面
            await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)

            for unit_name in units:
                print(f"\n{'='*80}")
                print(f"业务单元: {unit_name}")
                print(f"{'='*80}")

                # 查找并点击链接
                clicked = False
                frames = page.frames

                for frame in frames:
                    try:
                        element = await frame.query_selector(f'text="{unit_name}"')
                        if element:
                            await element.click()
                            await page.wait_for_timeout(5000)
                            clicked = True
                            break
                    except:
                        pass

                if not clicked:
                    print("  ✗ 未找到链接")
                    continue

                # 查找表格Frame
                table_frame = None
                frames = page.frames

                for frame in frames:
                    try:
                        content = await frame.content()
                        if '提交日期' in content and 'AI听记' in content:
                            table_frame = frame
                            break
                    except:
                        pass

                if not table_frame:
                    print("  ✗ 未找到表格")
                    await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(2000)
                    continue

                # 获取所有日期
                text = await table_frame.evaluate('() => document.body ? document.body.innerText : ""')
                dates = re.findall(r'(202[0-9]-[0-1][0-9]-[0-3][0-9])', text)
                unique_dates = sorted(set(dates), reverse=True)

                if unique_dates:
                    print(f"  ✓ 找到 {len(unique_dates)} 个日期:")
                    print(f"     最新: {unique_dates[0]}")
                    print(f"     最旧: {unique_dates[-1]}")
                    if len(unique_dates) > 5:
                        print(f"     最近5个: {', '.join(unique_dates[:5])}")
                    else:
                        print(f"     所有: {', '.join(unique_dates)}")

                    # 检查是否有听记链接
                    urls = re.findall(r'(https://shanji\.dingtalk\.com/[^\s<>"\']+)', text)
                    print(f"     听记链接数: {len(urls)}")
                else:
                    print("  ✗ 未找到任何日期")

                # 返回主页面
                await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(2000)

            print("\n" + "=" * 80)
            print("✓ 检查完成")

        except Exception as e:
            print(f"\n✗ 检查失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_all_units_dates())
