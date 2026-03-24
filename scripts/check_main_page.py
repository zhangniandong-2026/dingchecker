#!/usr/bin/env python3
"""检查主页面中的所有链接"""
import asyncio
from playwright.async_api import async_playwright

async def check_main_page_links():
    """检查主页面中有哪些可点击的链接"""

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]

            # 主页面URL
            main_url = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"

            print("=" * 80)
            print("检查主页面中的所有链接")
            print("=" * 80)

            # 导航到主页面
            await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)

            print(f"\n当前 URL: {page.url}")
            print(f"页面标题: {await page.title()}")

            # 在所有frames中查找包含"组"的文本
            all_texts = []
            frames = page.frames
            print(f"\n总 Frame 数: {len(frames)}")

            for i, frame in enumerate(frames):
                try:
                    # 获取所有包含"组"的文本元素
                    elements = await frame.query_selector_all('text=/.*组.*/')
                    if elements:
                        print(f"\nFrame {i} 找到 {len(elements)} 个包含'组'的元素:")
                        for elem in elements[:20]:  # 只显示前20个
                            text = await elem.inner_text()
                            text = text.strip()
                            if text and len(text) < 50:  # 过滤太长的文本
                                print(f"  - {text}")
                                all_texts.append(text)
                except Exception as e:
                    pass

            # 特别查找我们要找的6个单元
            target_units = [
                "媒体军工组",
                "交通行业组",
                "政府行业一组",
                "政府行业二组",
                "能源组",
                "央企组",
            ]

            print(f"\n{'='*80}")
            print("查找目标业务单元:")
            print(f"{'='*80}")

            for unit in target_units:
                found = False
                for frame in frames:
                    try:
                        elem = await frame.query_selector(f'text="{unit}"')
                        if elem:
                            is_visible = await elem.is_visible()
                            print(f"  ✓ {unit}: 找到 (可见: {is_visible})")
                            found = True
                            break
                    except:
                        pass

                if not found:
                    print(f"  ✗ {unit}: 未找到")

            print("\n" + "=" * 80)
            print("✓ 检查完成")

        except Exception as e:
            print(f"\n✗ 检查失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_main_page_links())
