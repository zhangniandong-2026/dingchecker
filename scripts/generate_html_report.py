#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成可视化HTML报告
"""

import sys
import os
import json
from html import escape

from report_data import DIMENSION_KEYS, load_report_data


def build_meeting_guidance_html():
    """构建报告开篇的晨会建议模块"""
    return """
        <div class="guidance-card">
            <div class="section-title">业务单元每日晨会建议</div>

            <div class="guidance-section">
                <h3>一、会议基本信息</h3>
                <ul>
                    <li><strong>适用对象：</strong>各业务单元全体销售、售前及负责人。</li>
                    <li><strong>会议时间：</strong>每日 08:30 - 09:30（严格控制在 30 分钟内）。</li>
                    <li><strong>会议形式：</strong>开启录音/转写设备。</li>
                </ul>
            </div>

            <div class="guidance-section">
                <h3>二、汇报内容规范（“3+1”结构化模板）</h3>
                <p class="guidance-intro">汇报者必须按照以下顺序发言，以便 AI 提取关键字段：</p>

                <div class="guidance-grid">
                    <div class="guidance-item">
                        <h4>昨日战果（Results）</h4>
                        <p><strong>规范：</strong>必须包含具体数据或进展（如：签单金额、完成初访、方案交付）。</p>
                        <p><strong>评价点：</strong>目标达成率、动作量化程度。</p>
                    </div>

                    <div class="guidance-item">
                        <h4>今日头号任务（Focus）</h4>
                        <p><strong>规范：</strong>仅限 1-3 项核心任务，必须有明确的客户名称和预期结果。</p>
                        <p><strong>评价点：</strong>优先级意识、目标清晰度。</p>
                    </div>

                    <div class="guidance-item">
                        <h4>项目协同与求助（Support）</h4>
                        <p><strong>规范：</strong>明确提出“谁、在什么时间、支持什么细节”。若无需求请说“今日无协同需求”。</p>
                        <p><strong>评价点：</strong>团队协作敏捷度、资源对齐速度。</p>
                    </div>

                    <div class="guidance-item">
                        <h4>市场微情报（Insights）</h4>
                        <p><strong>规范：</strong>简短描述竞品动态或客户反馈的一句话。</p>
                        <p><strong>评价点：</strong>市场敏感度。</p>
                    </div>
                </div>
            </div>

            <div class="guidance-section">
                <h3>三、负责人点评规范</h3>
                <p class="guidance-intro">负责人点评需遵循 “定调子、给资源、控节奏”：</p>
                <ul>
                    <li><strong>禁止：</strong>在晨会上深入讨论超过 3 分钟的技术方案细节。</li>
                    <li><strong>要求：</strong>针对销售/售前的协同需求，必须现场给出明确回应（“散会后对接”或“下午 2 点开专项会”）。</li>
                    <li><strong>评价点：</strong>领导力决策效率、点评互动比（建议负责人发言时长占比 20%-30%）。</li>
                </ul>
            </div>

            <div class="guidance-section guidance-redline">
                <h3>五、会议纪律“红线”</h3>
                <ul>
                    <li><strong>超时：</strong>单人汇报超过 2 分钟，主持人需强制打断。</li>
                    <li><strong>无关话题：</strong>严禁讨论与当日业务动作无关的行政杂事。</li>
                </ul>
            </div>
        </div>
