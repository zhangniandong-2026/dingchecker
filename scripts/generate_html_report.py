#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成可视化HTML报告
"""

import sys
import os
import re
from datetime import datetime
import json

def parse_score_from_line(line):
    """从评分行中提取分数"""
    # 匹配格式如："🎯 战果汇报质量：4分" 或 "🎯 目标清晰度：4分"
    match = re.search(r'[:：](\d+)分', line)
    if match:
        return int(match.group(1))
    return 0

def parse_unit_scores(content):
    """解析每个业务单元的评分"""
    units = []
    current_unit = None

    lines = content.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()

        # 检测业务单元标题 - 可能的格式：
        # ## 一、华北一组 或 一、华北一组 或 ### 华北一组 或 **华北一组**
        if re.match(r'^##\s*[一二三四五六七八九十]+、', line):
            # 格式：## 一、华北一组
            unit_name = re.sub(r'^##\s*[一二三四五六七八九十]+、\s*', '', line).strip()
            if current_unit:
                units.append(current_unit)
            current_unit = {
                'name': unit_name,
                'scores': {},
                'total': 0,
                'percentage': 0
            }
        elif re.match(r'^[一二三四五六七八九十]+、', line):
            # 格式：一、华北一组
            unit_name = re.sub(r'^[一二三四五六七八九十]+、\s*', '', line).strip()
            if current_unit:
                units.append(current_unit)
            current_unit = {
                'name': unit_name,
                'scores': {},
                'total': 0,
                'percentage': 0
            }

        # 检测综合得分行
        elif current_unit and '综合得分' in line:
            # 格式：综合得分：21/25 (84%)
            match = re.search(r'(\d+)/(\d+)\s*\((\d+)%\)', line)
            if match:
                current_unit['total'] = int(match.group(1))
                current_unit['percentage'] = int(match.group(3))

        # 检测各维度评分
        elif current_unit:
            # 战果汇报质量
            if '战果汇报质量' in line or '目标清晰度' in line:
                current_unit['scores']['战果汇报'] = parse_score_from_line(line)
            # 任务聚焦度
            elif '任务聚焦度' in line or '复盘闭环率' in line:
                current_unit['scores']['任务聚焦'] = parse_score_from_line(line)
            # 协同效率
            elif '协同效率' in line or '协作敏捷度' in line:
                current_unit['scores']['协同效率'] = parse_score_from_line(line)
            # 情报敏感度
            elif '情报敏感度' in line or '信息增量' in line:
                current_unit['scores']['情报敏感'] = parse_score_from_line(line)
            # 领导点评效率
            elif '领导点评效率' in line or '问题聚焦度' in line:
                current_unit['scores']['点评效率'] = parse_score_from_line(line)

    # 添加最后一个单元
    if current_unit:
        units.append(current_unit)

    return units

def generate_html_report(report_file, output_file):
    """生成HTML可视化报告"""

    # 读取报告内容
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取报告日期和生成时间
    report_date = ''
    generate_time = ''

    lines = content.split('\n')
    for line in lines[:20]:
        if line.startswith('日期:'):
            report_date = line.replace('日期:', '').strip()
        elif line.startswith('生成时间:'):
            generate_time = line.replace('生成时间:', '').strip()

    # 解析业务单元评分
    units = parse_unit_scores(content)

    # 按总分排序
    units.sort(key=lambda x: x.get('total', 0), reverse=True)

    # 计算平均分
    if units:
        avg_total = sum(u.get('total', 0) for u in units) / len(units)
        avg_percentage = sum(u.get('percentage', 0) for u in units) / len(units)
    else:
        avg_total = 0
        avg_percentage = 0

    # 找出各维度最高分
    dimension_best = {
        '战果汇报': {'unit': '暂无数据', 'score': 0},
        '任务聚焦': {'unit': '暂无数据', 'score': 0},
        '协同效率': {'unit': '暂无数据', 'score': 0},
        '情报敏感': {'unit': '暂无数据', 'score': 0},
        '点评效率': {'unit': '暂无数据', 'score': 0}
    }

    for unit in units:
        for dim, score in unit.get('scores', {}).items():
            if score > dimension_best[dim]['score']:
                dimension_best[dim]['score'] = score
                dimension_best[dim]['unit'] = unit['name']

    # 处理无数据情况
    if not units:
        # 返回一个空报告
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>早会质量评估报告 - {report_date}</title>
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
    <title>早会质量评估报告 - {report_date}</title>
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
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 早会质量评估报告</h1>
            <div class="date">📅 {report_date}</div>
            <div class="generate-time">🕐 生成时间：{generate_time}</div>
        </div>

        <div class="summary-cards">
            <div class="summary-card">
                <div class="icon">📈</div>
                <div class="label">参评单元数</div>
                <div class="value">{len(units)}</div>
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
                <div class="unit-name">{units[0]['name']}</div>
            </div>

            <div class="summary-card">
                <div class="icon">🎯</div>
                <div class="label">战果汇报最佳</div>
                <div class="value">{dimension_best['战果汇报']['score']}/5</div>
                <div class="unit-name">{dimension_best['战果汇报']['unit']}</div>
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
                        <td><strong>{unit['name']}</strong></td>
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
    dim_averages = {
        '战果汇报': 0,
        '任务聚焦': 0,
        '协同效率': 0,
        '情报敏感': 0,
        '点评效率': 0
    }

    if units:
        for dim in dim_averages.keys():
            total = sum(u.get('scores', {}).get(dim, 0) for u in units)
            dim_averages[dim] = round(total / len(units), 1)

    # JavaScript 数据
    top_units = units[:10]
    unit_names = [u['name'] for u in top_units]
    unit_scores = [u['total'] for u in top_units]

    html += f"""                </tbody>
            </table>
        </div>

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
                    data: {json.dumps([dim_averages[k] for k in ['战果汇报', '任务聚焦', '协同效率', '情报敏感', '点评效率']])},
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
        print('使用方法: python3 generate_html_report.py <report_file> [output_file]')
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
