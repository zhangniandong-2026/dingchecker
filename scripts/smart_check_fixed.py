#!/usr/bin/env python3
"""智能检查当前打开的钉钉文档页面 - 修复版"""
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
        await page.wait_for_timeout(3000)  # 增加等待时间到3秒

        # 检查是否是钉钉文档页面
        if 'alidocs.dingtalk.com' not in current_url and 'dingtalk.com' not in current_url:
            print("⚠️  这不是钉钉文档页面")
            return False

        print("✓ 确认是钉钉文档页面")
        return True
    except Exception as e:
        print(f"✗ 页面识别失败: {e}")
        return False

async def discover_business_units_from_text(page):
    """从页面文本内容中提取业务单元"""
    try:
        print("\n🔍 开始识别业务单元...")

        frames = page.frames
        all_text = ""

        # 从Frame 1和Frame 2提取文本
        for idx in [1, 2]:
            if idx < len(frames):
                try:
                    frame = frames[idx]
                    text = await frame.evaluate('() => document.body ? document.body.innerText : ""')
                    all_text += "\n" + text
                    print(f"   Frame {idx}: {len(text)} 字符")
                except:
                    pass

        if not all_text.strip():
            print("⚠️  无法获取页面文本")
            return []

        # 使用正则表达式提取业务单元名称
        patterns = [
            r'([\u4e00-\u9fa5]{2,10}组)',  # XX组 (中文2-10字)
            r'([\u4e00-\u9fa5]{2,10}部)',  # XX部
            r'([\u4e00-\u9fa5]{2,15}单元)',  # XX单元
            r'([\u4e00-\u9fa5]{2,10}团队)',  # XX团队
            r'([\u4e00-\u9fa5]{2,15}战队)',  # XX战队
            r'([\u4e00-\u9fa5]{2,15}分战队)',  # XX分战队
        ]

        all_units = set()
        for pattern in patterns:
            matches = re.findall(pattern, all_text)
            for match in matches:
                # 过滤掉明显不是业务单元的词
                if match not in ['工作组', '小组', '部门', '团队', '单元', '战队']:
                    if len(match) >= 3 and len(match) <= 15:
                        all_units.add(match)

        units_list = sorted(list(all_units))

        if units_list:
            print(f"✓ 识别到 {len(units_list)} 个业务单元:")
            for idx, unit in enumerate(units_list, 1):
                print(f"  {idx}. {unit}")
            return units_list
        else:
            print("⚠️  未能识别到业务单元")
            return []

    except Exception as e:
        print(f"✗ 业务单元识别失败: {e}")
        import traceback
        traceback.print_exc()
        return []

async def find_table_data_in_text(page, target_date):
    """在页面文本中查找表格数据"""
    try:
        print(f"\n📋 搜索日期 {target_date} 的数据...")

        frames = page.frames
        all_data = []

        # 检查每个frame
        for idx, frame in enumerate(frames):
            try:
                # 获取所有文本
                text = await frame.evaluate('() => document.body ? document.body.innerText : ""')

                # 按行分割
                lines = text.split('\n')

                # 查找包含目标日期的行
                for i, line in enumerate(lines):
                    if target_date in line:
                        print(f"   ✓ Frame {idx} 第{i}行: {line.strip()[:60]}")

                        # 提取周围的行作为上下文
                        context_start = max(0, i - 2)
                        context_end = min(len(lines), i + 3)
                        context = lines[context_start:context_end]

                        all_data.append({
                            'frame': idx,
                            'line': i,
                            'content': line.strip(),
                            'context': '\n'.join([l.strip() for l in context if l.strip()])
                        })

                # 查找URL链接
                urls = re.findall(r'https?://[^\s<>"\']+', text)
                if urls:
                    for url in urls:
                        if 'shanji.dingtalk' in url or 'alidocs.dingtalk' in url:
                            print(f"   ✓ Frame {idx} 找到链接: {url[:60]}...")
                            all_data.append({
                                'frame': idx,
                                'type': 'link',
                                'url': url
                            })

            except Exception as e:
                print(f"   Frame {idx} 搜索失败: {e}")

        return all_data

    except Exception as e:
        print(f"✗ 数据搜索失败: {e}")
        return []

async def extract_meeting_content(page, link):
    """提取会议内容"""
    try:
        print(f"\n📄 访问链接: {link[:60]}...")

        # 访问链接
        await page.goto(link, wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(3000)

        # 提取会议内容 - 尝试多个选择器
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

def generate_report(units_data, analysis, target_date, output_format='txt'):
    """生成报告"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_date = target_date

        # 文本报告
        report = f"""
{'='*80}
钉钉会议智能分析报告
生成时间: {timestamp}
目标日期: {report_date}
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
                if unit.get('link'):
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
║         钉钉会议智能分析系统 v2.1 (Fixed Version)           ║
║         修复表格解析 · 文本模式提取 · 智能识别              ║
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

            # 2. 从文本中识别业务单元
            business_units = await discover_business_units_from_text(page)

            if not business_units:
                print("\n⚠️  未能识别业务单元，尝试使用默认列表")
                business_units = ["移动组", "福建组", "北京非金一组", "北京非金二组",
                                "政府行业一组", "政府行业二组", "华北一组", "交通行业组"]
                print(f"   使用默认业务单元: {business_units}")

            # 3. 搜索目标日期的数据
            table_data = await find_table_data_in_text(page, target_date)

            if table_data:
                print(f"\n✓ 找到 {len(table_data)} 条相关数据")
            else:
                print(f"\n⚠️  未找到日期 {target_date} 的数据")

            # 4. 处理每个业务单元
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

                # 从table_data中查找链接
                for data in table_data:
                    if data.get('type') == 'link':
                        # 简单策略：为每个业务单元分配一个链接
                        # 实际应用中可能需要更复杂的匹配逻辑
                        if not unit_data['link']:
                            unit_data['link'] = data['url']
                            print(f"   找到链接: {data['url'][:60]}...")

                            # 提取内容
                            content = await extract_meeting_content(page, data['url'])
                            unit_data['content'] = content
                            break

                units_data.append(unit_data)

            # 5. AI 分析
            all_content = "\n\n".join([
                f"【{u['name']}】\n{u['content']}"
                for u in units_data if u['content']
            ])

            analysis = None
            if all_content and len(all_content) > 100:
                analysis = await analyze_with_gemini(all_content)

            # 6. 生成报告
            report_path = generate_report(units_data, analysis, target_date, output_format='pdf')

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
