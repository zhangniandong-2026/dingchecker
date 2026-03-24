#!/usr/bin/env python3
"""测试手动点击一个业务单元链接"""
import asyncio
from playwright.async_api import async_playwright

async def test_click_unit():
    """测试点击业务单元链接"""

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]

            # 主页面URL
            main_url = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"

            print("=" * 80)
            print("测试点击业务单元链接")
            print("=" * 80)

            # 导航到主页面
            print(f"\n1. 导航到主页面...")
            await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            print(f"   当前 URL: {page.url}")

            # 测试单元
            unit_name = "政府行业一组"
            print(f"\n2. 查找并点击: {unit_name}")

            # 查找链接
            clicked = False
            frames = page.frames

            for i, frame in enumerate(frames):
                try:
                    elem = await frame.query_selector(f'text="{unit_name}"')
                    if elem:
                        is_visible = await elem.is_visible()
                        print(f"   ✓ 在 Frame {i} 找到 (可见: {is_visible})")

                        if is_visible:
                            print(f"   → 点击...")
                            await elem.click()
                            await page.wait_for_timeout(5000)
                            clicked = True
                            print(f"   ✓ 已点击")
                            break
                except Exception as e:
                    print(f"   Frame {i} 错误: {e}")

            if not clicked:
                print(f"   ✗ 未能点击")
                return

            print(f"\n3. 检查页面变化...")
            print(f"   当前 URL: {page.url}")

            # 查找表格
            table_found = False
            frames = page.frames

            for i, frame in enumerate(frames):
                try:
                    content = await frame.content()
                    if '提交日期' in content and 'AI听记' in content:
                        table_found = True
                        print(f"   ✓ 在 Frame {i} 找到表格")

                        # 获取文本内容查看日期
                        text = await frame.evaluate('() => document.body ? document.body.innerText : ""')
                        import re
                        dates = re.findall(r'(202[0-9]-[0-1][0-9]-[0-3][0-9])', text)
                        unique_dates = sorted(set(dates), reverse=True)

                        if unique_dates:
                            print(f"   ✓ 找到日期: {', '.join(unique_dates[:5])}")
                        else:
                            print(f"   ✗ 未找到日期")
                        break
                except:
                    pass

            if not table_found:
                print(f"   ✗ 未找到表格")

            print("\n" + "=" * 80)
            print("✓ 测试完成")

        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_click_unit())
