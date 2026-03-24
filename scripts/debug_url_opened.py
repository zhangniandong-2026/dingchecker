#!/usr/bin/env python3
"""检查当前打开的URL"""
import asyncio
from playwright.async_api import async_playwright

async def check_url():
    """检查当前打开的URL"""

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]

            print("=" * 80)
            print("当前打开的页面信息")
            print("=" * 80)
            print(f"\n当前 URL: {page.url}")
            print(f"\n页面标题: {await page.title()}")

            # 检查有多少个frame
            frames = page.frames
            print(f"\n总 Frame 数: {len(frames)}")

            for i, frame in enumerate(frames):
                print(f"\nFrame {i}:")
                print(f"  URL: {frame.url[:100]}...")
                try:
                    # 尝试获取frame内容的片段
                    content = await frame.content()
                    print(f"  内容长度: {len(content)} 字符")

                    # 检查是否包含关键词
                    if '提交日期' in content:
                        print(f"  ✓ 包含 '提交日期'")
                    if 'AI听记' in content:
                        print(f"  ✓ 包含 'AI听记'")
                    if 'shanji.dingtalk.com' in content:
                        print(f"  ✓ 包含听记链接")
                except Exception as e:
                    print(f"  ✗ 无法读取内容: {e}")

            print("\n" + "=" * 80)
            print("✓ 检查完成")

        except Exception as e:
            print(f"\n✗ 检查失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_url())
