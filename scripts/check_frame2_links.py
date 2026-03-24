#!/usr/bin/env python3
"""详细检查Frame 2的链接"""
import asyncio
from playwright.async_api import async_playwright

async def check_frame2_links():
    """检查Frame 2中的所有链接"""

    print("🔗 Frame 2 链接详细分析")
    print("=" * 80)

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]

            frames = page.frames
            if len(frames) < 3:
                print("Frame 2 不存在")
                return

            frame = frames[2]  # Frame 2
            print(f"URL: {frame.url}\n")

            # 获取所有链接
            links = await frame.query_selector_all('a')
            print(f"找到 {len(links)} 个<a>标签\n")

            for i, link in enumerate(links, 1):
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    title = await link.get_attribute('title')

                    print(f"链接 {i}:")
                    print(f"   文本: {text.strip()[:50] if text else '(空)'}")
                    print(f"   href: {href[:80] if href else '(空)'}")
                    if title:
                        print(f"   title: {title[:50]}")

                    # 检查是否是听记链接
                    if href and ('shanji.dingtalk' in href or 'meeting' in href or '听记' in href):
                        print(f"   ✓ 这是听记链接!")

                    print()

                except Exception as e:
                    print(f"链接 {i} 解析失败: {e}\n")

        except Exception as e:
            print(f"\n✗ 失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_frame2_links())
