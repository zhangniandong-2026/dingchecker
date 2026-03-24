#!/usr/bin/env python3
"""每日自动检查所有业务单元的AI听记"""
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

def load_business_units_with_groups():
    """从配置文件加载业务单元列表，同时保留分组信息"""
    config_file = os.path.expanduser("~/repos/dingcheck/config/business_units.txt")
    units = []
    groups = {}  # {unit_name: group_name}
    current_group = "未分组"

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()

                    # 识别分组标题（注释行，如 "# 华东战区"）
                    if line.startswith('#') and len(line) > 1:
                        # 提取分组名称
                        group_name = line.lstrip('#').strip()
                        # 排除顶级注释（包含"配置文件"等说明性文字）
                        if any(kw in group_name for kw in ['配置文件', '每行', '单元名称', '一、', '二、']):
                            continue
                        if group_name:
                            current_group = group_name
                    # 业务单元行
                    elif line and not line.startswith('#'):
                        units.append(line)
                        groups[line] = current_group

            if units:
                print(f"✓ 从配置文件加载了 {len(units)} 个业务单元")
                return units, groups
        except Exception as e:
            print(f"⚠️ 读取配置文件失败: {e}")

    # 如果配置文件不存在或读取失败，使用默认列表（向后兼容）
    print("⚠️ 使用默认业务单元列表（6个）")
    default_units = [
        "媒体军工组",
        "交通行业组",
        "政府行业一组",
        "政府行业二组",
        "能源组",
        "央企组",
    ]
    default_groups = {unit: "默认分组" for unit in default_units}
    return default_units, default_groups

# 加载业务单元列表和分组信息
ALL_SHEETS, UNIT_GROUPS = load_business_units_with_groups()

