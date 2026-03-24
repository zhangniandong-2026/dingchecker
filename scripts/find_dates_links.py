#!/usr/bin/env python3
"""查找页面中的所有日期和链接"""
import asyncio
import re
from playwright.async_api import async_playwright

async def find_dates_and_links():
    """查找页面中所有的日期和链接"""

    print("📅 查找页面中的日期和链接")
    print("=" * 80)

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]
            print(f"✓ 已连接\n")

            frames = page.frames

            all_dates = {}
            all_links = {}

            for idx, frame in enumerate(frames):
                try:
                    text = await frame.evaluate('() => document.body ? document.body.innerText : ""')

                    # 查找日期
                    dates = re.findall(r'(202[0-9]-[0-1][0-9]-[0-3][0-9])', text)
                    if dates:
                        all_dates[f'Frame {idx}'] = list(set(dates))

                    # 查找链接
                    urls = re.findall(r'(https?://[^\s<>"\']+)', text)
                    if urls:
                        valid_urls = [u for u in urls if 'shanji.dingtalk' in u or 'alidocs.dingtalk' in u]
                        if valid_urls:
                            all_links[f'Frame {idx}'] = valid_urls

                    # 查找包含"今天"、"昨天"等的行
                    lines = text.split('\n')
                    relative_dates = []
                    for line in lines:
                        if any(keyword in line for keyword in ['今天', '昨天', '前天', '周']):
                            relative_dates.append(line.strip())

                    if relative_dates:
                        print(f"\nFrame {idx} - 相对日期:")
                        for rd in relative_dates[:10]:
                            print(f"   {rd[:60]}")

                except:
                    pass

            print(f"\n{'='*80}")
            print("找到的日期:")
            print(f"{'='*80}")
            for frame, dates in all_dates.items():
                print(f"\n{frame}:")
                for date in sorted(set(dates)):
                    print(f"   {date}")

            print(f"\n{'='*80}")
            print("找到的链接:")
            print(f"{'='*80}")
            for frame, links in all_links.items():
                print(f"\n{frame}:")
                for i, link in enumerate(links[:5], 1):
                    print(f"   {i}. {link[:80]}...")

            # 尝试在frame中查找带有特定文本的链接
            print(f"\n{'='*80}")
            print("查找带特定文本的元素:")
            print(f"{'='*80}")

            for idx in [1, 2]:
                if idx < len(frames):
                    frame = frames[idx]
                    print(f"\nFrame {idx}:")

                    # 查找所有链接元素
                    links = await frame.query_selector_all('a')
                    print(f"   总<a>标签: {len(links)} 个")

                    for i, link in enumerate(links[:10]):
                        try:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            if href:
                                print(f"   {i+1}. [{text[:20]}] -> {href[:60]}")
                        except:
                            pass

        except Exception as e:
            print(f"\n✗ 失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(find_dates_and_links())
