#!/usr/bin/env python3
"""提取Frame 2的所有业务单元名称"""
import asyncio
from playwright.async_api import async_playwright

async def extract_all_units():
    """提取所有业务单元"""

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]

            frames = page.frames
            if len(frames) < 3:
                print("Frame 2 不存在")
                return []

            frame = frames[2]  # Frame 2
            print(f"Frame 2: {frame.url}\n")

            # 获取所有链接的文本
            links = await frame.query_selector_all('a')
            print(f"找到 {len(links)} 个链接\n")

            units = []
            for link in links:
                try:
                    text = await link.inner_text()
                    text = text.strip()
                    if text and len(text) > 2:  # 至少3个字符
                        units.append(text)
                except:
                    pass

            print(f"提取到 {len(units)} 个业务单元：\n")
            for i, unit in enumerate(units, 1):
                print(f'{i:2d}. "{unit}",')

            return units

        except Exception as e:
            print(f"提取失败: {e}")
            import traceback
            traceback.print_exc()
            return []

if __name__ == '__main__':
    asyncio.run(extract_all_units())
