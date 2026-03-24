#!/usr/bin/env python3
"""检查表格是否需要滚动加载"""
import asyncio
from playwright.async_api import async_playwright
import re

async def check_with_scroll():
    """检查是否需要滚动"""

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = browser.contexts[0].pages[0]

        # 导航到主页面
        main_url = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"
        await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)

        # 点击政府行业一组
        print("=" * 80)
        print("检查表格数据（含滚动）")
        print("=" * 80)

        frames = page.frames
        for frame in frames:
            try:
                result = await frame.evaluate('''
                    () => {
                        const element = document.evaluate(
                            `//*[text()="政府行业一组"]`,
                            document,
                            null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE,
                            null
                        ).singleNodeValue;
                        if (element) {
                            element.click();
                            return true;
                        }
                        return false;
                    }
                ''')
                if result:
                    print("\n✓ 点击政府行业一组")
                    await page.wait_for_timeout(5000)
                    break
            except:
                pass

        # 查找表格frame
        table_frame = None
        for frame in page.frames:
            try:
                content = await frame.content()
                if '提交日期' in content and 'AI听记' in content:
                    table_frame = frame
                    print("✓ 找到表格Frame")
                    break
            except:
                pass

        if not table_frame:
            print("✗ 未找到表格")
            return

        # 第一次提取（不滚动）
        text = await table_frame.evaluate('() => document.body.innerText')
        dates_before = re.findall(r'(202[0-9]-[0-1][0-9]-[0-3][0-9])', text)
        unique_before = sorted(set(dates_before), reverse=True)

        print(f"\n【滚动前】找到 {len(unique_before)} 个日期:")
        for date in unique_before[:10]:
            print(f"  {date}")

        # 尝试向上滚动到顶部
        print(f"\n→ 滚动到顶部...")
        await table_frame.evaluate('''
            () => {
                window.scrollTo(0, 0);
                // 也尝试滚动表格容器
                const tables = document.querySelectorAll('[class*="table"], [class*="grid"], [class*="sheet"]');
                tables.forEach(t => {
                    if (t.scrollTop !== undefined) {
                        t.scrollTop = 0;
                    }
                });
            }
        ''')
        await page.wait_for_timeout(2000)

        # 第二次提取（滚动到顶部后）
        text = await table_frame.evaluate('() => document.body.innerText')
        dates_after = re.findall(r'(202[0-9]-[0-1][0-9]-[0-3][0-9])', text)
        unique_after = sorted(set(dates_after), reverse=True)

        print(f"\n【滚动后】找到 {len(unique_after)} 个日期:")
        for date in unique_after[:10]:
            print(f"  {date}")

        # 检查是否有今天的数据
        target_dates = ["2026-03-03", "2026-03-02"]
        print(f"\n【检查目标日期】")
        for target in target_dates:
            if target in unique_after:
                print(f"  ✓ {target}: 存在")
            else:
                print(f"  ✗ {target}: 不存在")

        print("\n" + "=" * 80)

asyncio.run(check_with_scroll())
