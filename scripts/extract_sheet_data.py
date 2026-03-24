#!/usr/bin/env python3
"""提取钉钉虚拟表格的实际数据"""
import asyncio
import json
from playwright.async_api import async_playwright

async def extract_sheet_data():
    """提取钉钉表格数据"""

    print("📊 钉钉表格数据提取测试")
    print("=" * 60)

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]
            print(f"✓ 已连接\n")

            frames = page.frames

            # 重点检查Frame 1（钉钉表格iframe）
            if len(frames) < 2:
                print("✗ Frame 1 不存在")
                return

            frame = frames[1]
            print(f"检查Frame 1: {frame.url[:80]}...\n")

            # 方法1: 尝试通过可见文本提取
            print("方法1: 提取所有可见文本...")
            all_text = await frame.evaluate('''
                () => {
                    return document.body.innerText;
                }
            ''')

            # 搜索日期模式
            import re
            dates = re.findall(r'202[0-9]-[0-1][0-9]-[0-3][0-9]', all_text)
            print(f"  找到日期: {dates[:10]}")

            # 搜索URL
            urls = re.findall(r'https?://[^\s<>"]+', all_text)
            print(f"  找到URL: {len(urls)} 个")
            if urls:
                print(f"  示例: {urls[0][:60]}...")

            # 方法2: 查找包含"AI听记"的链接
            print("\n方法2: 查找链接元素...")
            links = await frame.query_selector_all('a[href]')
            print(f"  总链接数: {len(links)}")

            valid_links = []
            for link in links[:50]:  # 只检查前50个
                href = await link.get_attribute('href')
                text = await link.inner_text()
                if href and ('shanji.dingtalk' in href or 'alidocs' in href):
                    valid_links.append({
                        'href': href,
                        'text': text.strip()[:30]
                    })

            if valid_links:
                print(f"  有效链接: {len(valid_links)} 个")
                for i, link in enumerate(valid_links[:5]):
                    print(f"    {i+1}. {link['text']} -> {link['href'][:60]}...")

            # 方法3: 查找工作表标签
            print("\n方法3: 查找工作表标签...")
            tabs = await frame.query_selector_all('[role="tab"]')
            print(f"  标签数: {len(tabs)}")

            for i, tab in enumerate(tabs[:10]):
                text = await tab.inner_text()
                is_selected = await tab.get_attribute('aria-selected')
                print(f"    {i+1}. {text.strip()} (selected: {is_selected})")

            # 方法4: 尝试点击标签并提取数据
            if len(tabs) > 0:
                print("\n方法4: 尝试激活第一个标签...")
                first_tab = tabs[0]
                await first_tab.click()
                await frame.wait_for_timeout(1000)

                # 再次检查页面内容
                new_text = await frame.evaluate('() => document.body.innerText')
                new_dates = re.findall(r'202[0-9]-[0-1][0-9]-[0-3][0-9]', new_text)
                print(f"  点击后找到日期: {new_dates[:10]}")

            # 方法5: 检查是否有API数据
            print("\n方法5: 检查window对象...")
            window_data = await frame.evaluate('''
                () => {
                    const info = {
                        hasReact: typeof window.React !== 'undefined',
                        hasVue: typeof window.Vue !== 'undefined',
                        hasAngular: typeof window.angular !== 'undefined',
                        customKeys: []
                    };

                    // 查找自定义的全局变量
                    for (let key in window) {
                        if (key.startsWith('__') || key.includes('data') || key.includes('Data')) {
                            info.customKeys.push(key);
                        }
                    }

                    return info;
                }
            ''')

            print(f"  React: {window_data['hasReact']}")
            print(f"  Vue: {window_data['hasVue']}")
            print(f"  自定义键: {window_data['customKeys'][:10]}")

            # 方法6: 监听网络请求
            print("\n方法6: 检查页面HTML源码...")
            html_sample = await frame.content()

            # 查找data属性
            data_attrs = re.findall(r'data-[a-zA-Z-]+="[^"]*"', html_sample)
            print(f"  data-* 属性: {len(data_attrs)} 个")
            if data_attrs:
                unique_attrs = list(set([attr.split('=')[0] for attr in data_attrs]))
                print(f"  属性名: {unique_attrs[:10]}")

            print("\n" + "=" * 60)
            print("✓ 数据提取测试完成")

            # 总结
            print("\n💡 发现:")
            print(f"   - 日期数量: {len(dates)}")
            print(f"   - URL数量: {len(urls)}")
            print(f"   - 有效链接: {len(valid_links)}")
            print(f"   - 工作表标签: {len(tabs)}")

        except Exception as e:
            print(f"\n✗ 提取失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(extract_sheet_data())
