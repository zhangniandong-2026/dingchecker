#!/usr/bin/env python3
"""诊断钉钉页面结构的调试脚本"""
import asyncio
from playwright.async_api import async_playwright

async def diagnose_page():
    """诊断当前打开的钉钉页面结构"""

    print("🔍 钉钉页面结构诊断工具")
    print("=" * 60)

    async with async_playwright() as p:
        try:
            # 连接到Chrome调试端口
            print("\n1. 连接Chrome...")
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')

            contexts = browser.contexts
            if not contexts:
                print("✗ 未找到浏览器上下文")
                return

            pages = contexts[0].pages
            if not pages:
                print("✗ 未找到打开的页面")
                return

            page = pages[0]
            print(f"✓ 已连接到页面: {page.url}")

            # 2. 检查iframe数量
            print("\n2. 检查iframe结构...")
            frames = page.frames
            print(f"   总frame数: {len(frames)}")

            for idx, frame in enumerate(frames):
                try:
                    url = frame.url
                    print(f"   Frame {idx}: {url[:80]}")
                except:
                    print(f"   Frame {idx}: (无法获取URL)")

            # 3. 在每个frame中查找表格元素
            print("\n3. 查找表格元素...")

            for idx, frame in enumerate(frames):
                try:
                    print(f"\n   --- Frame {idx} ---")

                    # 查找标准table标签
                    tables = await frame.query_selector_all('table')
                    print(f"   <table> 标签: {len(tables)} 个")

                    # 查找带table class的元素
                    table_divs = await frame.query_selector_all('[class*="table"], [class*="Table"]')
                    print(f"   class*='table': {len(table_divs)} 个")

                    # 查找grid布局
                    grids = await frame.query_selector_all('[class*="grid"], [class*="Grid"]')
                    print(f"   class*='grid': {len(grids)} 个")

                    # 查找row/cell结构
                    rows = await frame.query_selector_all('[class*="row"], [role="row"]')
                    print(f"   row元素: {len(rows)} 个")

                    cells = await frame.query_selector_all('[class*="cell"], [role="cell"]')
                    print(f"   cell元素: {len(cells)} 个")

                    # 查找列名关键词
                    content = await frame.content()
                    keywords = ['日期', '链接', 'AI听记', '提交日期', '业务单元']
                    found_keywords = [kw for kw in keywords if kw in content]
                    if found_keywords:
                        print(f"   ✓ 找到关键词: {', '.join(found_keywords)}")

                    # 如果找到表格，显示详细信息
                    if len(tables) > 0:
                        print(f"\n   📋 详细分析第一个<table>:")
                        table_info = await frame.evaluate('''
                            () => {
                                const table = document.querySelector('table');
                                if (!table) return null;

                                const info = {
                                    className: table.className,
                                    id: table.id,
                                    rows: table.querySelectorAll('tr').length,
                                    cells_in_first_row: 0
                                };

                                const firstRow = table.querySelector('tr');
                                if (firstRow) {
                                    info.cells_in_first_row = firstRow.querySelectorAll('td, th').length;
                                }

                                // 提取第一行内容
                                const headerCells = [];
                                const headers = table.querySelectorAll('thead th, tr:first-child td, tr:first-child th');
                                headers.forEach(h => headerCells.push(h.textContent.trim()));
                                info.headers = headerCells;

                                return info;
                            }
                        ''')

                        if table_info:
                            print(f"      className: {table_info.get('className', 'N/A')}")
                            print(f"      id: {table_info.get('id', 'N/A')}")
                            print(f"      行数: {table_info.get('rows', 0)}")
                            print(f"      第一行单元格数: {table_info.get('cells_in_first_row', 0)}")
                            if table_info.get('headers'):
                                print(f"      表头内容: {table_info['headers'][:5]}")

                    # 尝试其他可能的表格结构
                    if len(tables) == 0:
                        print(f"\n   🔎 尝试其他选择器:")

                        # Canvas表格（一些应用使用canvas渲染）
                        canvases = await frame.query_selector_all('canvas')
                        print(f"      canvas: {len(canvases)} 个")

                        # 虚拟滚动列表
                        virtual_lists = await frame.query_selector_all('[class*="virtual"], [class*="Virtual"]')
                        print(f"      virtual list: {len(virtual_lists)} 个")

                        # Sheet相关元素
                        sheets = await frame.query_selector_all('[class*="sheet"], [class*="Sheet"]')
                        print(f"      sheet元素: {len(sheets)} 个")

                except Exception as e:
                    print(f"   ✗ Frame {idx} 分析失败: {e}")

            # 4. 检查工作表标签
            print("\n4. 查找工作表标签...")

            for idx, frame in enumerate(frames):
                try:
                    tabs = await frame.query_selector_all('[role="tab"]')
                    if len(tabs) > 0:
                        print(f"   Frame {idx}: 找到 {len(tabs)} 个标签")
                        for i, tab in enumerate(tabs[:5]):  # 最多显示5个
                            text = await tab.inner_text()
                            print(f"      Tab {i+1}: {text.strip()}")
                except:
                    pass

            print("\n" + "=" * 60)
            print("✓ 诊断完成")
            print("\n💡 建议：")
            print("   1. 如果找到了table元素，记录其className和id")
            print("   2. 如果没有table，查看使用了哪种替代结构")
            print("   3. 记录包含关键词的frame编号")

        except Exception as e:
            print(f"\n✗ 诊断失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(diagnose_page())
