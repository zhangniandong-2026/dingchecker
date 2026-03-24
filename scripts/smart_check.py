#!/usr/bin/env python3
"""智能检查当前打开的钉钉文档页面 - 动态识别业务单元和日期"""
import asyncio
import sys
import re
import os
from playwright.async_api import async_playwright
from datetime import datetime, date

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

async def discover_current_page(page):
    """识别当前打开的钉钉页面"""
    try:
        current_url = page.url
        print(f"当前页面: {current_url}")

        # 等待页面加载完成
        await page.wait_for_timeout(2000)

        # 检查是否是钉钉文档页面
        if 'alidocs.dingtalk.com' not in current_url and 'dingtalk.com' not in current_url:
            print("⚠️  这不是钉钉文档页面")
            return False

        print("✓ 确认是钉钉文档页面")
        return True
    except Exception as e:
        print(f"✗ 页面识别失败: {e}")
        return False

async def discover_business_units(page):
    """动态发现页面中的所有业务单元（工作表标签）"""
    try:
        print("\n🔍 开始识别业务单元...")

        # 在所有 frame 中查找工作表标签
        all_sheets = []
        frames = [page] + page.frames

        for frame in frames:
            try:
                # 查找可能的工作表标签元素
                # 钉钉文档的工作表通常在底部标签栏
                sheet_elements = await frame.query_selector_all('[role="tab"], .sheet-tab, .tab-item, [class*="sheet"], [class*="tab"]')

                for elem in sheet_elements:
                    text = await elem.inner_text()
                    text = text.strip()

                    # 过滤掉无效的标签名
                    if text and len(text) > 0 and len(text) < 50:
                        # 排除常见的非业务单元标签
                        if text not in ['新建', '添加', '+', '更多', 'Sheet1', 'Sheet2']:
                            if text not in all_sheets:
                                all_sheets.append(text)

            except Exception as e:
                continue

        # 如果自动发现失败，尝试通过页面内容识别
        if not all_sheets:
            print("⚠️  未找到标签栏，尝试从页面内容识别...")
            all_sheets = await discover_from_content(page)

        if all_sheets:
            print(f"✓ 发现 {len(all_sheets)} 个业务单元:")
            for idx, sheet in enumerate(all_sheets, 1):
                print(f"  {idx}. {sheet}")
            return all_sheets
        else:
            print("✗ 未能识别业务单元")
            return []

    except Exception as e:
        print(f"✗ 业务单元识别失败: {e}")
        return []

