#!/usr/bin/env python3
"""深度诊断钉钉虚拟表格结构"""
import asyncio
import json
from playwright.async_api import async_playwright

async def deep_diagnose():
    """深度诊断钉钉表格的实际DOM结构"""

    print("🔬 钉钉虚拟表格深度诊断")
    print("=" * 60)

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            page = browser.contexts[0].pages[0]
            print(f"✓ 已连接: {page.url[:60]}...\n")

            # 重点检查Frame 1（有34个sheet元素）
            frames = page.frames
            target_frames = [0, 1]  # Frame 0 和 Frame 1 都有关键词

            for frame_idx in target_frames:
                if frame_idx >= len(frames):
                    continue

                frame = frames[frame_idx]
                print(f"\n{'='*60}")
                print(f"Frame {frame_idx}: {frame.url[:80]}")
                print(f"{'='*60}")

                # 1. 查找所有可能包含数据的容器
                result = await frame.evaluate('''
                    () => {
                        const info = {
                            sheets: [],
                            cells: [],
                            rows: [],
                            dataContainers: []
                        };

                        // 查找sheet相关元素
                        const sheetElements = document.querySelectorAll('[class*="sheet"], [class*="Sheet"]');
                        sheetElements.forEach(el => {
                            if (el.textContent && el.textContent.length < 500) {
                                info.sheets.push({
                                    className: el.className,
                                    text: el.textContent.trim().substring(0, 50)
                                });
                            }
                        });

                        // 查找cell相关元素
                        const cellSelectors = [
                            '[class*="cell"]',
                            '[class*="Cell"]',
                            '[data-cell]',
                            '[role="gridcell"]'
                        ];

                        cellSelectors.forEach(selector => {
                            const cells = document.querySelectorAll(selector);
                            if (cells.length > 0) {
                                info.cells.push({
                                    selector: selector,
                                    count: cells.length,
                                    samples: Array.from(cells).slice(0, 5).map(c => c.textContent.trim().substring(0, 30))
                                });
                            }
                        });

                        // 查找row相关元素
                        const rowSelectors = [
                            '[class*="row"]',
                            '[class*="Row"]',
                            '[data-row]',
                            '[role="row"]'
                        ];

                        rowSelectors.forEach(selector => {
                            const rows = document.querySelectorAll(selector);
                            if (rows.length > 0) {
                                info.rows.push({
                                    selector: selector,
                                    count: rows.length
                                });
                            }
                        });

                        // 查找可能包含数据的容器
                        const dataSelectors = [
                            '[class*="data"]',
                            '[class*="Data"]',
                            '[class*="content"]',
                            '[class*="Content"]',
                            '[class*="grid"]',
                            '[class*="Grid"]'
                        ];

                        dataSelectors.forEach(selector => {
                            const containers = document.querySelectorAll(selector);
                            if (containers.length > 0 && containers.length < 100) {
                                info.dataContainers.push({
                                    selector: selector,
                                    count: containers.length
                                });
                            }
                        });

                        return info;
                    }
                ''')

                # 显示结果
                if result['sheets']:
                    print(f"\n📋 Sheet元素 ({len(result['sheets'])} 个):")
                    for i, sheet in enumerate(result['sheets'][:10]):
                        print(f"   {i+1}. [{sheet['className'][:40]}] {sheet['text']}")

                if result['cells']:
                    print(f"\n🔲 Cell元素:")
                    for cell_group in result['cells']:
                        print(f"   {cell_group['selector']}: {cell_group['count']} 个")
                        if cell_group['samples']:
                            print(f"      示例: {cell_group['samples'][:3]}")

                if result['rows']:
                    print(f"\n📏 Row元素:")
                    for row_group in result['rows']:
                        print(f"   {row_group['selector']}: {row_group['count']} 个")

                if result['dataContainers']:
                    print(f"\n📦 数据容器:")
                    for container in result['dataContainers'][:5]:
                        print(f"   {container['selector']}: {container['count']} 个")

                # 2. 搜索包含特定文本的元素
                print(f"\n🔍 搜索关键文本元素...")
                keywords = ['2026-03-03', '2026-03-02', 'AI听记', '链接']

                for keyword in keywords:
                    elements = await frame.query_selector_all(f'text="{keyword}"')
                    if len(elements) > 0:
                        print(f"   '{keyword}': 找到 {len(elements)} 个")

                        # 获取第一个元素的详细信息
                        if len(elements) > 0:
                            elem_info = await frame.evaluate('''
                                (keyword) => {
                                    const xpath = `//*[contains(text(), "${keyword}")]`;
                                    const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                                    const elem = result.singleNodeValue;

                                    if (elem) {
                                        return {
                                            tagName: elem.tagName,
                                            className: elem.className,
                                            parent: elem.parentElement ? {
                                                tagName: elem.parentElement.tagName,
                                                className: elem.parentElement.className
                                            } : null
                                        };
                                    }
                                    return null;
                                }
                            ''', keyword)

                            if elem_info:
                                print(f"      标签: <{elem_info['tagName']}> class='{elem_info['className'][:50]}'")

                # 3. 尝试找到包含日期列的结构
                print(f"\n📅 搜索日期模式...")
                date_elements = await frame.evaluate('''
                    () => {
                        const datePattern = /202[0-9]-[0-1][0-9]-[0-3][0-9]/;
                        const found = [];

                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null
                        );

                        let count = 0;
                        while (walker.nextNode() && count < 20) {
                            const text = walker.currentNode.textContent.trim();
                            if (datePattern.test(text)) {
                                const elem = walker.currentNode.parentElement;
                                found.push({
                                    text: text,
                                    tagName: elem.tagName,
                                    className: elem.className
                                });
                                count++;
                            }
                        }

                        return found;
                    }
                ''')

                if date_elements:
                    print(f"   找到 {len(date_elements)} 个日期元素:")
                    for i, elem in enumerate(date_elements[:5]):
                        print(f"   {i+1}. {elem['text']} [<{elem['tagName']}> class='{elem['className'][:40]}']")

            print("\n" + "=" * 60)
            print("✓ 深度诊断完成")

        except Exception as e:
            print(f"\n✗ 诊断失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(deep_diagnose())