async def navigate_to_main_page(page):
    """导航到主页面"""
    try:
        main_url = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"
        print(f"导航到主页面: {main_url}")
        await page.goto(main_url, wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(3000)
        print("✓ 主页面加载完成\n")
        return True
    except Exception as e:
        print(f"✗ 导航失败: {e}")
        return False

async def click_sheet_link(page, sheet_name):
    """点击工作表链接"""
    try:
        print(f"  查找工作表链接...")

        # 在主页面或iframe中查找
        frames = [page] + page.frames

        for frame in frames:
            try:
                # 先尝试直接查找
                element = await frame.query_selector(f'text="{sheet_name}"')

                # 如果没找到，尝试滚动页面
                if not element:
                    try:
                        await frame.evaluate('''
                            () => {
                                window.scrollTo(0, document.body.scrollHeight);
                            }
                        ''')
                        await page.wait_for_timeout(2000)

                        # 再次查找
                        element = await frame.query_selector(f'text="{sheet_name}"')
                    except:
                        pass

                if element:
                    print(f"  ✓ 找到链接")

                    # 滚动到元素可见
                    try:
                        await element.scroll_into_view_if_needed()
                        await page.wait_for_timeout(500)
                    except:
                        pass

                    # 点击并等待 - 使用更稳健的策略
                    click_success = False
                    for attempt in range(3):  # 尝试3次
                        try:
                            if attempt > 0:
                                print(f"  ⚠ 第{attempt + 1}次尝试点击...")

                            # 尝试使用JavaScript点击（更稳定）
                            await frame.evaluate('''
                                (text) => {
                                    const element = document.evaluate(
                                        `//*[text()="${text}"]`,
                                        document,
                                        null,
                                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                                        null
                                    ).singleNodeValue;
                                    if (element) {
                                        element.click();
                                        return true;
                                    }
                                    return false;
                                }
                            ''', sheet_name)

                            click_success = True
                            print(f"  ✓ 已点击，等待页面加载...")
                            break
                        except Exception as click_error:
                            if attempt == 2:  # 最后一次尝试
                                print(f"  ⚠ 点击失败: {str(click_error)[:50]}")
                            await page.wait_for_timeout(1000)

                    if not click_success:
                        # 如果JavaScript点击也失败，尝试常规点击
                        try:
                            await element.click(timeout=5000)
                            click_success = True
                            print(f"  ✓ 已点击（常规方式），等待页面加载...")
                        except:
                            pass

                    if not click_success:
                        continue  # 跳过此frame，尝试其他frame

                    # 等待更长时间确保iframe内容完全加载
                    await page.wait_for_timeout(5000)

                    # 验证frame是否加载完成
                    found_table = False
                    for _ in range(10):  # 最多再等5秒
                        frames_check = page.frames
                        for f in frames_check:
                            try:
                                content = await f.content()
                                if '提交日期' in content and 'AI听记链接' in content:
                                    print(f"  ✓ 表格加载完成")
                                    found_table = True
                                    return True
                            except:
                                pass
                        if found_table:
                            break
                        await page.wait_for_timeout(500)

                    # 即使没有检测到表格，也返回True（可能是权限问题或表格为空）
                    print(f"  ⚠ 未检测到表格，但继续执行（可能是权限或空表格）")
                    return True
            except Exception as e:
                print(f"  ⚠ 点击异常: {str(e)[:50]}")
                continue

        print(f"  ✗ 未找到工作表链接")
        return False

    except Exception as e:
        print(f"  ✗ 点击出错: {str(e)[:100]}")
        return False

async def extract_content_for_current_sheet(page, target_date):
    """提取当前工作表指定日期的内容 - 使用点击策略"""
    try:
        # 查找包含表格的 iframe，增加重试机制
        target_frame = None
        for attempt in range(5):  # 最多尝试5次
            frames = page.frames
            for frame in frames:
                try:
                    content = await frame.content()
                    if '提交日期' in content and 'AI听记链接' in content:
                        target_frame = frame
                        break
                except:
                    pass

            if target_frame:
                break

            if attempt < 4:  # 不是最后一次尝试
                await page.wait_for_timeout(1000)

        if not target_frame:
            return "无表格", None

        # 策略：找到日期元素，然后模拟点击右侧的链接
        result = await target_frame.evaluate('''
            (targetDate) => {
                // 1. 查找目标日期元素
                function findDateElement() {
                    const allElements = document.querySelectorAll('*');
                    for (const elem of allElements) {
                        if (elem.children.length === 0) {
                            const text = elem.textContent.trim();
                            if (text === targetDate) {
                                return elem;
                            }
                        }
                    }
                    return null;
                }

                const dateElement = findDateElement();
                if (!dateElement) {
                    return { success: false, reason: 'date-not-found' };
                }

                // 2. 滚动到该元素
                dateElement.scrollIntoView({ behavior: 'auto', block: 'center' });

                // 3. 获取日期元素的位置
                const dateRect = dateElement.getBoundingClientRect();
                const dateY = dateRect.top + dateRect.height / 2;
                const dateRight = dateRect.right;

                // 4. 查找右侧的链接元素
                const allLinks = document.querySelectorAll('a, [role="link"]');
                const candidates = [];

                for (const link of allLinks) {
                    const linkRect = link.getBoundingClientRect();
                    const linkY = linkRect.top + linkRect.height / 2;
                    const linkX = linkRect.left;
                    const text = link.textContent.trim();
                    const href = link.href || '';

                    // 条件：Y坐标接近（同一行，缩小到20像素内）且在日期右侧
                    if (Math.abs(linkY - dateY) < 20 && linkX > dateRight - 100) {
                        // 必须是shanji.dingtalk.com的链接
                        if (href.includes('shanji.dingtalk.com')) {
                            candidates.push({
                                element: link,
                                text: text,
                                href: href,
                                distanceX: linkX - dateRight,
                                distanceY: Math.abs(linkY - dateY)
                            });
                        }
                    }
                }

                if (candidates.length === 0) {
                    return { success: false, reason: 'link-not-found', dateY: dateY };
                }

                // 5. 按距离排序，选择最近的
                candidates.sort((a, b) => {
                    const distA = Math.sqrt(a.distanceX ** 2 + a.distanceY ** 2);
                    const distB = Math.sqrt(b.distanceX ** 2 + b.distanceY ** 2);
                    return distA - distB;
                });

                // 6. 返回要点击的元素的XPath
                function getXPath(element) {
                    if (element.id) return `//*[@id="${element.id}"]`;
                    const parts = [];
                    while (element && element.nodeType === Node.ELEMENT_NODE) {
                        let nbOfPreviousSiblings = 0;
                        let sibling = element.previousSibling;
                        while (sibling) {
                            if (sibling.nodeType !== Node.DOCUMENT_TYPE_NODE &&
                                sibling.nodeName === element.nodeName) {
                                nbOfPreviousSiblings++;
                            }
                            sibling = sibling.previousSibling;
                        }
                        const prefix = element.nodeName.toLowerCase();
                        const nth = nbOfPreviousSiblings > 0 ? `[${nbOfPreviousSiblings + 1}]` : '';
                        parts.push(prefix + nth);
                        element = element.parentElement;
                    }
                    return parts.length ? '/' + parts.reverse().join('/') : '';
                }

                return {
                    success: true,
                    xpath: getXPath(candidates[0].element),
                    linkText: candidates[0].text,
                    candidatesCount: candidates.length
                };
            }
        ''', target_date)

        if not result.get('success'):
            return "无", None

        # 点击链接
        try:
            # 记录点击前的所有页面URL
            initial_urls = set(pg.url for pg in page.context.pages)

            # 通过XPath定位并点击元素
            click_result = await target_frame.evaluate(f'''
                (xpath) => {{
                    const element = document.evaluate(xpath, document, null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (element) {{
                        element.click();
                        return true;
                    }}
                    return false;
                }}
            ''', result['xpath'])

            if not click_result:
                return "无", None

            # 等待新标签页打开，最多等待10秒
            link_url = None
            new_page = None

            for _ in range(20):  # 20次 × 500ms = 10秒
                await page.wait_for_timeout(500)

                # 检查是否有新打开的页面
                for pg in page.context.pages:
                    if pg.url not in initial_urls:
                        new_page = pg

                        # 情况1: 真正的听记链接
                        if 'shanji.dingtalk.com' in pg.url:
                            link_url = pg.url.replace('/permission/', '/transcribes/')
                            await pg.close()
                            break

                        # 情况2: 打开了错误页面（假链接/备注文字）
                        # 检查是否是错误页面
                        try:
                            page_content = await pg.content()
                            # 如果是Chrome错误页面或空白页
                            if ('ERR_' in pg.url or 'chrome-error://' in pg.url or
                                'about:blank' in pg.url or
                                '无法访问' in page_content or 'ERR_CONNECTION' in page_content):
                                await pg.close()
                                return "无", None  # 这是假链接，归为"无链接"
                        except:
                            pass

                        # 如果是其他未知页面，也关闭
                        await pg.close()
                        break

                if link_url or new_page:
                    break

            if not link_url:
                return "无", None

        except Exception as e:
            return "无", None
        
        # 访问链接并提取内容
        context = page.context
        content_page = await context.new_page()
        
        try:
            await content_page.goto(link_url, wait_until='domcontentloaded', timeout=60000)
            # 增加初始等待时间，给权限验证更多时间
            await content_page.wait_for_timeout(8000)

            # 检查权限
            page_text = await content_page.evaluate('() => document.body.innerText')

            # 如果显示无权限，等待3秒后重试一次（可能只是权限加载慢）
            if '暂无权限' in page_text or '申请权限' in page_text:
                print(f"  ⚠️ 检测到权限提示，等待3秒后重试...")
                await content_page.wait_for_timeout(3000)
                # 重新检查权限
                page_text = await content_page.evaluate('() => document.body.innerText')

                # 重试后还是无权限，才返回"无权限"
                if '暂无权限' in page_text or '申请权限' in page_text:
                    await content_page.close()
                    return "无权限", link_url
                else:
                    print(f"  ✓ 权限验证通过（重试成功）")

            # 等待内容加载
            await content_page.wait_for_timeout(3000)

            # 点击"转写"标签页（默认打开的是"AI 纪要"）
            try:
                clicked = await content_page.evaluate('''
                    () => {
                        // 查找"转写"标签页按钮
                        const tabs = document.querySelectorAll('.dtd-tabs-tab');
                        for (const tab of tabs) {
                            const btn = tab.querySelector('.dtd-tabs-tab-btn');
                            if (btn && btn.innerText.trim() === '转写') {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }
                ''')

                if clicked:
                    print(f"  ✓ 已切换到'转写'标签页")
                    # 等待转写内容加载（增加等待时间）
                    await content_page.wait_for_timeout(4000)
                else:
                    print(f"  ⚠️ 未找到'转写'标签页，使用默认页面")
            except Exception as e:
                print(f"  ⚠️ 切换标签页失败: {e}")

            # 提取内容（只提取转写标签页的内容）
            content = await content_page.evaluate('''
                () => {
                    // 优先尝试提取转写内容区域
                    const transcribeSelectors = [
                        '.fm-transcribe-text__list',
                        '.fm-transcribe-text__auto-sizer',
                        '.fm-transcribe-text'
                    ];

                    for (const selector of transcribeSelectors) {
                        const elem = document.querySelector(selector);
                        if (elem && elem.innerText.trim().length > 50) {
                            return elem.innerText.trim();
                        }
                    }

                    // 如果没找到，尝试查找激活的标签页面板
                    const tabPanels = document.querySelectorAll('.dtd-tabs-tabpane');
                    for (const panel of tabPanels) {
                        if (panel.classList.contains('dtd-tabs-tabpane-active')) {
                            const text = panel.innerText.trim();
                            if (text.length > 50) {
                                return text;
                            }
                        }
                    }

                    // 降级方案：移除导航元素后提取
                    const toRemove = [
                        'nav', 'header', 'footer',
                        '[class*="navigation"]',
                        '[class*="header"]',
                        '[class*="footer"]',
                        '[class*="sidebar"]',
                        '[class*="control"]',
                        'button',
                    ];

                    toRemove.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(elem => {
                            if (elem.parentNode) {
                                elem.remove();
                            }
                        });
                    });

                    return document.body.innerText.trim();
                }
            ''')
            
            # 清理内容
            if content:
                lines = content.split('\n')
                cleaned_lines = []
                skip_keywords = [
                    'AI 听记首页', 'AI 问答', '申请编辑', '翻译', '分享',
                    '转写', '章节', '发言人', '还不错', '待改进',
                    'Powered by', '去升级', '限免', '新建对话', '帮我提炼',
                    '升级权益', '助力业务', '知识即问即用', '问答范围',
                    'AI一键生成思维导图', '👋 Hi', '我可以帮你', '深度思考',
                    '通义', '畅用AI问答'
                ]
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if '👋' in line or '我可以帮你' in line or 'AI一键生成思维导图' in line:
                        break
                    if any(keyword in line for keyword in skip_keywords):
                        continue
                    if re.match(r'^\d{2}:\d{2}$', line):
                        continue
                    if re.match(r'^\d+(\.\d+)?x$', line):
                        continue
                    
                    cleaned_lines.append(line)
                
                content = '\n'.join(cleaned_lines)
            
            await content_page.close()
            
            if content and len(content) > 50:
                # 提取语音转写内容（完整的会议转写，而不是AI纪要）
                transcription = None

                # 钉钉 AI 听记的格式通常是：
                # AI 纪要（这部分我们不要）
                # ...
                # 待办（这部分我们也不要）
                # ...
                # 然后是语音转写部分（这才是我们要的）

                # 策略1: 查找"语音转写"或"转写内容"标题之后的内容
                transcription_match = re.search(r'(语音转写|转写内容|发言记录|会议记录)[\s:：]*(.*?)(?=\n\n\n|$)', content, re.DOTALL)
                if transcription_match:
                    transcription = transcription_match.group(2).strip()
                    print(f"  ✓ 提取到语音转写（{len(transcription)} 字符）")

                # 策略2: 如果没找到明确的转写标题,查找时间戳格式的内容（如"00:00"、"[00:00]"等）
                # 语音转写通常包含大量的时间戳
                if not transcription:
                    # 查找第一个时间戳的位置
                    timestamp_match = re.search(r'\d{2}:\d{2}', content)
                    if timestamp_match:
                        # 从第一个时间戳开始提取
                        start_pos = timestamp_match.start()
                        # 往前找到段落开始（避免截断发言人名字）
                        while start_pos > 0 and content[start_pos-1] not in ['\n', '\r']:
                            start_pos -= 1
                        transcription = content[start_pos:].strip()
                        print(f"  ✓ 通过时间戳定位提取到语音转写（{len(transcription)} 字符）")

                # 策略3: 如果还没找到,尝试排除AI纪要和待办部分,提取剩余内容
                if not transcription:
                    # 找到"待办"之后的内容
                    after_todo_match = re.search(r'待办.*?\n\n(.*)', content, re.DOTALL)
                    if after_todo_match:
                        transcription = after_todo_match.group(1).strip()
                        print(f"  ✓ 排除AI纪要后提取到语音转写（{len(transcription)} 字符）")

                # 策略4: 最后的兜底方案 - 使用完整内容
                if not transcription:
                    transcription = content
                    print(f"  ⚠ 使用完整内容作为语音转写（{len(transcription)} 字符）")

                return transcription, link_url
            else:
                return "无", link_url
            
        except Exception as e:
            await content_page.close()
            return f"访问出错: {str(e)[:100]}", link_url
    
    except Exception as e:
        return f"提取出错: {str(e)[:100]}", None

def analyze_with_ai(results, target_date):
    """使用AI分析会议内容"""
    if not GEMINI_AVAILABLE:
        return "\n\n⚠️ Google Gemini未安装或未配置API密钥，跳过AI分析\n"

    # 检查API密钥
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return "\n\n⚠️ 未配置GEMINI_API_KEY环境变量，跳过AI分析\n使用方法: export GEMINI_API_KEY='your-api-key'\n"

    # 只分析成功提取内容的单元
    success_results = [r for r in results if r['status'] == '成功' and r['content']]

    if len(success_results) == 0:
        return "\n\n📊 AI分析：今日无可分析内容（所有单元均无权限或无链接）\n"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # 构建分析提示词
        content_summary = f"# {target_date} 业务单元早会语音转写内容\n\n"
        for r in success_results:
            # 限制每个单元的内容长度，避免超出token限制
            content_preview = r['content'][:3000] if len(r['content']) > 3000 else r['content']
            content_summary += f"## {r['sheet']}\n\n{content_preview}\n\n"

        prompt = f"""你是一个专业的团队管理顾问，负责评估早会质量。请基于以下早会转写内容，按照"3+1"结构化晨会标准进行评估。

{content_summary}

【输出格式要求】

请严格按照以下格式输出报告（分为四个部分）：

================================================================================
第一部分：早会规范说明（"3+1"结构化模板）
================================================================================

## 一、会议基本信息

**适用对象：** 各业务单元（BU）全体销售、售前及负责人

**会议时间：** 每日 08:30 - 08:50（严格控制在 20 分钟内）

**会议形式：** 站立式，开启录音/转写设备

## 二、汇报内容规范（"3+1"结构化模板）

汇报者必须按照以下顺序发言，以便 AI 提取关键字段：

### 1. 昨日战果（Results） 🎯
**规范：** 必须包含具体数据或进展（如：签单金额、完成初访、方案交付）
**AI 评价点：** 目标达成率、动作量化程度
**示例：**
- ✅ 好："完成XX客户30万POC合同签订"
- ✅ 好："完成3家客户初访，其中2家有明确需求"
- ❌ 差："昨天跟进了一些客户"

### 2. 今日头号任务（Focus） 🔍
**规范：** 仅限 1-3 项核心任务，必须有明确的客户名称和预期结果
**AI 评价点：** 优先级意识、目标清晰度
**示例：**
- ✅ 好："上午10点拜访XX银行张经理，争取获得技术交流机会"
- ✅ 好："下午3点前完成YY公司投标文件，目标金额50万"
- ❌ 差："今天继续跟进客户"

### 3. 项目协同与求助（Support） 🤝
**规范：** 明确提出"谁、在什么时间、支持什么细节"。若无需求请说"今日无协同需求"
**AI 评价点：** 团队协作敏捷度、资源对齐速度
**示例：**
- ✅ 好："需要李工今天下午2点前提供XX产品的技术白皮书"
- ✅ 好："今日无协同需求"
- ❌ 差："可能需要一些支持"

### 4. 市场微情报（Insights） 📈
**规范：** 简短描述竞品动态或客户反馈的一句话
**AI 评价点：** 市场敏感度
**示例：**
- ✅ 好："XX客户反馈竞品A公司报价比我们低15%"
- ✅ 好："今日无新情报"
- ❌ 差："市场情况还可以"

## 三、负责人点评规范

负责人点评需遵循 **"定调子、给资源、控节奏"**：
- ❌ 禁止：在晨会上深入讨论超过 3 分钟的技术方案细节
- ✅ 要求：针对协同需求，必须现场给出明确回应（"散会后对接"或"下午2点开专项会"）
- 📊 AI评价点：领导力决策效率、点评互动比（建议占比 20%-30%）

================================================================================
第二部分：五维度评价说明（基于"3+1"模板）
================================================================================

本报告采用五维度评价体系：

### 维度 1：战果汇报质量 🎯（对应"昨日战果"）
**评分标准（1-5分）：**
5分=所有战果都有具体数据；4分=大部分有数据；3分=部分有数据；2分=描述模糊；1分=完全模糊

### 维度 2：任务聚焦度 🔍（对应"今日头号任务"）
**评分标准（1-5分）：**
5分=1-3项核心任务且明确；4分=3-5项任务；3分=5+项或部分不明确；2分=任务模糊或过多；1分=无明确任务

### 维度 3：协同效率 🤝（对应"项目协同与求助"）
**评分标准（1-5分）：**
5分=明确"谁+何时+做什么"且有响应；4分=明确且响应及时；3分=较明确但响应延迟；2分=模糊或无响应；1分=有需求但不敢提

### 维度 4：情报敏感度 📈（对应"市场微情报"）
**评分标准（1-5分）：**
5分=提供具体有价值情报；4分=有情报且较具体；3分=有情报但不够具体；2分=情报空泛；1分=无情报

### 维度 5：领导点评效率 👔（对应"负责人点评规范"）
**评分标准（1-5分）：**
5分=现场明确决策，简洁有力，时长占比20-30%；4分=大部分明确决策；3分=部分明确或时长略长；2分=决策模糊或时长过长；1分=无实质点评

================================================================================
第三部分：详细评分（对每个业务单元）
================================================================================

[对每个业务单元，按以下格式输出]

一、[业务单元名称]
────────────────────────────────────────
综合得分：XX/25 (XX%)  排名：#X

🎯 战果汇报质量：X分
   ✅ 优点：
      - [具体优点1：引用实际案例]
      - [具体优点2]
   ⚠️ 待改进：
      - [具体建议]
   [如果表现特别好，加上] ✨ 亮点：[特别突出之处]

🔍 任务聚焦度：X分
   [同上格式]

🤝 协同效率：X分
   [同上格式]

📈 情报敏感度：X分
   [同上格式]

👔 领导点评效率：X分
   [同上格式，如无负责人点评则说明"本单元无负责人点评"]

📋 改进建议（按优先级）：
   1. 🔴 高优先级：
      - [最重要的改进建议]

   2. 🟡 中优先级：
      - [重要的改进建议]

   3. 🟢 低优先级：
      - [可选的改进建议]

────────────────────────────────────────

[重复以上格式评价所有业务单元]

================================================================================
第四部分：综合分析与团队建议
================================================================================

📊 整体表现：

1. 综合排名（TOP 5）：
   🥇 [单元名] - XX分 (XX%)
   🥈 [单元名] - XX分 (XX%)
   🥉 [单元名] - XX分 (XX%)
   [列出所有单元的排名]

2. 单项冠军（可作为学习标杆）：
   🎯 战果汇报质量最佳：[单元名] (X分) - [简短说明为什么]
   🔍 任务聚焦度最佳：[单元名] (X分) - [简短说明]
   🤝 协同效率最佳：[单元名] (X分) - [简短说明]
   📈 情报敏感度最佳：[单元名] (X分) - [简短说明]
   👔 领导点评效率最佳：[单元名] (X分) - [简短说明]

3. 需要重点关注的单元：
   ⚠️ [单元名] - XX分 (XX%)
      主要问题：[简要说明，如"战果描述模糊，缺少数据"、"任务过多不聚焦"]
      改进重点：[1-2条关键建议]

🎯 团队层面改进建议（基于"3+1"规范）：

1. 立即行动（本周内实施）：
   ✅ [具体、可操作的建议1]
   ✅ [具体、可操作的建议2]

2. 本月优化：
   ✅ [中期改进建议1]
   ✅ [中期改进建议2]

3. 持续提升：
   ✅ [长期优化建议]

💡 下一步行动清单：
   □ [行动项1，如"组织一次'3+1'规范培训"]
   □ [行动项2]
   □ [行动项3]

📌 特别提醒：
[如果发现普遍性问题，在这里特别强调，如"50%的单元昨日战果描述缺少具体数据，建议统一要求必须包含数字"]

【评估要求】
1. 严格按照"3+1"结构和5个维度评分
2. 评分必须基于具体案例，引用实际内容
3. 改进建议必须具体、可操作、可衡量
4. 不要输出原始转写内容
5. 使用友好、建设性、激励性的语气
6. 对优秀表现要明确表扬和鼓励
"""

        print("  正在进行AI分析...")
        response = model.generate_content(prompt)

        analysis = "\n\n" + "="*80 + "\n"
        analysis += "早会质量评估报告\n"
        analysis += "="*80 + "\n\n"
        analysis += response.text
        analysis += "\n\n" + "="*80 + "\n"
        analysis += "💡 报告由 DingCheck + Google Gemini AI 生成\n"
        analysis += f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        analysis += "="*80 + "\n"

        return analysis

    except Exception as e:
        return f"\n\n⚠️ AI分析失败: {str(e)[:200]}\n"

async def batch_check_auto(target_date):
    """全自动批量检查"""
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]

            # 查找主页面（优先选择有applicationId但没有sheetId的页面）
            pages = context.pages
            page = None
            for pg in pages:
                if "93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm" in pg.url:
                    # 优先选择主页面
                    if "applicationId" in pg.url and "sheetId" not in pg.url:
                        page = pg
                        break
                    # 如果没找到主页面，任何目标URL的页面都可以
                    elif page is None:
                        page = pg

            # 如果还没找到页面，使用第一个页面
            if page is None:
                page = pages[0]

            print(f"="*80)
            print(f"每日检查业务单元 - 日期: {target_date}")
            print(f"业务单元数量: {len(ALL_SHEETS)}")
            print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"="*80)
            print()

            # 导航到主页面
            if not await navigate_to_main_page(page):
                print("✗ 无法导航到主页面")
                return

            results = []

            for i, sheet_name in enumerate(ALL_SHEETS, 1):
                print(f"[{i}/{len(ALL_SHEETS)}] 检查: {sheet_name}")

                # 点击工作表链接
                success = await click_sheet_link(page, sheet_name)
                if not success:
                    print(f"  ✗ 无法切换到此工作表")
                    results.append({
                        'sheet': sheet_name,
                        'group': UNIT_GROUPS.get(sheet_name, "未分组"),
                        'status': '无法访问',
                        'content': None,
                        'link': None
                    })
                    continue

                print(f"  ✓ 已切换到工作表")

                # 提取内容
                content, link = await extract_content_for_current_sheet(page, target_date)

                if content == "无":
                    print(f"  结果: 无听记链接")
                    results.append({
                        'sheet': sheet_name,
                        'group': UNIT_GROUPS.get(sheet_name, "未分组"),
                        'status': '无',
                        'content': None,
                        'link': None
                    })
                elif content == "无表格":
                    print(f"  结果: 无表格数据")
                    results.append({
                        'sheet': sheet_name,
                        'group': UNIT_GROUPS.get(sheet_name, "未分组"),
                        'status': '无表格',
                        'content': None,
                        'link': None
                    })
                elif content == "无权限":
                    print(f"  结果: 无权限")
                    results.append({
                        'sheet': sheet_name,
                        'group': UNIT_GROUPS.get(sheet_name, "未分组"),
                        'status': '无权限',
                        'content': None,
                        'link': link
                    })
                elif content.startswith("访问出错") or content.startswith("提取出错"):
                    print(f"  结果: {content[:50]}...")
                    results.append({
                        'sheet': sheet_name,
                        'group': UNIT_GROUPS.get(sheet_name, "未分组"),
                        'status': '错误',
                        'content': content,
                        'link': link
                    })
                else:
                    print(f"  结果: 成功提取（{len(content)} 字符）")
                    results.append({
                        'sheet': sheet_name,
                        'group': UNIT_GROUPS.get(sheet_name, "未分组"),
                        'status': '成功',
                        'content': content,
                        'link': link
                    })

                # 返回主页面
                print(f"  返回主页面...")
                main_url = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"
                await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(2000)

            # 生成报告
            print("\n" + "="*80)
            print("汇总报告")
            print("="*80)
            print()

            # 统计
            total = len(results)
            success_count = sum(1 for r in results if r['status'] == '成功')
            no_link_count = sum(1 for r in results if r['status'] == '无')
            no_permission_count = sum(1 for r in results if r['status'] == '无权限')
            no_table_count = sum(1 for r in results if r['status'] == '无表格')
            error_count = sum(1 for r in results if r['status'] in ['错误', '无法访问'])

            print(f"总计: {total} 个业务单元")
            print(f"  ✓ 成功提取: {success_count}")
            print(f"  - 无听记链接: {no_link_count}")
            print(f"  - 无表格数据: {no_table_count}")
            print(f"  ⚠ 无权限: {no_permission_count}")
            print(f"  ✗ 错误/无法访问: {error_count}")
            print()

            # 详细结果
            if success_count > 0:
                print("-"*80)
                print("成功提取的业务单元:")
                print("-"*80)

                # 按分组展示
                from collections import defaultdict
                groups_results = defaultdict(list)
                for r in results:
                    if r['status'] == '成功':
                        groups_results[r['group']].append(r)

                # 按分组顺序展示（保持配置文件顺序）
                displayed_groups = []
                for r in results:
                    if r['status'] == '成功' and r['group'] not in displayed_groups:
                        displayed_groups.append(r['group'])

                for group_name in displayed_groups:
                    print(f"\n【{group_name}】")
                    print("-"*60)
                    for r in groups_results[group_name]:
                        print(f"\n  ▸ {r['sheet']}")
                        print(f"    链接: {r['link']}")
                        print(f"\n{r['content']}\n")

            if no_permission_count > 0:
                print("\n" + "-"*80)
                print("无权限的业务单元:")
                print("-"*80)
                for r in results:
                    if r['status'] == '无权限':
                        print(f"  - {r['sheet']}: {r['link']}")

            # 保存报告到文件
            import os
            from collections import defaultdict
            report_dir = os.path.expanduser("~/repos/dingcheck/data/daily_reports")
            os.makedirs(report_dir, exist_ok=True)
            report_file = os.path.join(report_dir, f"report_{target_date}.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"钉钉日会检查报告\n")
                f.write(f"="*80 + "\n")
                f.write(f"日期: {target_date}\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*80 + "\n\n")

                f.write(f"总体统计:\n")
                f.write(f"  总计: {total} 个业务单元\n")
                f.write(f"  ✓ 成功提取: {success_count}\n")
                f.write(f"  - 无听记链接: {no_link_count}\n")
                f.write(f"  - 无表格数据: {no_table_count}\n")
                f.write(f"  ⚠ 无权限: {no_permission_count}\n")
                f.write(f"  ✗ 错误/无法访问: {error_count}\n\n")

                # 按分组统计
                f.write("="*80 + "\n")
                f.write("分组统计\n")
                f.write("="*80 + "\n\n")

                groups_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'no_link': 0, 'no_permission': 0, 'error': 0})
                for r in results:
                    group = r['group']
                    groups_stats[group]['total'] += 1
                    if r['status'] == '成功':
                        groups_stats[group]['success'] += 1
                    elif r['status'] == '无':
                        groups_stats[group]['no_link'] += 1
                    elif r['status'] == '无权限':
                        groups_stats[group]['no_permission'] += 1
                    elif r['status'] in ['错误', '无法访问', '无表格']:
                        groups_stats[group]['error'] += 1

                # 按配置文件顺序显示分组统计
                displayed_groups = []
                for r in results:
                    if r['group'] not in displayed_groups:
                        displayed_groups.append(r['group'])

                for group_name in displayed_groups:
                    stats = groups_stats[group_name]
                    f.write(f"【{group_name}】\n")
                    f.write(f"  总计: {stats['total']} | 成功: {stats['success']} | 无链接: {stats['no_link']} | 无权限: {stats['no_permission']} | 错误: {stats['error']}\n\n")

                # 详细内容 - 按分组展示
                f.write("\n" + "="*80 + "\n")
                f.write("详细内容\n")
                f.write("="*80 + "\n\n")

                for group_name in displayed_groups:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"【{group_name}】\n")
                    f.write(f"{'='*80}\n\n")

                    # 找出该分组的所有单元
                    group_results = [r for r in results if r['group'] == group_name]

                    for r in group_results:
                        f.write(f"\n{'-'*80}\n")
                        f.write(f"▸ {r['sheet']}\n")
                        f.write(f"{'-'*80}\n")
                        f.write(f"状态: {r['status']}\n")
                        if r['link']:
                            f.write(f"链接: {r['link']}\n")
                        # 不再输出转写内容，只保留评分和分析
                        # if r['content'] and r['status'] == '成功':
                        #     f.write(f"\n内容:\n{r['content']}\n")

                # 进行AI分析并追加到报告
                ai_analysis = analyze_with_ai(results, target_date)
                f.write(ai_analysis)

            print(f"\n报告已保存到: {report_file}")

            # 显示AI分析结果
            if success_count > 0:
                print(ai_analysis)

            print("="*80)

        except Exception as e:
            print(f"✗ 错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # 如果没有提供日期参数，使用当天日期
    if len(sys.argv) < 2:
        target_date = date.today().strftime('%Y-%m-%d')
        print(f"未指定日期，使用当天日期: {target_date}\n")
    else:
        target_date = sys.argv[1]

    asyncio.run(batch_check_auto(target_date))

