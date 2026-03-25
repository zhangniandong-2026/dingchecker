#!/usr/bin/env python3
"""每日自动检查所有业务单元的AI听记"""
import asyncio
import sys
import re
import os
import json
import shutil
from playwright.async_api import async_playwright
from datetime import datetime, date

from cdp_helper import connect_browser_over_cdp
from gemini_sdk import GEMINI_AVAILABLE, generate_text
from report_data import build_report_data, render_text_report

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMESTAMP_LINE_RE = re.compile(r'^\[?(\d{1,2}):(\d{2})(?::(\d{2}))?\]?$')


def parse_timestamp_seconds(line: str):
    """将 00:00 / 00:00:00 格式转成秒。"""
    match = TIMESTAMP_LINE_RE.match((line or "").strip())
    if not match:
        return None

    first = int(match.group(1))
    second = int(match.group(2))
    third = match.group(3)
    if third is None:
        return first * 60 + second
    return first * 3600 + second * 60 + int(third)


def format_timestamp_label(total_seconds: int) -> str:
    """将秒数转为易读时间。"""
    total_seconds = max(int(total_seconds or 0), 0)
    hours, remain = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remain, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def parse_timed_transcript_segments(raw_content: str):
    """从带时间轴的转写文本中提取发言片段。"""
    if not raw_content:
        return []

    ignored_speakers = {"转写", "章节", "发言人", "AI纪要", "AI 纪要", "待办"}
    lines = [line.strip() for line in raw_content.splitlines() if line.strip()]
    segments = []
    index = 0

    while index < len(lines):
        start_seconds = parse_timestamp_seconds(lines[index])
        if start_seconds is None:
            index += 1
            continue

        cursor = index + 1
        speaker = ""
        speaker_candidates = []
        speech_lines = []
        while cursor < len(lines) and parse_timestamp_seconds(lines[cursor]) is None:
            line = lines[cursor]
            if not speaker and not speech_lines:
                if line in ignored_speakers:
                    cursor += 1
                    continue
                if len(line) <= 30:
                    speaker_candidates.append(line)
                    cursor += 1
                    continue
                speaker = speaker_candidates[-1] if speaker_candidates else "未知发言人"
                speech_lines.append(line)
            else:
                if not speaker:
                    speaker = speaker_candidates[-1] if speaker_candidates else "未知发言人"
                speech_lines.append(line)
            cursor += 1

        if not speaker and speaker_candidates:
            speaker = speaker_candidates[-1]

        if speaker and cursor < len(lines):
            segments.append(
                {
                    "speaker": speaker,
                    "start_seconds": start_seconds,
                    "text": " ".join(speech_lines).strip(),
                }
            )

        index = cursor

    return segments


def parse_transcribe_row_segments(rows):
    """从转写行结构中提取更稳定的发言片段。"""
    if not rows:
        return []

    ignored_speakers = {"转写", "章节", "发言人", "AI纪要", "AI 纪要", "待办"}
    segments = []

    for row in rows:
        if not row:
            continue

        lines = [line.strip() for line in str(row).splitlines() if line.strip()]
        if not lines:
            continue

        timestamp_index = None
        start_seconds = None
        for index, line in enumerate(lines):
            start_seconds = parse_timestamp_seconds(line)
            if start_seconds is not None:
                timestamp_index = index
                break

        if timestamp_index is None:
            continue

        speaker_candidates = [
            line for line in lines[:timestamp_index]
            if line not in ignored_speakers
        ]
        speaker = speaker_candidates[-1] if speaker_candidates else "未知发言人"
        text = " ".join(lines[timestamp_index + 1:]).strip()

        if not text:
            continue

        segments.append(
            {
                "speaker": speaker,
                "start_seconds": start_seconds,
                "text": text,
            }
        )

    return segments


def build_transcription_from_segments(segments):
    """将结构化发言片段重新组织为干净正文。"""
    if len(segments) < 2:
        return None

    lines = []
    for segment in segments:
        speaker = segment.get("speaker", "").strip()
        text = segment.get("text", "").strip()
        if not speaker or not text:
            continue
        lines.append(speaker)
        lines.append(text)

    transcription = "\n".join(lines).strip()
    return transcription if len(transcription) > 80 else None


def build_transcription_from_timed_segments(raw_content: str):
    """根据时间轴片段重建更干净的正文转写。"""
    segments = parse_timed_transcript_segments(raw_content)
    return build_transcription_from_segments(segments)


