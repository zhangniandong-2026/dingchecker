#!/usr/bin/env python3
"""全面检查所有Frame"""
import asyncio
import re
from playwright.async_api import async_playwright

async def check_all_frames():
    """检查所有Frame的内容"""

    print("🔍 全Frame检查")
    print("=" * 80)

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]
            print(f"✓ 已连接: {page.url[:60]}...\n")

            frames = page.frames
            print(f"总Frame数: {len(frames)}\n")

            for idx, frame in enumerate(frames):
                print(f"\n{'='*80}")
                print(f"Frame {idx}")
                print(f"{'='*80}")

                try:
                    url = frame.url
                    print(f"URL: {url}")

                    # 等待Frame加载
                    await frame.wait_for_timeout(1000)

                    # 获取所有文本
                    try:
                        text_content = await frame.evaluate('() => document.body ? document.body.innerText : ""')
                        text_len = len(text_content)
                        print(f"文本长度: {text_len} 字符")

                        if text_len > 0:
                            # 查找日期
                            dates = re.findall(r'202[0-9]-[0-1][0-9]-[0-3][0-9]', text_content)
                            if dates:
                                unique_dates = list(set(dates))
                                print(f"✓ 找到日期: {unique_dates[:10]}")

                            # 查找关键词
                            keywords = ['AI听记', '链接', '业务单元', '移动组', '福建组', '政府', '听记']
                            found = [kw for kw in keywords if kw in text_content]
                            if found:
                                print(f"✓ 找到关键词: {found}")

                            # 查找URL
                            urls = re.findall(r'https?://[^\s<>"\']+', text_content)
                            if urls:
                                unique_urls = list(set(urls))
                                print(f"✓ 找到URL: {len(unique_urls)} 个")
                                for i, url in enumerate(unique_urls[:3]):
                                    print(f"   {i+1}. {url[:80]}...")

                            # 显示文本示例
                            if text_len > 100:
                                lines = text_content.split('\n')
                                non_empty_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) > 5]
                                print(f"\n文本示例 (前10行):")
                                for i, line in enumerate(non_empty_lines[:10]):
                                    print(f"   {i+1}. {line[:70]}")

                    except Exception as e:
                        print(f"无法获取文本内容: {e}")

                    # 检查链接元素
                    links = await frame.query_selector_all('a[href]')
                    if len(links) > 0:
                        print(f"\n<a> 标签: {len(links)} 个")

                        # 检查前几个链接
                        for i, link in enumerate(links[:5]):
                            try:
                                href = await link.get_attribute('href')
                                text = await link.inner_text()
                                if href and (len(href) > 10 or text):
                                    print(f"   {i+1}. [{text[:30]}] -> {href[:60]}")
                            except:
                                pass

                    # 检查标签tab
                    tabs = await frame.query_selector_all('[role="tab"]')
                    if len(tabs) > 0:
                        print(f"\n[role=tab]: {len(tabs)} 个")
                        for i, tab in enumerate(tabs[:10]):
                            try:
                                text = await tab.inner_text()
                                print(f"   {i+1}. {text.strip()}")
                            except:
                                pass

                except Exception as e:
                    print(f"Frame {idx} 处理失败: {e}")

            print("\n" + "="*80)
            print("✓ 检查完成")

        except Exception as e:
            print(f"\n✗ 失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_all_frames())
