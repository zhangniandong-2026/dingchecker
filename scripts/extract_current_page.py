#!/usr/bin/env python3
"""直接从当前打开的页面提取听记链接"""
import asyncio
import re
from playwright.async_api import async_playwright

async def extract_from_current_page():
    """直接从当前页面提取"""

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]

            print("=" * 80)
            print("从当前页面提取数据")
            print("=" * 80)
            print(f"\n当前 URL: {page.url}")

            # 查找包含表格的frame
            table_frame = None
            frames = page.frames

            for frame in frames:
                try:
                    content = await frame.content()
                    if '提交日期' in content and 'AI听记' in content:
                        table_frame = frame
                        print(f"\n✓ 找到表格Frame")
                        break
                except:
                    pass

            if not table_frame:
                print("\n✗ 未找到表格Frame")
                return

            # 获取所有文本
            text = await table_frame.evaluate('() => document.body ? document.body.innerText : ""')

            # 查找日期 2026-03-02
            target_date = "2026-03-02"
            if target_date in text:
                print(f"\n✓ 找到日期 {target_date}")

                # 查找该日期附近的听记链接
                urls = re.findall(r'(https://shanji\.dingtalk\.com/[^\s<>"\']+)', text)
                print(f"\n找到 {len(urls)} 个听记链接:")
                for i, url in enumerate(urls[:5], 1):
                    print(f"  {i}. {url[:80]}...")
            else:
                print(f"\n✗ 未找到日期 {target_date}")

                # 显示找到的所有日期
                dates = re.findall(r'(202[0-9]-[0-1][0-9]-[0-3][0-9])', text)
                unique_dates = sorted(set(dates), reverse=True)
                print(f"\n找到的日期 ({len(unique_dates)} 个):")
                for date in unique_dates[:10]:
                    print(f"  - {date}")

            print("\n" + "=" * 80)
            print("✓ 提取完成")

        except Exception as e:
            print(f"\n✗ 提取失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(extract_from_current_page())