def extract_speech_discipline_alerts_from_segments(segments, threshold_seconds: int = 120):
    """基于发言片段识别超 2 分钟的连续发言。"""
    if len(segments) < 2:
        return []

    turns = []
    for current, following in zip(segments, segments[1:]):
        duration_seconds = following["start_seconds"] - current["start_seconds"]
        if duration_seconds <= 0 or duration_seconds > 3600:
            continue

        if (
            turns
            and turns[-1]["speaker"] == current["speaker"]
            and turns[-1]["end_seconds"] == current["start_seconds"]
        ):
            turns[-1]["end_seconds"] = following["start_seconds"]
            turns[-1]["duration_seconds"] += duration_seconds
            if not turns[-1]["excerpt"] and current["text"]:
                turns[-1]["excerpt"] = current["text"][:120]
            continue

        turns.append(
            {
                "speaker": current["speaker"],
                "start_seconds": current["start_seconds"],
                "end_seconds": following["start_seconds"],
                "duration_seconds": duration_seconds,
                "excerpt": current["text"][:120],
            }
        )

    alerts = []
    for turn in turns:
        if turn["duration_seconds"] <= threshold_seconds:
            continue
        alerts.append(
            {
                "speaker": turn["speaker"],
                "start_label": format_timestamp_label(turn["start_seconds"]),
                "end_label": format_timestamp_label(turn["end_seconds"]),
                "duration_seconds": turn["duration_seconds"],
                "duration_label": f"{turn['duration_seconds'] // 60}分{turn['duration_seconds'] % 60:02d}秒",
                "excerpt": turn["excerpt"],
            }
        )

    return alerts


def extract_speech_discipline_alerts(raw_content: str, threshold_seconds: int = 120):
    """基于转写时间戳识别超 2 分钟的连续发言。"""
    segments = parse_timed_transcript_segments(raw_content)
    return extract_speech_discipline_alerts_from_segments(segments, threshold_seconds)


async def capture_transcribe_panel_text(content_page):
    """滚动转写虚拟列表，尽量聚合完整正文。"""
    try:
        return await content_page.evaluate('''
            async () => {
                const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                const root = (
                    document.querySelector('.fm-transcribe-text__list') ||
                    document.querySelector('.fm-transcribe-text') ||
                    document.querySelector('[class*="transcribe"]')
                );

                if (!root) {
                    return null;
                }

                const findViewport = () => {
                    const directViewport = root.querySelector('[data-overlayscrollbars-viewport]');
                    if (directViewport && directViewport.scrollHeight > directViewport.clientHeight + 40) {
                        return directViewport;
                    }

                    const nestedScrollable = Array.from(root.querySelectorAll('*')).find((elem) => {
                        const style = window.getComputedStyle(elem);
                        return (
                            (style.overflowY === 'scroll' || style.overflowY === 'auto') &&
                            elem.scrollHeight > elem.clientHeight + 40
                        );
                    });
                    if (nestedScrollable) {
                        return nestedScrollable;
                    }

                    const hostViewport = document.querySelector('.fm-scroll-container [data-overlayscrollbars-viewport]');
                    if (hostViewport && hostViewport.scrollHeight > hostViewport.clientHeight + 40) {
                        return hostViewport;
                    }

                    return null;
                };

                const viewport = findViewport();
                const rowMap = new Map();
                const chunkMap = new Map();

                const captureVisibleText = () => {
                    const rows = Array.from(root.querySelectorAll('.fm-virtual-paragrah-row'));
                    rows.forEach((row, index) => {
                        const text = (row.innerText || '').trim();
                        if (!text) {
                            return;
                        }
                        const rowId = (row.id || '').trim();
                        const key = rowId || `row-${index}-${text.slice(0, 24)}`;
                        rowMap.set(key, text);
                    });

                    const chunkText = (root.innerText || '').trim();
                    if (chunkText) {
                        chunkMap.set(chunkText.slice(0, 120), chunkText);
                    }
                };

                captureVisibleText();

                if (viewport) {
                    viewport.scrollTop = 0;
                    await sleep(300);
                    captureVisibleText();

                    const step = Math.max(Math.floor(viewport.clientHeight * 0.75), 220);
                    const maxLoops = 80;

                    for (let loop = 0; loop < maxLoops; loop += 1) {
                        const maxScrollTop = Math.max(viewport.scrollHeight - viewport.clientHeight, 0);
                        if (viewport.scrollTop >= maxScrollTop) {
                            break;
                        }

                        const nextTop = Math.min(viewport.scrollTop + step, maxScrollTop);
                        if (nextTop <= viewport.scrollTop) {
                            break;
                        }

                        viewport.scrollTop = nextTop;
                        viewport.dispatchEvent(new Event('scroll', { bubbles: true }));
                        await sleep(500);
                        captureVisibleText();
                    }

                    viewport.scrollTop = Math.max(viewport.scrollHeight - viewport.clientHeight, 0);
                    viewport.dispatchEvent(new Event('scroll', { bubbles: true }));
                    await sleep(500);
                    captureVisibleText();
                }

                const orderedRows = Array.from(rowMap.entries())
                    .sort((left, right) => {
                        const leftNumber = Number(left[0]);
                        const rightNumber = Number(right[0]);

                        if (!Number.isNaN(leftNumber) && !Number.isNaN(rightNumber)) {
                            return leftNumber - rightNumber;
                        }

                        return left[0].localeCompare(right[0]);
                    })
                    .map((entry) => entry[1]);

                const orderedChunks = Array.from(chunkMap.values());
                const aggregatedText = (orderedRows.length >= 3 ? orderedRows : orderedChunks).join('\\n').trim();

                return {
                    text: aggregatedText,
                    rows: orderedRows,
                    row_count: orderedRows.length,
                    chunk_count: orderedChunks.length,
                    used_virtual_list: Boolean(viewport),
                    scroll_height: viewport ? viewport.scrollHeight : null,
                    client_height: viewport ? viewport.clientHeight : null,
                };
            }
        ''')
    except Exception:
        return None


