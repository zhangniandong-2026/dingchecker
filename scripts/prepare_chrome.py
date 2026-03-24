#!/usr/bin/env python3
"""
Chrome 调试环境预检查和自动修复脚本
确保 Chrome 处于正确状态，可以被自动化程序使用
"""
import asyncio
import sys
import subprocess
from playwright.async_api import async_playwright
import time

# 钉钉主页面 URL
DINGTALK_URL = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"

async def check_chrome_process():
    """检查 Chrome 调试进程是否运行"""
    print("1️⃣  检查 Chrome 调试进程...")
    result = subprocess.run(
        ['pgrep', '-f', 'remote-debugging-port=9222'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("   ✅ Chrome 调试模式运行中")
        return True
    else:
        print("   ❌ Chrome 调试模式未运行")
        print("   💡 请运行: bash ~/dingtalk_checker/chrome/start_chrome_debug.sh")
        return False

async def ensure_page_exists():
    """确保至少有一个可用的页面"""
    print("\n2️⃣  检查浏览器页面...")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            context = browser.contexts[0]

            # 查找可用的页面（排除 Chrome 内部页面）
            usable_page = None
            for page in context.pages:
                url = page.url
                # 排除 Chrome 内部页面
                if not url.startswith('chrome://') and not url.startswith('chrome-extension://'):
                    usable_page = page
                    print(f"   ✅ 找到可用页面: {url[:60]}...")
                    break

            # 如果没有可用页面，创建新页面
            if not usable_page:
                print("   ⚠️  没有可用的页面，创建新页面...")
                usable_page = await context.new_page()
                print("   ✅ 新页面已创建")

            return usable_page

    except Exception as e:
        print(f"   ❌ 连接 Chrome 失败: {e}")
        return None

async def navigate_to_dingtalk(page):
    """导航到钉钉页面"""
    print("\n3️⃣  导航到钉钉文档...")

    try:
        # 检查当前是否已经在钉钉页面
        current_url = page.url
        if 'alidocs.dingtalk.com' in current_url:
            print(f"   ✅ 已在钉钉页面")
            return True

        # 导航到钉钉主页
        print(f"   → 正在打开 {DINGTALK_URL[:60]}...")
        await page.goto(DINGTALK_URL, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(3000)

        print("   ✅ 页面已打开")
        return True

    except Exception as e:
        print(f"   ❌ 导航失败: {e}")
        return False

async def check_login_status(page):
    """检查是否已登录钉钉"""
    print("\n4️⃣  检查登录状态...")

    try:
        # 等待页面加载
        await page.wait_for_timeout(2000)

        # 检查是否在登录页面（通过 URL 判断）
        if 'login' in page.url.lower():
            print("   ❌ 未登录，当前在登录页面")
            print("   💡 请在浏览器中手动登录钉钉")
            return False

        # 检查页面内容是否包含目录（说明已登录）
        content = await page.content()

        # 检查关键元素
        if '目录' in content or '快速访问' in content or '知识库' in content:
            print("   ✅ 已登录钉钉")
            return True

        # 尝试检查是否有业务单元链接
        frames = page.frames
        has_units = False
        for frame in frames:
            try:
                text = await frame.evaluate('() => document.body ? document.body.innerText : ""')
                if any(unit in text for unit in ['政府行业一组', '交通行业组', '央企组']):
                    has_units = True
                    break
            except:
                pass

        if has_units:
            print("   ✅ 已登录钉钉（检测到业务单元）")
            return True

        # 无法确定，但不报错
        print("   ⚠️  无法确定登录状态，可能需要手动检查")
        return True  # 返回 True 继续执行

    except Exception as e:
        print(f"   ⚠️  检查登录状态出错: {e}")
        return True  # 出错也返回 True，让后续流程继续

async def refresh_page_if_needed(page):
    """如果页面长时间未刷新，重新加载"""
    print("\n5️⃣  检查页面新鲜度...")

    try:
        # 重新导航到主页面，确保数据是最新的
        await page.goto(DINGTALK_URL, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(2000)
        print("   ✅ 页面已刷新")
        return True
    except Exception as e:
        print(f"   ⚠️  刷新页面失败: {e}")
        return False

async def main():
    """主函数"""
    print("="*70)
    print("🔧 Chrome 调试环境预检查")
    print("="*70)

    # 1. 检查 Chrome 进程
    if not await check_chrome_process():
        print("\n❌ 预检查失败：Chrome 调试模式未运行")
        sys.exit(1)

    playwright = None
    browser = None

    try:
        # 创建 playwright 实例
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp('http://localhost:9222')
        context = browser.contexts[0]

        # 2. 查找或创建可用页面
        print("\n2️⃣  检查浏览器页面...")
        usable_page = None
        for page in context.pages:
            url = page.url
            if not url.startswith('chrome://') and not url.startswith('chrome-extension://'):
                usable_page = page
                print(f"   ✅ 找到可用页面: {url[:60]}...")
                break

        if not usable_page:
            print("   ⚠️  没有可用的页面，创建新页面...")
            usable_page = await context.new_page()
            print("   ✅ 新页面已创建")

        # 3. 导航到钉钉
        print("\n3️⃣  导航到钉钉文档...")
        current_url = usable_page.url
        if 'alidocs.dingtalk.com' in current_url:
            print(f"   ✅ 已在钉钉页面")
        else:
            print(f"   → 正在打开 {DINGTALK_URL[:60]}...")
            await usable_page.goto(DINGTALK_URL, wait_until='domcontentloaded', timeout=30000)
            await usable_page.wait_for_timeout(3000)
            print("   ✅ 页面已打开")

        # 4. 检查登录状态
        print("\n4️⃣  检查登录状态...")
        await usable_page.wait_for_timeout(2000)

        if 'login' in usable_page.url.lower():
            print("   ❌ 未登录，当前在登录页面")
            print("\n💡 解决方法：")
            print("   1. 在 Chrome 中打开钉钉文档")
            print("   2. 手动登录")
            print("   3. 重新运行检查程序")
            sys.exit(1)

        content = await usable_page.content()
        if '目录' in content or '快速访问' in content or '知识库' in content:
            print("   ✅ 已登录钉钉")
        else:
            # 检查业务单元
            frames = usable_page.frames
            has_units = False
            for frame in frames:
                try:
                    text = await frame.evaluate('() => document.body ? document.body.innerText : ""')
                    if any(unit in text for unit in ['政府行业一组', '交通行业组', '央企组']):
                        has_units = True
                        break
                except:
                    pass

            if has_units:
                print("   ✅ 已登录钉钉（检测到业务单元）")
            else:
                print("   ⚠️  无法确定登录状态，建议手动检查")

        # 5. 刷新页面
        print("\n5️⃣  刷新页面确保数据最新...")
        await usable_page.goto(DINGTALK_URL, wait_until='domcontentloaded', timeout=30000)
        await usable_page.wait_for_timeout(2000)
        print("   ✅ 页面已刷新")

        print("\n" + "="*70)
        print("✅ 所有检查通过！Chrome 环境已准备好")
        print("="*70)

    except Exception as e:
        print(f"\n❌ 预检查失败: {e}")
        sys.exit(1)

    finally:
        # 不关闭 browser，保持连接
        if playwright:
            await playwright.stop()

    sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())
