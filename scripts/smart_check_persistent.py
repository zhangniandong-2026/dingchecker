#!/usr/bin/env python3
"""智能检查 - 使用持久化浏览器，不需要远程调试"""
import asyncio
import sys
import os
from playwright.async_api import async_playwright
from datetime import datetime

# 复用之前的功能
import importlib.util
spec = importlib.util.spec_from_file_location("smart_check", os.path.expanduser("~/dingtalk_checker/scripts/smart_check.py"))
smart_check = importlib.util.module_from_spec(spec)

async def main():
    """主函数 - 使用持久化浏览器"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║    钉钉会议智能分析系统 v2.1 (Persistent Browser Mode)     ║
║             无需远程调试 · 自动保持登录状态                 ║
╚══════════════════════════════════════════════════════════════╝
""")

    # 获取参数
    target_url = sys.argv[1] if len(sys.argv) > 1 else None
    target_date = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime('%Y-%m-%d')

    if not target_url:
        print("❌ 请提供钉钉文档 URL")
        print("\n使用方法:")
        print("  python3 smart_check_persistent.py <钉钉文档URL> [日期]")
        print("\n示例:")
        print("  python3 smart_check_persistent.py https://alidocs.dingtalk.com/i/nodes/xxxxx")
        print("  python3 smart_check_persistent.py https://alidocs.dingtalk.com/i/nodes/xxxxx 2026-03-01")
        return

    print(f"目标 URL: {target_url}")
    print(f"目标日期: {target_date}\n")

    async with async_playwright() as p:
        try:
            # 使用持久化浏览器上下文
            user_data_dir = os.path.expanduser('~/dingtalk_checker/chrome/chrome_persistent_profile')
            os.makedirs(user_data_dir, exist_ok=True)

            print("🔌 启动持久化浏览器...")
            print(f"   用户数据目录: {user_data_dir}")
            print("   (首次使用需要登录钉钉，之后会自动保持登录)\n")

            context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=False,  # 显示浏览器窗口
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                ]
            )

            # 获取或创建页面
            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()

            print("✓ 浏览器已启动\n")

            # 导航到目标 URL
            print(f"📄 访问页面: {target_url[:60]}...")
            await page.goto(target_url, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(3000)
            print("✓ 页面加载完成\n")

            # 检查是否需要登录
            try:
                page_content = await page.content()
                needs_login = '登录' in page_content or 'login' in page.url.lower()
            except:
                # 页面可能还在加载
                await page.wait_for_timeout(3000)
                try:
                    page_content = await page.content()
                    needs_login = '登录' in page_content or 'login' in page.url.lower()
                except:
                    needs_login = False

            if needs_login:
                print("\n⚠️  检测到需要登录")
                print("等待登录完成... (自动检测页面变化)")

                # 自动等待登录完成（最多等待 2 分钟）
                for i in range(120):
                    await page.wait_for_timeout(1000)
                    try:
                        content = await page.content()
                        if '登录' not in content and 'login' not in page.url.lower():
                            print("✓ 登录检测完成")
                            break
                    except:
                        pass  # 页面还在加载，继续等待

                    if i % 10 == 0 and i > 0:
                        print(f"  等待中... ({i}秒)")

                await page.wait_for_timeout(2000)

            # 执行智能检查流程
            # 这里可以复用 smart_check.py 中的函数
            spec.loader.exec_module(smart_check)

            # 识别业务单元
            business_units = await smart_check.discover_business_units(page)
            if not business_units:
                print("\n⚠️  未能自动识别业务单元，使用默认列表")
                business_units = ["政府行业一组", "政府行业二组", "央企组"]

            # 识别表格结构
            table_info = await smart_check.discover_table_structure(page)

            # 提取会议内容
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

                if table_info:
                    links = await smart_check.extract_links_by_date(page, target_date, table_info)
                    if links:
                        unit_data['link'] = links[0]
                        content = await smart_check.extract_meeting_content(page, links[0])
                        unit_data['content'] = content

                units_data.append(unit_data)

            # AI 分析
            all_content = "\n\n".join([
                f"【{u['name']}】\n{u['content']}"
                for u in units_data if u['content']
            ])

            analysis = None
            if all_content:
                analysis = await smart_check.analyze_with_gemini(all_content)

            # 生成报告
            report_path = smart_check.generate_report(units_data, analysis, output_format='pdf')

            print(f"\n{'='*60}")
            print("✓ 处理完成！")
            print(f"报告: {report_path}")
            print(f"{'='*60}\n")

            # 等待一段时间后自动关闭
            print("5 秒后自动关闭浏览器...")
            await page.wait_for_timeout(5000)

            await context.close()

        except Exception as e:
            print(f"\n✗ 执行失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