def should_generate_txt_report():
    """兼容文本报告默认关闭，可按需开启。"""
    return os.environ.get('DINGCHECK_GENERATE_TXT', '0') == '1' or os.environ.get('DINGCHECK_GENERATE_PDF', '0') == '1'

def load_business_units_with_groups():
    """从配置文件加载业务单元列表，同时保留分组信息"""
    config_file = os.path.join(PROJECT_ROOT, "config", "business_units.txt")
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
            return "无表格", None, []

        async def page_looks_like_transcribe(target_page):
            """判断页面是否已经进入 AI 听记详情。"""
            try:
                signals = await target_page.evaluate(
                    """() => {
                        const text = (document.body && document.body.innerText) || '';
                        return {
                            text: text,
                            hasTab: text.includes('转写'),
                            hasSummary: text.includes('AI 纪要') || text.includes('AI纪要'),
                            hasTodo: text.includes('待办'),
                            hasSpeaker: text.includes('发言人'),
                        };
                    }"""
                )
            except Exception:
                return False

            text = signals.get('text', '')
            return any(
                [
                    signals.get('hasTab'),
                    signals.get('hasSummary'),
                    signals.get('hasTodo'),
                    signals.get('hasSpeaker'),
                    'shanji.dingtalk.com' in (target_page.url or ''),
                    ('transcribes' in (target_page.url or '')),
                    ('permission' in (target_page.url or '')),
                    ('AI 纪要' in text or 'AI纪要' in text),
                ]
            )

        # 策略：找到日期元素，然后尝试点击同一行右侧的候选入口
        result = await target_frame.evaluate('''
            (targetDate) => {
                function getXPath(element) {
                    if (!element) return '';
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

                // 1. 查找目标日期元素
                function findDateElement() {
                    const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
                    const matches = [];
                    const allElements = document.querySelectorAll('*');

                    for (const elem of allElements) {
                        if (elem.children.length !== 0) {
                            continue;
                        }

                        const text = elem.textContent.trim();
                        if (text !== targetDate) {
                            continue;
                        }

                        const rect = elem.getBoundingClientRect();
                        const visible =
                            rect.width > 0 &&
                            rect.height > 0 &&
                            rect.bottom > 0 &&
                            rect.top < viewportHeight;

                        matches.push({
                            element: elem,
                            rectTop: rect.top,
                            rectLeft: rect.left,
                            visible: visible,
                        });
                    }

                    if (matches.length === 0) {
                        return null;
                    }

                    matches.sort((a, b) => {
                        if (a.visible !== b.visible) {
                            return a.visible ? -1 : 1;
                        }
                        if (a.rectTop !== b.rectTop) {
                            return b.rectTop - a.rectTop;
                        }
                        return a.rectLeft - b.rectLeft;
                    });

                    return matches[0].element;
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

                // 4. 查找右侧的可点击候选元素
                const allElements = document.querySelectorAll('*');
                const candidates = [];
                const seenXPaths = new Set();

                function pickClickableTarget(element) {
                    let current = element;
                    while (current && current !== document.body) {
                        const href = current.getAttribute('href') || '';
                        const role = current.getAttribute('role') || '';
                        const tag = current.tagName || '';
                        const cursor = getComputedStyle(current).cursor;
                        const clickable = (
                            tag === 'A' ||
                            tag === 'BUTTON' ||
                            role === 'link' ||
                            role === 'button' ||
                            typeof current.onclick === 'function' ||
                            href ||
                            cursor === 'pointer'
                        );
                        if (clickable) {
                            return current;
                        }
                        current = current.parentElement;
                    }
                    return element;
                }

                for (const rawElement of allElements) {
                    const rect = rawElement.getBoundingClientRect();
                    if (rect.width <= 0 || rect.height <= 0) {
                        continue;
                    }

                    const centerY = rect.top + rect.height / 2;
                    const centerX = rect.left + rect.width / 2;
                    if (Math.abs(centerY - dateY) >= 24 || centerX <= dateRight - 120) {
                        continue;
                    }

                    const target = pickClickableTarget(rawElement);
                    if (!target) {
                        continue;
                    }

                    const targetRect = target.getBoundingClientRect();
                    if (targetRect.width <= 0 || targetRect.height <= 0) {
                        continue;
                    }

                    const xpath = getXPath(target);
                    if (!xpath || seenXPaths.has(xpath)) {
                        continue;
                    }
                    seenXPaths.add(xpath);

                    const href = target.getAttribute('href') || target.href || '';
                    const text = (target.innerText || target.textContent || '').trim();
                    const role = target.getAttribute('role') || '';
                    const tag = target.tagName || '';
                    const cursor = getComputedStyle(target).cursor;
                    const distanceX = targetRect.left - dateRight;
                    const distanceY = Math.abs((targetRect.top + targetRect.height / 2) - dateY);
                    const likelyMeetingEntry = (
                        href.includes('shanji.dingtalk.com') ||
                        text.includes('查看') ||
                        text.includes('听记') ||
                        text.includes('纪要') ||
                        text.includes('会议')
                    );

                    candidates.push({
                        xpath: xpath,
                        text: text,
                        href: href,
                        role: role,
                        tag: tag,
                        cursor: cursor,
                        distanceX: distanceX,
                        distanceY: distanceY,
                        likelyMeetingEntry: likelyMeetingEntry,
                    });
                }

                if (candidates.length === 0) {
                    return { success: false, reason: 'link-not-found', dateY: dateY };
                }

                // 5. 优先靠近日期、且更像会议入口的候选元素
                candidates.sort((a, b) => {
                    if (a.likelyMeetingEntry !== b.likelyMeetingEntry) {
                        return a.likelyMeetingEntry ? -1 : 1;
                    }
                    const distA = Math.sqrt(a.distanceX ** 2 + a.distanceY ** 2);
                    const distB = Math.sqrt(b.distanceX ** 2 + b.distanceY ** 2);
                    return distA - distB;
                });

                return {
                    success: true,
                    candidates: candidates.slice(0, 8),
                };
            }
        ''', target_date)

        if not result.get('success'):
            return "无", None, []

        # 点击候选入口，兼容新标签页和当前页跳转两种行为
        try:
            content_page = None
            link_url = None

            for candidate in result.get('candidates', []):
                initial_pages = list(page.context.pages)
                initial_page_urls = {pg: pg.url for pg in initial_pages}

                click_result = await target_frame.evaluate(
                    '''
                    (xpath) => {
                        const element = document.evaluate(xpath, document, null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        if (!element) {
                            return false;
                        }
                        element.scrollIntoView({ behavior: 'auto', block: 'center', inline: 'center' });
                        element.click();
                        return true;
                    }
                    ''',
                    candidate['xpath'],
                )

                if not click_result:
                    continue

                for _ in range(24):  # 24次 × 500ms = 12秒
                    await page.wait_for_timeout(500)

                    for pg in page.context.pages:
                        if pg not in initial_pages:
                            if await page_looks_like_transcribe(pg):
                                content_page = pg
                                break

                            try:
                                page_content = await pg.content()
                                if (
                                    'ERR_' in pg.url
                                    or 'chrome-error://' in pg.url
                                    or 'about:blank' in pg.url
                                    or '无法访问' in page_content
                                    or 'ERR_CONNECTION' in page_content
                                ):
                                    await pg.close()
                                else:
                                    await pg.close()
                            except Exception:
                                pass
                    if content_page:
                        break

                    if page.url != initial_page_urls.get(page, page.url):
                        if await page_looks_like_transcribe(page):
                            content_page = page
                            break

                if content_page:
                    link_url = content_page.url or candidate.get('href') or None
                    break

            if not content_page:
                return "无", None, []
        except Exception as e:
            return "无", None, []

        try:
            normalized_link_url = link_url.replace('/permission/', '/transcribes/') if link_url else None
            if normalized_link_url and normalized_link_url != content_page.url:
                await content_page.goto(normalized_link_url, wait_until='domcontentloaded', timeout=60000)
                link_url = normalized_link_url

            # 增加初始等待时间，给权限验证和页面挂载更多时间
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
                    return "无权限", link_url, []
                else:
                    print(f"  ✓ 权限验证通过（重试成功）")

            # 等待内容加载
            await content_page.wait_for_timeout(3000)

            # 点击"转写"标签页（默认打开的是"AI 纪要"）
            try:
                clicked = await content_page.evaluate('''
                    () => {
                        const candidates = [];
                        const selectors = [
                            '.dtd-tabs-tab',
                            '.dtd-tabs-tab-btn',
                            '[role="tab"]',
                            'button',
                            '[class*="tab"]'
                        ];

                        for (const selector of selectors) {
                            document.querySelectorAll(selector).forEach(elem => candidates.push(elem));
                        }

                        const seen = new Set();
                        for (const elem of candidates) {
                            if (!elem || seen.has(elem)) {
                                continue;
                            }
                            seen.add(elem);

                            const text = (elem.innerText || elem.textContent || '').trim();
                            if (!text || !text.includes('转写')) {
                                continue;
                            }

                            elem.click();
                            if (typeof elem.dispatchEvent === 'function') {
                                elem.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                            }
                            return true;
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

            transcribe_capture = await capture_transcribe_panel_text(content_page)
            row_segments = parse_transcribe_row_segments(
                transcribe_capture.get('rows') if transcribe_capture else None
            )
            raw_page_text = (
                transcribe_capture.get('text')
                if transcribe_capture and transcribe_capture.get('text')
                else await content_page.evaluate('() => document.body.innerText')
            )
            timed_transcription = (
                build_transcription_from_segments(row_segments)
                if row_segments
                else build_transcription_from_timed_segments(raw_page_text)
            )

            # 提取内容（只提取转写标签页的内容）
            content = await content_page.evaluate('''
                () => {
                    // 优先尝试提取转写内容区域
                    const transcribeSelectors = [
                        '.fm-transcribe-text__list',
                        '.fm-transcribe-text__auto-sizer',
                        '.fm-transcribe-text',
                        '[class*="transcribe"]',
                        '[class*="speech"]'
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

                    // 再降级：优先寻找包含多段时间戳的最小内容块
                    const blocks = Array.from(document.querySelectorAll('div, section, article, main'));
                    const transcriptCandidates = [];
                    for (const block of blocks) {
                        const text = (block.innerText || '').trim();
                        if (text.length < 100) {
                            continue;
                        }
                        const timestampCount = (text.match(/\b\d{2}:\d{2}(?::\d{2})?\b/g) || []).length;
                        if (timestampCount < 2) {
                            continue;
                        }
                        transcriptCandidates.push({
                            text,
                            timestampCount,
                            length: text.length,
                        });
                    }

                    if (transcriptCandidates.length > 0) {
                        transcriptCandidates.sort((a, b) => {
                            if (a.timestampCount !== b.timestampCount) {
                                return b.timestampCount - a.timestampCount;
                            }
                            return a.length - b.length;
                        });
                        return transcriptCandidates[0].text;
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
            
            if transcribe_capture and transcribe_capture.get('text'):
                content = transcribe_capture.get('text')
                if transcribe_capture.get('used_virtual_list'):
                    print(
                        f"  ✓ 已聚合转写全文（{transcribe_capture.get('row_count', 0)} 段，"
                        f"{len(content)} 字符）"
                    )

            discipline_alerts = (
                extract_speech_discipline_alerts_from_segments(row_segments)
                if row_segments
                else extract_speech_discipline_alerts(raw_page_text or content)
            )

            used_timed_transcription = False
            if timed_transcription:
                content = timed_transcription
                used_timed_transcription = True
                print(f"  ✓ 通过时间轴提取到语音转写（{len(content)} 字符）")

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
            
            if content_page != page:
                await content_page.close()
            
            if content and len(content) > 50:
                # 提取语音转写内容（完整的会议转写，而不是AI纪要）
                transcription = content if used_timed_transcription else None

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

                return transcription, link_url, discipline_alerts
            else:
                return "无", link_url, discipline_alerts
            
        except Exception as e:
            if content_page != page:
                await content_page.close()
            return f"访问出错: {str(e)[:100]}", link_url, []
    
    except Exception as e:
        return f"提取出错: {str(e)[:100]}", None, []

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
        analysis_text = generate_text(prompt, "gemini-2.5-flash", api_key=api_key)

        analysis = "\n\n" + "="*80 + "\n"
        analysis += "早会质量评估报告\n"
        analysis += "="*80 + "\n\n"
        analysis += analysis_text
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
            print("连接 Chrome 调试会话...")
            browser, browser_info = await connect_browser_over_cdp(p)
            print(
                f"✓ Chrome CDP 已连接: {browser_info['browser']} "
                f"(Protocol {browser_info['protocol_version']})"
            )
            if not browser.contexts:
                raise RuntimeError("Chrome CDP 已连接，但未发现可用浏览器上下文")
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
                        'link': None,
                        'discipline_alerts': []
                    })
                    continue

                print(f"  ✓ 已切换到工作表")

                # 提取内容
                content, link, discipline_alerts = await extract_content_for_current_sheet(page, target_date)

                if content == "无":
                    print(f"  结果: 无听记链接")
                    results.append({
                        'sheet': sheet_name,
                        'group': UNIT_GROUPS.get(sheet_name, "未分组"),
                        'status': '无',
                        'content': None,
                        'link': None,
                        'discipline_alerts': []
                    })
                elif content == "无表格":
                    print(f"  结果: 无表格数据")
                    results.append({
                        'sheet': sheet_name,
                        'group': UNIT_GROUPS.get(sheet_name, "未分组"),
                        'status': '无表格',
                        'content': None,
                        'link': None,
                        'discipline_alerts': []
                    })
                elif content == "无权限":
                    print(f"  结果: 无权限")
                    results.append({
                        'sheet': sheet_name,
                        'group': UNIT_GROUPS.get(sheet_name, "未分组"),
                        'status': '无权限',
                        'content': None,
                        'link': link,
                        'discipline_alerts': []
                    })
                elif content.startswith("访问出错") or content.startswith("提取出错"):
                    print(f"  结果: {content[:50]}...")
                    results.append({
                        'sheet': sheet_name,
                        'group': UNIT_GROUPS.get(sheet_name, "未分组"),
                        'status': '错误',
                        'content': content,
                        'link': link,
                        'discipline_alerts': []
                    })
                else:
                    print(f"  结果: 成功提取（{len(content)} 字符）")
                    if discipline_alerts:
                        print(f"  ⚠️ 会议纪律提醒：检测到 {len(discipline_alerts)} 段单人发言超过2分钟")
                    results.append({
                        'sheet': sheet_name,
                        'group': UNIT_GROUPS.get(sheet_name, "未分组"),
                        'status': '成功',
                        'content': content,
                        'link': link,
                        'discipline_alerts': discipline_alerts
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

            # 保存结构化报告与兼容文本报告
            report_dir = os.path.join(PROJECT_ROOT, "data", "daily_reports")
            os.makedirs(report_dir, exist_ok=True)
            generate_dt = datetime.now()
            generate_time = generate_dt.strftime('%Y-%m-%d %H:%M:%S')
            run_id = generate_dt.strftime('%Y%m%d-%H%M%S-%f')
            ai_analysis = analyze_with_ai(results, target_date)
            report_data = build_report_data(target_date, generate_time, results, ai_analysis, run_id=run_id)

            latest_json_file = os.path.join(report_dir, f"report_{target_date}.json")
            archive_json_file = os.path.join(report_dir, f"report_{target_date}__{run_id}.json")

            with open(archive_json_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            shutil.copyfile(archive_json_file, latest_json_file)

            report_file = None
            if should_generate_txt_report():
                archive_report_file = os.path.join(report_dir, f"report_{target_date}__{run_id}.txt")
                latest_report_file = os.path.join(report_dir, f"report_{target_date}.txt")
                with open(archive_report_file, 'w', encoding='utf-8') as f:
                    f.write(render_text_report(report_data))
                shutil.copyfile(archive_report_file, latest_report_file)
                report_file = latest_report_file

            print(f"结构化数据已保存到: {latest_json_file}")
            print(f"历史归档JSON已保存到: {archive_json_file}")
            if report_file:
                print(f"兼容文本报告已保存到: {report_file}")

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
