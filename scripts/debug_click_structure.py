#!/usr/bin/env python3
"""调试：查看点击业务单元后的页面结构"""
import asyncio
from playwright.async_api import async_playwright

async def debug_click_unit():
    """点击一个业务单元，查看页面结构"""

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]

            print("="*80)
            print("调试：点击业务单元后的页面结构")
            print("="*80)

            # 导航到主页面
            main_url = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"
            print(f"\n1. 导航到主页面...")
            await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            print("   ✓ 主页面加载完成")

            # 查找Frame 2
            frames = page.frames
            print(f"\n2. 检查Frames: 共{len(frames)}个")

            if len(frames) < 3:
                print("   ✗ Frame 2不存在")
                return

            frame2 = frames[2]
            print(f"   Frame 2: {frame2.url[:80]}...")

            # 获取第一个业务单元链接
            links = await frame2.query_selector_all('a')
            print(f"\n3. Frame 2中有 {len(links)} 个链接")

            if len(links) == 0:
                print("   ✗ 没有找到链接")
                return

            first_link = links[0]
            unit_name = await first_link.inner_text()
            print(f"\n4. 准备点击第一个业务单元: {unit_name}")

            # 记录点击前的URL
            before_url = page.url
            print(f"   点击前URL: {before_url[:80]}...")

            # 点击链接
            print(f"\n5. 点击链接...")
            await first_link.click()
            await page.wait_for_timeout(3000)

            # 检查点击后的状态
            after_url = page.url
            print(f"   点击后URL: {after_url[:80]}...")
            print(f"   URL是否变化: {'是' if before_url != after_url else '否'}")

            # 检查是否打开了新标签页
            pages = page.context.pages
            print(f"\n6. 当前打开的页面数: {len(pages)}")

            # 检查当前页面的frames
            print(f"\n7. 检查点击后的Frame结构:")
            current_frames = page.frames
            print(f"   Frame数量: {len(current_frames)}")

            for idx, frame in enumerate(current_frames):
                print(f"\n   Frame {idx}:")
                print(f"   URL: {frame.url[:80]}...")

                # 获取文本内容的前几行
                try:
                    text = await frame.evaluate('() => document.body ? document.body.innerText : ""')
                    lines = [l.strip() for l in text.split('\n') if l.strip()][:10]
                    print(f"   文本内容前10行:")
                    for i, line in enumerate(lines, 1):
                        print(f"      {i}. {line[:60]}")

                    # 查找关键词
                    keywords = ['日期', '提交日期', 'AI听记', '链接', '2026-03-03', '2026-03-02']
                    found = [kw for kw in keywords if kw in text]
                    if found:
                        print(f"   ✓ 找到关键词: {found}")

                    # 查找表格
                    has_table = await frame.evaluate('() => document.querySelector("table") !== null')
                    print(f"   是否有<table>: {has_table}")

                except Exception as e:
                    print(f"   提取失败: {e}")

            # 查找所有链接
            print(f"\n8. 在主页面查找所有<a>标签:")
            all_links = await page.query_selector_all('a')
            print(f"   共 {len(all_links)} 个")

            # 查找包含日期的链接
            date_links = []
            for link in all_links[:50]:  # 只检查前50个
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute('href')
                    if '2026' in text or (href and '2026' in href):
                        date_links.append({
                            'text': text.strip()[:50],
                            'href': href[:80] if href else '(空)'
                        })
                except:
                    pass

            if date_links:
                print(f"\n   找到 {len(date_links)} 个包含日期的链接:")
                for i, link in enumerate(date_links[:10], 1):
                    print(f"   {i}. [{link['text']}] -> {link['href']}")

            print("\n" + "="*80)
            print("✓ 调试完成")

        except Exception as e:
            print(f"\n✗ 调试失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(debug_click_unit())