"""


def render_bullet_list(items, empty_text="暂无内容"):
    """渲染项目列表。"""
    if not items:
        return f'<p class="empty-text">{escape(empty_text)}</p>'
    list_items = ''.join(f"<li>{escape(str(item))}</li>" for item in items)
    return f"<ul>{list_items}</ul>"


def render_group_summary_html(groups):
    """渲染分组采集概览。"""
    if not groups:
        return ""

    cards = []
    for group in groups:
        cards.append(
            f"""
            <div class="group-card">
                <div class="group-name">{escape(group.get('name', '未分组'))}</div>
                <div class="group-stats">
                    <span>总计 {group.get('total', 0)}</span>
                    <span>成功 {group.get('success', 0)}</span>
                    <span>无链接 {group.get('no_link', 0)}</span>
                    <span>无权限 {group.get('no_permission', 0)}</span>
                    <span>错误 {group.get('error', 0)}</span>
                </div>
            </div>
            """
        )

    return f"""
        <div class="table-card">
            <h3>🗂️ 采集分组概览</h3>
            <div class="group-grid">
                {''.join(cards)}
            </div>
        </div>
    """


def render_capture_results_html(results):
    """渲染采集结果表。"""
    if not results:
        return ""

    rows = []
    for item in results:
        status = item.get("status", "")
        discipline_alerts = item.get("discipline_alerts", [])
        status_class = {
            "成功": "status-success",
            "无权限": "status-warning",
            "无": "status-muted",
            "无表格": "status-muted",
            "错误": "status-danger",
            "无法访问": "status-danger",
        }.get(status, "status-muted")

        link = item.get("link")
        link_html = f'<a href="{escape(link)}" target="_blank" rel="noopener noreferrer">打开链接</a>' if link else "-"
        discipline_html = (
            f'<span class="discipline-pill">{len(discipline_alerts)} 段超2分钟</span>' if discipline_alerts else "-"
        )
        rows.append(
            f"""
                <tr>
                    <td>{escape(item.get('group', '未分组'))}</td>
                    <td><strong>{escape(item.get('sheet', ''))}</strong></td>
                    <td><span class="status-pill {status_class}">{escape(status)}</span></td>
                    <td>{item.get('content_length', 0)}</td>
                    <td>{discipline_html}</td>
                    <td>{link_html}</td>
                </tr>
            """
        )

    return f"""
        <div class="table-card">
            <h3>📥 采集结果明细</h3>
            <table>
                <thead>
                    <tr>
                        <th>分组</th>
                        <th>业务单元</th>
                        <th>状态</th>
                        <th>转写字数</th>
                        <th>纪律提醒</th>
                        <th>链接</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
    """


def render_discipline_alerts_html(results):
    """渲染跨业务单元的会议纪律提醒。"""
    items = []
    for result in results:
        for alert in result.get("discipline_alerts", []):
            time_range = " - ".join(
                part for part in [alert.get("start_label", "").strip(), alert.get("end_label", "").strip()] if part
            )
            time_range_html = f" | {escape(time_range)}" if time_range else ""
            excerpt = alert.get("excerpt", "").strip()
            excerpt_html = f'<div class="discipline-excerpt">{escape(excerpt)}</div>' if excerpt else ""
            items.append(
                f"""
                <div class="discipline-item">
                    <div class="discipline-item-head">
                        <strong>{escape(result.get('sheet', ''))}</strong>
                        <span>{escape(alert.get('speaker', '未知发言人'))} 连续发言 {escape(alert.get('duration_label', ''))}{time_range_html}</span>
                    </div>
                    {excerpt_html}
                </div>
                """
            )

    if not items:
        return ""

    return f"""
        <div class="table-card">
            <h3>⏱️ 会议纪律提醒</h3>
            <p class="discipline-intro">根据转写时间戳自动识别单人连续发言超过 2 分钟的片段，便于复盘主持节奏和控时情况。</p>
            <div class="discipline-list">
                {''.join(items)}
            </div>
        </div>
    """


def render_unit_detail_cards(units):
    """渲染业务单元详细诊断。"""
    if not units:
        return ""

    priority_meta = [
        ("high", "🔴 高优先级"),
        ("medium", "🟡 中优先级"),
        ("low", "🟢 低优先级"),
    ]
    unit_cards = []

    for unit in units:
        dimensions = unit.get("dimensions", {})
        scores = unit.get("scores", {})
        discipline_alerts = unit.get("discipline_alerts", [])
        dimension_cards = []

        for dimension in DIMENSION_KEYS:
            detail = dimensions.get(dimension, {})
            score = detail.get("score", scores.get(dimension, 0))
            strengths_html = render_bullet_list(detail.get("strengths", []), "未提取到明确优点")
            improvements_html = render_bullet_list(detail.get("improvements", []), "未提取到明确改进项")
            highlight = detail.get("highlight", "").strip()
            highlight_html = (
                f'<div class="highlight-box">✨ 亮点：{escape(highlight)}</div>' if highlight else ""
            )
            dimension_cards.append(
                f"""
                <div class="dimension-card">
                    <div class="dimension-card-head">
                        <h4>{escape(dimension)}</h4>
                        <span class="dimension-score">{score}/5</span>
                    </div>
                    {highlight_html}
                    <div class="detail-block">
                        <div class="detail-label">优点</div>
                        {strengths_html}
                    </div>
                    <div class="detail-block">
                        <div class="detail-label">待改进</div>
                        {improvements_html}
                    </div>
                </div>
                """
            )

        priority_cards = []
        suggestions = unit.get("priority_suggestions", {})
        for key, label in priority_meta:
            priority_cards.append(
                f"""
                <div class="priority-card priority-{key}">
                    <div class="priority-title">{label}</div>
                    {render_bullet_list(suggestions.get(key, []), "暂无建议")}
                </div>
                """
            )

        discipline_html = ""
        if discipline_alerts:
            alert_cards = []
            for alert in discipline_alerts:
                time_range = " - ".join(
                    part for part in [alert.get("start_label", "").strip(), alert.get("end_label", "").strip()] if part
                )
                time_range_html = f" | {escape(time_range)}" if time_range else ""
                excerpt = alert.get("excerpt", "").strip()
                excerpt_html = f'<div class="discipline-excerpt">{escape(excerpt)}</div>' if excerpt else ""
                alert_cards.append(
                    f"""
                    <div class="discipline-alert-card">
                        <div class="discipline-alert-title">{escape(alert.get('speaker', '未知发言人'))}</div>
                        <div class="discipline-alert-meta">连续发言 {escape(alert.get('duration_label', ''))}{time_range_html}</div>
                        {excerpt_html}
                    </div>
                    """
                )
            discipline_html = f"""
                <div class="discipline-alert-section">
                    <div class="discipline-section-title">会议纪律提醒</div>
                    <div class="discipline-alert-grid">
                        {''.join(alert_cards)}
                    </div>
                </div>
            """

        unit_cards.append(
            f"""
            <section class="unit-detail-card">
                <div class="unit-detail-header">
                    <div>
                        <div class="unit-rank">#{unit.get('rank', '-')}</div>
                        <h3>{escape(unit.get('name', ''))}</h3>
                    </div>
                    <div class="unit-summary-meta">
                        <span class="total-score">{unit.get('total', 0)}/{unit.get('max_total', 25)}</span>
                        <span class="total-percentage">{unit.get('percentage', 0)}%</span>
                    </div>
                </div>

                <div class="dimensions-detail-grid">
                    {''.join(dimension_cards)}
                </div>

                {discipline_html}

                <div class="priority-grid">
                    {''.join(priority_cards)}
                </div>
            </section>
            """
        )

    return f"""
        <div class="detail-section">
            <div class="table-card">
                <h3>🧠 业务单元详细诊断</h3>
                <div class="unit-detail-list">
                    {''.join(unit_cards)}
                </div>
            </div>
        </div>
    """


def render_raw_analysis_html(raw_text):
    """渲染原始 AI 文本，便于兼容追溯。"""
    if not raw_text:
        return ""

    return f"""
        <div class="table-card raw-analysis-card">
            <details>
                <summary>查看原始 AI 报告文本</summary>
                <pre>{escape(raw_text)}</pre>
            </details>
        </div>
    """

def generate_html_report(report_file, output_file):
    """生成HTML可视化报告"""
    report_data = load_report_data(report_file)
    metadata = report_data.get('metadata', {})
    summary = report_data.get('summary', {})
    analysis = report_data.get('analysis', {})
    groups = report_data.get('groups', [])
    results = report_data.get('results', [])
    raw_text = analysis.get('raw_text', '')

    report_title = metadata.get('title', '早会质量评估报告')
    report_date = metadata.get('report_date', '')
    generate_time = metadata.get('generated_at', '')
    units = analysis.get('units', [])
    avg_total = summary.get('average_total', 0)
    avg_percentage = summary.get('average_percentage', 0)
    dimension_best = analysis.get('dimension_best', {})
    evaluated_unit_count = summary.get('evaluated_unit_count', len(units))

    meeting_guidance_html = build_meeting_guidance_html()
    group_summary_html = render_group_summary_html(groups)
    capture_results_html = render_capture_results_html(results)
    discipline_alerts_html = render_discipline_alerts_html(results)
    unit_detail_html = render_unit_detail_cards(units)
    raw_analysis_html = render_raw_analysis_html(raw_text)

    # 处理无数据情况
    if not units:
        # 返回一个空报告
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(str(report_title))} - {escape(str(report_date))}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .message {{
            background: white;
            border-radius: 16px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .message h1 {{
            font-size: 36px;
            color: #1a73e8;
            margin-bottom: 20px;
        }}
        .message p {{
            font-size: 18px;
            color: #5f6368;
        }}
    </style>
</head>
<body>
    <div class="message">
        <p style="margin-bottom: 12px; color: #1a73e8; font-weight: 600;">{escape(str(report_title))}</p>
        <h1>⚠️ 无评分数据</h1>
        <p>该报告中未找到可解析的评分数据</p>
        <p style="margin-top: 20px; font-size: 14px; color: #80868b;">
            请确保报告使用"3+1"结构化模板生成，并包含评分信息
        </p>
    </div>
</body>
</html>
"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        return True

    # 生成HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(str(report_title))} - {escape(str(report_date))}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .header h1 {{
            font-size: 36px;
            color: #1a73e8;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .header .date {{
            font-size: 18px;
            color: #5f6368;
            margin-bottom: 5px;
        }}

        .header .generate-time {{
            font-size: 14px;
            color: #80868b;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .guidance-card {{
            background: white;
            border-radius: 12px;
            padding: 28px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }}

        .section-title {{
            font-size: 24px;
            color: #1a73e8;
            font-weight: 700;
            margin-bottom: 24px;
        }}

        .guidance-section {{
            margin-bottom: 22px;
        }}

        .guidance-section:last-child {{
            margin-bottom: 0;
        }}

        .guidance-section h3 {{
            font-size: 18px;
            color: #202124;
            margin-bottom: 12px;
        }}

        .guidance-section h4 {{
            font-size: 16px;
            color: #1a73e8;
            margin-bottom: 10px;
        }}

        .guidance-section ul {{
            padding-left: 20px;
            color: #3c4043;
            line-height: 1.8;
        }}

        .guidance-section li {{
            margin-bottom: 6px;
        }}

        .guidance-intro {{
            color: #5f6368;
            margin-bottom: 14px;
            line-height: 1.7;
        }}

        .guidance-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
        }}

        .guidance-item {{
            border: 1px solid #e8eaed;
            border-radius: 10px;
            padding: 16px;
            background: #fafbff;
        }}

        .guidance-item p {{
            color: #3c4043;
            line-height: 1.7;
            margin-bottom: 8px;
        }}

        .guidance-item p:last-child {{
            margin-bottom: 0;
        }}

        .guidance-redline {{
            border-top: 1px solid #f1d5d1;
            padding-top: 18px;
        }}

        .summary-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .summary-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }}

        .summary-card .icon {{
            font-size: 32px;
            margin-bottom: 10px;
        }}

        .summary-card .label {{
            font-size: 14px;
            color: #5f6368;
            margin-bottom: 8px;
        }}

        .summary-card .value {{
            font-size: 32px;
            font-weight: 700;
            color: #1a73e8;
        }}

        .summary-card .unit-name {{
            font-size: 16px;
            color: #34a853;
            margin-top: 8px;
            font-weight: 600;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}

        .chart-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}

        .chart-card h3 {{
            font-size: 20px;
            color: #1a73e8;
            margin-bottom: 20px;
            font-weight: 600;
        }}

        .chart-container {{
            position: relative;
            height: 300px;
        }}

        .table-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 30px;
            overflow-x: auto;
        }}

        .table-card h3 {{
            font-size: 20px;
            color: #1a73e8;
            margin-bottom: 20px;
            font-weight: 600;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th {{
            background: #f1f3f4;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #1a73e8;
            border-bottom: 2px solid #dadce0;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #e8eaed;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .rank {{
            display: inline-block;
            width: 30px;
            height: 30px;
            line-height: 30px;
            text-align: center;
            border-radius: 50%;
            font-weight: 700;
            color: white;
        }}

        .rank-1 {{ background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%); color: #333; }}
        .rank-2 {{ background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%); color: #333; }}
        .rank-3 {{ background: linear-gradient(135deg, #cd7f32 0%, #e6a965 100%); color: white; }}
        .rank-other {{ background: #dadce0; color: #5f6368; }}

        .score-bar {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .score-bar-bg {{
            flex: 1;
            height: 8px;
            background: #e8eaed;
            border-radius: 4px;
            overflow: hidden;
        }}

        .score-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #34a853 0%, #5bb974 100%);
            border-radius: 4px;
            transition: width 1s ease;
        }}

        .score-value {{
            font-weight: 600;
            color: #1a73e8;
            min-width: 60px;
        }}

        .group-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
        }}

        .group-card {{
            border: 1px solid #e8eaed;
            border-radius: 12px;
            padding: 18px;
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        }}

        .group-name {{
            font-size: 18px;
            font-weight: 700;
            color: #202124;
            margin-bottom: 10px;
        }}

        .group-stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            color: #5f6368;
            font-size: 14px;
        }}

        .group-stats span {{
            background: #eef3fd;
            color: #355f9f;
            border-radius: 999px;
            padding: 6px 10px;
        }}

        .discipline-pill {{
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 13px;
            font-weight: 700;
            background: #fff4e5;
            color: #b06000;
        }}

        .status-pill {{
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 13px;
            font-weight: 600;
        }}

        .status-success {{
            background: #e6f4ea;
            color: #137333;
        }}

        .status-warning {{
            background: #fef7e0;
            color: #b06000;
        }}

        .status-muted {{
            background: #f1f3f4;
            color: #5f6368;
        }}

        .status-danger {{
            background: #fce8e6;
            color: #c5221f;
        }}

        .detail-section {{
            margin-bottom: 30px;
        }}

        .unit-detail-list {{
            display: grid;
            gap: 22px;
        }}

        .unit-detail-card {{
            border: 1px solid #e8eaed;
            border-radius: 16px;
            padding: 24px;
            background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        }}

        .unit-detail-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 20px;
        }}

        .unit-detail-header h3 {{
            font-size: 24px;
            color: #202124;
            margin-top: 6px;
        }}

        .unit-rank {{
            font-size: 13px;
            color: #5f6368;
            font-weight: 700;
            letter-spacing: 0.08em;
        }}

        .unit-summary-meta {{
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 6px;
        }}

        .total-score {{
            font-size: 28px;
            color: #1a73e8;
            font-weight: 700;
        }}

        .total-percentage {{
            color: #5f6368;
            font-size: 15px;
        }}

        .dimensions-detail-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 18px;
        }}

        .dimension-card {{
            border: 1px solid #e8eaed;
            border-radius: 12px;
            padding: 16px;
            background: #fff;
        }}

        .dimension-card-head {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
        }}

        .dimension-card-head h4 {{
            font-size: 17px;
            color: #202124;
        }}

        .dimension-score {{
            background: #e8f0fe;
            color: #1a73e8;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 13px;
            font-weight: 700;
        }}

        .highlight-box {{
            background: #eef7ea;
            border-radius: 10px;
            padding: 10px 12px;
            color: #2d6a3d;
            line-height: 1.6;
            margin-bottom: 14px;
        }}

        .detail-block {{
            margin-top: 12px;
        }}

        .detail-label {{
            font-size: 13px;
            font-weight: 700;
            color: #5f6368;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .detail-block ul {{
            padding-left: 18px;
            color: #3c4043;
            line-height: 1.7;
        }}

        .detail-block li {{
            margin-bottom: 6px;
        }}

        .discipline-intro {{
            color: #5f6368;
            margin-bottom: 16px;
            line-height: 1.7;
        }}

        .discipline-list {{
            display: grid;
            gap: 14px;
        }}

        .discipline-item {{
            border: 1px solid #fde0b2;
            border-radius: 12px;
            padding: 14px 16px;
            background: #fffaf2;
        }}

        .discipline-item-head {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
            color: #6b4b00;
            line-height: 1.6;
        }}

        .discipline-alert-section {{
            margin-bottom: 18px;
        }}

        .discipline-section-title {{
            font-size: 14px;
            font-weight: 700;
            color: #b06000;
            margin-bottom: 12px;
            letter-spacing: 0.04em;
        }}

        .discipline-alert-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 14px;
        }}

        .discipline-alert-card {{
            border: 1px solid #fde0b2;
            border-radius: 12px;
            padding: 14px;
            background: #fffaf2;
        }}

        .discipline-alert-title {{
            font-size: 15px;
            font-weight: 700;
            color: #6b4b00;
            margin-bottom: 6px;
        }}

        .discipline-alert-meta {{
            font-size: 13px;
            color: #8a5b00;
            line-height: 1.6;
        }}

        .discipline-excerpt {{
            margin-top: 10px;
            font-size: 13px;
            color: #5f6368;
            line-height: 1.6;
        }}

        .priority-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
        }}

        .priority-card {{
            border-radius: 12px;
            padding: 16px;
            border: 1px solid #e8eaed;
        }}

        .priority-title {{
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .priority-card ul {{
            padding-left: 18px;
            line-height: 1.7;
            color: #3c4043;
        }}

        .priority-card li {{
            margin-bottom: 6px;
        }}

        .priority-high {{
            background: #fff4f4;
        }}

        .priority-medium {{
            background: #fff9eb;
        }}

        .priority-low {{
            background: #f3fbf4;
        }}

        .empty-text {{
            color: #80868b;
            font-size: 14px;
            line-height: 1.6;
        }}

        .raw-analysis-card details {{
            cursor: pointer;
        }}

        .raw-analysis-card summary {{
            font-weight: 700;
            color: #1a73e8;
            outline: none;
        }}

        .raw-analysis-card pre {{
            margin-top: 16px;
            padding: 16px;
            background: #f8f9fa;
            border-radius: 12px;
            white-space: pre-wrap;
            word-break: break-word;
            line-height: 1.7;
            color: #3c4043;
            font-size: 13px;
        }}

        .footer {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            color: #5f6368;
            font-size: 14px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}

        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}

            .unit-detail-header {{
                flex-direction: column;
            }}

            .unit-summary-meta {{
                align-items: flex-start;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {escape(str(report_title))}</h1>
            <div class="date">📅 {escape(str(report_date))}</div>
            <div class="generate-time">🕐 生成时间：{escape(str(generate_time))}</div>
        </div>

        {meeting_guidance_html}

        <div class="summary-cards">
            <div class="summary-card">
                <div class="icon">📈</div>
                <div class="label">参评单元数</div>
                <div class="value">{evaluated_unit_count}</div>
            </div>

            <div class="summary-card">
                <div class="icon">⭐</div>
                <div class="label">平均得分</div>
                <div class="value">{avg_total:.1f}/25</div>
                <div style="color: #5f6368; font-size: 16px; margin-top: 5px;">({avg_percentage:.1f}%)</div>
            </div>

            <div class="summary-card">
                <div class="icon">🏆</div>
                <div class="label">最高分</div>
                <div class="value">{units[0]['total']}/25</div>
                <div class="unit-name">{escape(units[0]['name'])}</div>
            </div>

            <div class="summary-card">
                <div class="icon">🎯</div>
                <div class="label">战果汇报最佳</div>
                <div class="value">{dimension_best['战果汇报']['score']}/5</div>
                <div class="unit-name">{escape(dimension_best['战果汇报']['unit'])}</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-card">
                <h3>📊 综合得分排名（TOP 10）</h3>
                <div class="chart-container">
                    <canvas id="rankingChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h3>🎯 五维度平均得分</h3>
                <div class="chart-container">
                    <canvas id="dimensionChart"></canvas>
                </div>
            </div>
        </div>

        {group_summary_html}

        {capture_results_html}

        {discipline_alerts_html}

        <div class="table-card">
            <h3>📋 详细评分表</h3>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>业务单元</th>
                        <th>战果汇报</th>
                        <th>任务聚焦</th>
                        <th>协同效率</th>
                        <th>情报敏感</th>
                        <th>点评效率</th>
                        <th>总分</th>
                        <th>百分比</th>
                    </tr>
                </thead>
                <tbody>
"""

    # 添加表格数据
    for i, unit in enumerate(units[:20], 1):  # 只显示前20名
        rank_class = f'rank-{i}' if i <= 3 else 'rank-other'
        scores = unit.get('scores', {})

        html += f"""                    <tr>
                        <td><span class="rank {rank_class}">#{i}</span></td>
                        <td><strong>{escape(unit['name'])}</strong></td>
                        <td>{scores.get('战果汇报', 0)}/5</td>
                        <td>{scores.get('任务聚焦', 0)}/5</td>
                        <td>{scores.get('协同效率', 0)}/5</td>
                        <td>{scores.get('情报敏感', 0)}/5</td>
                        <td>{scores.get('点评效率', 0)}/5</td>
                        <td><strong>{unit['total']}/25</strong></td>
                        <td>
                            <div class="score-bar">
                                <div class="score-bar-bg">
                                    <div class="score-bar-fill" style="width: {unit['percentage']}%"></div>
                                </div>
                                <span class="score-value">{unit['percentage']}%</span>
                            </div>
                        </td>
                    </tr>
"""

    # 计算各维度平均分
    dim_averages = analysis.get('dimension_averages', {key: 0 for key in DIMENSION_KEYS})

    # JavaScript 数据
    top_units = units[:10]
    unit_names = [u['name'] for u in top_units]
    unit_scores = [u['total'] for u in top_units]

    html += f"""                </tbody>
            </table>
        </div>

        {unit_detail_html}

        {raw_analysis_html}

        <div class="footer">
            💡 报告由 DingCheck + Google Gemini AI 生成 |
            📊 基于"3+1"结构化早会标准评估 |
            🔧 DingCheck 自动化检查工具
        </div>
    </div>

    <script>
        // 综合得分排名图表
        const rankingCtx = document.getElementById('rankingChart').getContext('2d');
        new Chart(rankingCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(unit_names, ensure_ascii=False)},
                datasets: [{{
                    label: '总分',
                    data: {json.dumps(unit_scores)},
                    backgroundColor: 'rgba(26, 115, 232, 0.8)',
                    borderColor: 'rgba(26, 115, 232, 1)',
                    borderWidth: 2,
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 25,
                        ticks: {{
                            stepSize: 5
                        }}
                    }}
                }}
            }}
        }});

        // 五维度雷达图
        const dimensionCtx = document.getElementById('dimensionChart').getContext('2d');
        new Chart(dimensionCtx, {{
            type: 'radar',
            data: {{
                labels: ['战果汇报', '任务聚焦', '协同效率', '情报敏感', '点评效率'],
                datasets: [{{
                    label: '平均得分',
                    data: {json.dumps([dim_averages.get(k, 0) for k in DIMENSION_KEYS])},
                    fill: true,
                    backgroundColor: 'rgba(52, 168, 83, 0.2)',
                    borderColor: 'rgb(52, 168, 83)',
                    pointBackgroundColor: 'rgb(52, 168, 83)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(52, 168, 83)'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 5,
                        ticks: {{
                            stepSize: 1
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('使用方法: python3 generate_html_report.py <report_file(.json/.txt)> [output_file]')
        sys.exit(1)

    report_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # 自动生成输出文件名
        base_name = os.path.splitext(report_file)[0]
        output_file = f'{base_name}.html'

    if not os.path.exists(report_file):
        print(f'❌ 报告文件不存在: {report_file}')
        sys.exit(1)

    if generate_html_report(report_file, output_file):
        print(f'✅ HTML可视化报告已生成: {output_file}')
    else:
        print(f'❌ HTML报告生成失败')
        sys.exit(1)
