#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成美化的 PDF 报告（支持中文）
"""

import sys
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def register_chinese_fonts():
    """注册中文字体"""
    try:
        # 使用 macOS 系统自带的中文字体
        pdfmetrics.registerFont(TTFont('STHeiti', '/System/Library/Fonts/STHeiti Light.ttc', subfontIndex=0))
        pdfmetrics.registerFont(TTFont('STHeitiB', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=0))
        return True
    except Exception as e:
        print(f'⚠️  中文字体加载失败: {e}')
        return False

def create_pdf(report_file, output_file):
    """生成PDF报告"""

    # 注册中文字体
    if not register_chinese_fonts():
        print('❌ 无法加载中文字体，PDF生成失败')
        return False

    # 读取报告内容
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 创建PDF文档
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # 准备内容
    story = []

    # 定义样式（使用中文字体）
    styles = getSampleStyleSheet()

    # 标题样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='STHeitiB',
        fontSize=22,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=20,
        spaceBefore=10,
        alignment=TA_CENTER,
        leading=28
    )

    # 副标题样式
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontName='STHeiti',
        fontSize=11,
        textColor=colors.HexColor('#5f6368'),
        spaceAfter=20,
        alignment=TA_CENTER,
        leading=16
    )

    # 大标题样式
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading2'],
        fontName='STHeitiB',
        fontSize=15,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=10,
        spaceBefore=15,
        leading=20
    )

    # 小标题样式
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading3'],
        fontName='STHeitiB',
        fontSize=12,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=8,
        spaceBefore=10,
        leading=16
    )

    # 正文样式
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName='STHeiti',
        fontSize=10,
        leading=16,
        alignment=TA_LEFT,
        spaceAfter=4
    )

    # 粗体正文样式
    body_bold_style = ParagraphStyle(
        'CustomBodyBold',
        parent=body_style,
        fontName='STHeitiB',
    )

    # 提取报告日期和生成时间
    lines = content.split('\n')
    report_date = ''
    generate_time = ''

    for line in lines[:10]:
        if line.startswith('日期:'):
            report_date = line.replace('日期:', '').strip()
        elif line.startswith('生成时间:'):
            generate_time = line.replace('生成时间:', '').strip()

    # 添加标题
    story.append(Paragraph('早会质量评估报告', title_style))
    story.append(Paragraph(f'日期：{report_date}', subtitle_style))
    if generate_time:
        story.append(Paragraph(f'生成时间：{generate_time}', subtitle_style))
    story.append(Spacer(1, 0.5*cm))

    # 解析并添加内容
    in_ai_section = False
    in_unit_section = False
    current_unit = ''
    skip_next_separator = False

    for i, line in enumerate(lines):
        line = line.strip()

        # 跳过空行和分隔线
        if not line or line.startswith('='*20):
            if 'AI 智能分析' in line or '早会质量评估报告' in line or (i > 0 and ('AI 智能分析' in lines[i-1] or '早会质量评估报告' in lines[i-1])):
                # AI分析章节开始，添加分页
                story.append(PageBreak())
                story.append(Paragraph('早会质量评估报告', title_style))
                story.append(Spacer(1, 0.5*cm))
                in_ai_section = True
                skip_next_separator = True
            continue

        # 跳过报告头部（已经处理）
        if line in ['批量检查报告', report_date, generate_time]:
            continue

        # 统计信息
        if line.startswith('统计:'):
            story.append(Paragraph('<b>统计摘要</b>', heading1_style))
            continue

        if line.startswith(('总计:', '✓', '-', '⚠', '✗')):
            story.append(Paragraph(line, body_style))
            continue

        # 业务单元标题
        if line.startswith('业务单元:'):
            unit_name = line.replace('业务单元:', '').strip()
            current_unit = unit_name
            story.append(Spacer(1, 0.4*cm))
            story.append(Paragraph(f'业务单元：{unit_name}', heading1_style))
            in_unit_section = True
            continue

        # 状态和链接
        if line.startswith('状态:'):
            status = line.replace('状态:', '').strip()
            if status == '无':
                story.append(Paragraph(f'<font color="#999999">状态：{status}听记链接</font>', body_style))
            elif status == '成功':
                story.append(Paragraph(f'<font color="#34a853">状态：成功提取</font>', body_style))
            else:
                story.append(Paragraph(f'状态：{status}', body_style))
            continue

        if line.startswith('链接:'):
            link_url = line.replace('链接:', '').strip()
            story.append(Paragraph(f'<font color="#0066cc">链接：{link_url}</font>', body_style))
            story.append(Spacer(1, 0.2*cm))
            continue

        # 内容区域
        if line.startswith('内容:'):
            story.append(Paragraph('<b>会议内容：</b>', body_bold_style))
            continue

        # 主题、时间、参与人
        if line.startswith(('主题:', '时间:', '参与人:')):
            story.append(Paragraph(f'<b>{line}</b>', body_bold_style))
            continue

        # 检测一级标题（一、二、三、四、五）
        if line.startswith(('一、', '二、', '三、', '四、', '五、')):
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(f'<b>{line}</b>', heading2_style))
            continue

        # 检测业务单元标题（【xxx】格式）
        if line.startswith('【') and '】' in line:
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph(f'<b>{line}</b>', body_bold_style))
            continue

        # 检测二级标题（markdown格式）
        if line.startswith('**') and line.endswith('**'):
            clean_line = line.replace('**', '')
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph(f'<b>{clean_line}</b>', body_bold_style))
            continue

        # 检测分点标题
        if line.startswith(('*   **', '* **')) and '**' in line:
            # 提取粗体部分和其余内容
            parts = line.split('**')
            if len(parts) >= 3:
                bold_part = parts[1]
                rest_part = '**'.join(parts[2:])
                formatted_line = f'• <b>{bold_part}</b>{rest_part}'
                story.append(Paragraph(formatted_line, body_style))
                continue

        # 处理列表项
        if line.startswith(('* ', '- ', '• ')):
            clean_line = line[2:].strip()
            # 处理✨标记
            if '✨' in clean_line:
                clean_line = clean_line.replace('✨', '<font color="#ff6b35">✨</font>')
            story.append(Paragraph(f'  • {clean_line}', body_style))
            continue

        # 处理数字列表
        if len(line) > 2 and line[0].isdigit() and line[1] == '.':
            story.append(Paragraph(line, body_style))
            continue

        # 处理💡标记
        if '💡' in line:
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(line, body_style))
            continue

        # 处理分隔线
        if line.startswith('---'):
            story.append(Spacer(1, 0.2*cm))
            continue

        # 普通文本
        if line and not line.startswith('#'):
            story.append(Paragraph(line, body_style))

    # 生成PDF
    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f'❌ PDF生成失败: {e}')
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('使用方法: python3 generate_pdf_report.py <report_file> [output_file]')
        sys.exit(1)

    report_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # 自动生成输出文件名
        base_name = os.path.splitext(report_file)[0]
        output_file = f'{base_name}.pdf'

    if not os.path.exists(report_file):
        print(f'错误: 报告文件不存在: {report_file}')
        sys.exit(1)

    if create_pdf(report_file, output_file):
        print(f'✅ PDF报告已生成: {output_file}')
    else:
        print(f'❌ PDF报告生成失败')
        sys.exit(1)