async def discover_from_content(page):
    """从页面内容中识别业务单元名称"""
    try:
        # 尝试从页面中提取可能的组名
        frames = [page] + page.frames
        potential_units = set()

        for frame in frames:
            try:
                content = await frame.content()

                # 查找常见的业务单元命名模式
                patterns = [
                    r'(\w+组)',  # XX组
                    r'(\w+部)',  # XX部
                    r'(\w+单元)',  # XX单元
                    r'(\w+团队)',  # XX团队
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if len(match) > 2 and len(match) < 20:
                            potential_units.add(match)

            except:
                continue

        return list(potential_units)[:10]  # 最多返回10个

    except Exception as e:
        print(f"内容识别失败: {e}")
        return []

async def discover_table_structure(page):
    """识别表格结构：列名和数据"""
    try:
        print("\n📋 识别表格结构...")

        # 查找包含表格的 iframe
        target_frame = None
        frames = page.frames

        for frame in frames:
            try:
                content = await frame.content()
                # 查找常见的列名
                if any(keyword in content for keyword in ['日期', '链接', '提交日期', 'AI听记']):
                    target_frame = frame
                    break
            except:
                pass

        if not target_frame:
            print("⚠️  未找到表格")
            return None

        # 提取表格结构
        table_info = await target_frame.evaluate('''
            () => {
                // 查找表格
                const tables = document.querySelectorAll('table');
                if (tables.length === 0) return null;

                const table = tables[0];
                const headers = [];
                const rows = [];

                // 提取表头
                const headerCells = table.querySelectorAll('thead th, tr:first-child td, tr:first-child th');
                headerCells.forEach(cell => {
                    headers.push(cell.textContent.trim());
                });

                // 提取数据行（前10行）
                const dataRows = table.querySelectorAll('tbody tr, tr');
                let count = 0;
                dataRows.forEach(row => {
                    if (count >= 10) return;

                    const cells = row.querySelectorAll('td, th');
                    if (cells.length > 0) {
                        const rowData = [];
                        cells.forEach(cell => {
                            rowData.push(cell.textContent.trim());
                        });
                        rows.push(rowData);
                        count++;
                    }
                });

                return {
                    headers: headers,
                    rows: rows,
                    columnCount: headers.length
                };
            }
        ''')

        if table_info:
            print(f"✓ 表格结构:")
            print(f"  列数: {table_info['columnCount']}")
            print(f"  列名: {', '.join(table_info['headers'][:5])}...")  # 只显示前5列
            print(f"  数据行: {len(table_info['rows'])}")

            # 自动识别关键列
            date_col_idx = None
            link_col_idx = None

            for idx, header in enumerate(table_info['headers']):
                if '日期' in header or 'Date' in header:
                    date_col_idx = idx
                    print(f"  → 日期列: 第 {idx + 1} 列 ({header})")
                if 'AI听记' in header or '链接' in header or 'Link' in header:
                    link_col_idx = idx
                    print(f"  → 链接列: 第 {idx + 1} 列 ({header})")

            table_info['date_col_idx'] = date_col_idx
            table_info['link_col_idx'] = link_col_idx

            return table_info
        else:
            print("✗ 无法解析表格")
            return None

    except Exception as e:
        print(f"✗ 表格结构识别失败: {e}")
        return None

async def extract_links_by_date(page, target_date, table_info):
    """根据日期提取链接"""
    try:
        if not table_info or table_info['date_col_idx'] is None or table_info['link_col_idx'] is None:
            print("⚠️  表格结构信息不完整，无法提取")
            return []

        date_idx = table_info['date_col_idx']
        link_idx = table_info['link_col_idx']

        print(f"\n🔗 提取日期 {target_date} 的链接...")

        links = []
        for row in table_info['rows']:
            if len(row) > max(date_idx, link_idx):
                row_date = row[date_idx].strip()
                row_link = row[link_idx].strip()

                # 匹配日期
                if target_date in row_date or row_date in target_date:
                    if row_link and ('http' in row_link or 'shanji.dingtalk' in row_link):
                        links.append(row_link)
                        print(f"  ✓ 找到链接: {row_link[:50]}...")

        if not links:
            print(f"  ⚠️  未找到日期 {target_date} 的链接")

        return links

    except Exception as e:
        print(f"✗ 链接提取失败: {e}")
        return []

async def extract_meeting_content(page, link):
    """提取会议内容"""
    try:
        print(f"\n📄 访问链接: {link[:60]}...")

        # 访问链接
        await page.goto(link, wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(3000)

        # 提取会议内容
        # 尝试多个选择器
        selectors = [
            '.meeting-content',
            '.transcribe-content',
            '[class*="content"]',
            'main',
            'article',
            'body'
        ]

        content = None
        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    content = await elem.inner_text()
                    if content and len(content) > 100:  # 至少有100字符
                        break
            except:
                continue

        if content:
            content = content.strip()
            print(f"  ✓ 提取成功 ({len(content)} 字符)")
            return content
        else:
            print("  ⚠️  未找到有效内容")
            return None

    except Exception as e:
        print(f"  ✗ 内容提取失败: {e}")
        return None

async def analyze_with_gemini(all_content):
    """使用 Gemini 分析会议内容"""
    try:
        if not GEMINI_AVAILABLE:
            print("⚠️  Gemini SDK 未安装")
            return None

        print("\n🧠 开始 AI 分析...")

        # 配置 Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            print("⚠️  未配置 GEMINI_API_KEY")
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # 构建提示词
        prompt = f"""
请分析以下业务会议内容，提供专业的管理分析报告：

{all_content}

请提供以下维度的分析：

1. **各业务单元工作摘要**
   - 简要概括每个单元的核心工作
   - 识别关键里程碑和成果

2. **横向对比与优秀实践**
   - 对比各单元的工作方式
   - 标注值得学习的亮点（用✨标记）

3. **各业务单元改进建议**
   - 针对每个单元的具体建议
   - 考虑其独特情况

4. **整体改进建议**
   - 适用于所有团队的通用建议
   - 组织级优化方向
"""

        response = model.generate_content(prompt)
        analysis = response.text

        print("✓ AI 分析完成")
        return analysis

    except Exception as e:
        print(f"✗ AI 分析失败: {e}")
        return None

def generate_report(units_data, analysis, output_format='txt'):
    """生成报告"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_date = datetime.now().strftime('%Y-%m-%d')

        # 文本报告
        report = f"""
{'='*80}
钉钉会议智能分析报告
生成时间: {timestamp}
{'='*80}

【数据统计】
总计: {len(units_data)} 个业务单元
成功提取: {sum(1 for u in units_data if u['content'])}
无内容: {sum(1 for u in units_data if not u['content'])}

{'='*80}
【各业务单元详情】
{'='*80}

"""

        for idx, unit in enumerate(units_data, 1):
            report += f"\n[{idx}] {unit['name']}\n"
            report += f"{'─'*60}\n"

            if unit['content']:
                report += f"链接: {unit['link']}\n\n"
                report += unit['content']
                report += "\n\n"
            else:
                report += "状态: 未获取到内容\n\n"

        if analysis:
            report += f"\n{'='*80}\n"
            report += "【AI 智能分析】\n"
            report += f"{'='*80}\n\n"
            report += analysis
            report += "\n\n💡 分析由 Google Gemini 生成\n"

        report += f"\n{'='*80}\n"

        # 保存文本报告
        report_dir = os.path.expanduser('~/dingtalk_checker/daily_reports')
        os.makedirs(report_dir, exist_ok=True)

        txt_path = os.path.join(report_dir, f'smart_report_{report_date}.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✓ 报告已保存: {txt_path}")

        # 生成 PDF
        if output_format == 'pdf':
            pdf_path = generate_pdf_report(txt_path)
            if pdf_path:
                print(f"✓ PDF 已生成: {pdf_path}")
                return pdf_path

        return txt_path

    except Exception as e:
        print(f"✗ 报告生成失败: {e}")
        return None

def generate_pdf_report(txt_path):
    """生成 PDF 报告"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # 注册中文字体
        font_path = '/System/Library/Fonts/STHeiti Light.ttc'
        pdfmetrics.registerFont(TTFont('STHeiti', font_path))

        # 读取文本内容
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 创建 PDF
        pdf_path = txt_path.replace('.txt', '.pdf')
        c = canvas.Canvas(pdf_path, pagesize=A4)
        c.setFont('STHeiti', 10)

        # 写入内容（简化版）
        y = 800
        for line in content.split('\n')[:100]:  # 限制行数
            if y < 50:
                c.showPage()
                y = 800
                c.setFont('STHeiti', 10)

            c.drawString(50, y, line[:80])  # 限制每行长度
            y -= 15

        c.save()
        return pdf_path

    except Exception as e:
        print(f"⚠️  PDF 生成失败: {e}")
        return None

async def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         钉钉会议智能分析系统 v2.0 (Smart Mode)              ║
║         自动识别业务单元 · 动态提取链接 · AI 分析           ║
╚══════════════════════════════════════════════════════════════╝
""")

    # 获取参数
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
    print(f"目标日期: {target_date}\n")

    async with async_playwright() as p:
        try:
            # 连接到 Chrome 调试端口
            print("🔌 连接 Chrome 调试端口...")
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')

            # 获取当前打开的页面
            contexts = browser.contexts
            if not contexts:
                print("✗ 未找到打开的页面")
                return

            pages = contexts[0].pages
            if not pages:
                print("✗ 未找到打开的标签页")
                return

            page = pages[0]  # 使用第一个标签页
            print(f"✓ 已连接到页面\n")

            # 1. 识别当前页面
            if not await discover_current_page(page):
                return

            # 2. 识别业务单元
            business_units = await discover_business_units(page)
            if not business_units:
                print("\n⚠️  未能自动识别业务单元，使用默认列表")
                business_units = ["政府行业一组", "政府行业二组", "央企组"]

            # 3. 识别表格结构
            table_info = await discover_table_structure(page)

            # 4. 提取会议内容
            units_data = []

            for unit_name in business_units:
                print(f"\n{'='*60}")
                print(f"处理: {unit_name}")
                print(f"{'='*60}")

                unit_data = {
                    'name': unit_name,
                    'link': None,
                    'content': None
                }

                # 提取链接
                if table_info:
                    links = await extract_links_by_date(page, target_date, table_info)
                    if links:
                        unit_data['link'] = links[0]

                        # 提取内容
                        content = await extract_meeting_content(page, links[0])
                        unit_data['content'] = content

                units_data.append(unit_data)

            # 5. AI 分析
            all_content = "\n\n".join([
                f"【{u['name']}】\n{u['content']}"
                for u in units_data if u['content']
            ])

            analysis = None
            if all_content:
                analysis = await analyze_with_gemini(all_content)

            # 6. 生成报告
            report_path = generate_report(units_data, analysis, output_format='pdf')

            print(f"\n{'='*60}")
            print("✓ 处理完成！")
            print(f"报告: {report_path}")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"\n✗ 执行失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
