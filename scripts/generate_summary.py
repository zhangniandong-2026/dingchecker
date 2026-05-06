#!/usr/bin/env python3
"""从完整报告生成简版摘要"""
import argparse
import json
import re
from pathlib import Path


def parse_report(report_content):
    """解析报告内容，提取关键信息"""
    lines = report_content.split('\n')

    # 跳过frontmatter
    start_idx = 0
    if lines[0].strip() == '---':
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                start_idx = i + 1
                break

    content = '\n'.join(lines[start_idx:])

    # 提取日期（从标题）
    title_match = re.search(r'# (\d{4}-\d{2}-\d{2})', content)
    date = title_match.group(1) if title_match else ''

    # 从数据概览表格提取统计数字
    total_units = 0
    valid_data = 0
    no_meeting = 0
    permission_error = 0
    no_transcript = 0

    overview_section = re.search(r'## 一、数据概览.*?\n\n(.*?)(?=\n\*\*|$)', content, re.DOTALL)
    if overview_section:
        table_text = overview_section.group(1)
        # 提取总业务单元
        total_match = re.search(r'\|\s*总业务单元\s*\|\s*(\d+)', table_text)
        if total_match:
            total_units = int(total_match.group(1))
        # 提取有完整转写
        valid_match = re.search(r'\|\s*(?:\*\*)?有完整转写(?:\*\*)?\s*\|\s*(?:\*\*)?(\d+)(?:\*\*)?\s*\|', table_text)
        if valid_match:
            valid_data = int(valid_match.group(1))
        # 提取未找到听记
        no_meeting_match = re.search(r'\|\s*未找到听记\s*\|\s*(\d+)', table_text)
        if no_meeting_match:
            no_meeting = int(no_meeting_match.group(1))
        # 提取权限错误
        permission_match = re.search(r'\|\s*权限错误\s*\|\s*(\d+)', table_text)
        if permission_match:
            permission_error = int(permission_match.group(1))
        # 提取有听记无转写
        no_transcript_match = re.search(r'\|\s*有听记无转写\s*\|\s*(\d+)', table_text)
        if no_transcript_match:
            no_transcript = int(no_transcript_match.group(1))

    has_meeting = total_units - no_meeting
    exception_count = no_meeting + permission_error

    # 提取预警信息
    warnings = []

    # 权限错误单元
    permission_section = re.search(r'### 🟣 权限错误.*?\n\n(.*?)(?=\n###|$)', content, re.DOTALL)
    if permission_section:
        units_text = permission_section.group(1)
        units = re.findall(r'[-•]\s*(.+?)(?:\n|$)', units_text)
        warnings.extend([f"{u.strip()}：权限错误" for u in units if u.strip()])

    # 未找到听记单元
    no_meeting_section = re.search(r'### 🔴 未找到听记.*?\n\n(.*?)(?=\n\*\*可能原因|###|$)', content, re.DOTALL)
    if no_meeting_section:
        units_text = no_meeting_section.group(1)
        # 提取战区信息
        battle_zones = re.findall(r'\*\*(.+?战区|.+?战队)\*\*[（(](\d+)个[)）]', units_text)
        for zone, count in battle_zones[:2]:
            warnings.append(f"{zone}：{count}个单元未找到听记")

    # 提取所有单元评分（从详细评分章节）
    rankings = []
    detail_section = re.search(r'## 四、详细评分(.*?)(?=\n## |$)', content, re.DOTALL)
    if detail_section:
        detail_text = detail_section.group(1)
        # 匹配格式：#### 单元名 - 分数分
        unit_scores = re.findall(r'####\s+(.+?)\s*-\s*(\d+)分', detail_text)
        for rank, (name, score) in enumerate(unit_scores, 1):
            rankings.append({
                'rank': rank,
                'name': name.strip(),
                'score': int(score)
            })

    # 按分数排序（从高到低）
    rankings.sort(key=lambda x: (-x['score'], x['name']))
    # 重新分配排名
    for rank, item in enumerate(rankings, 1):
        item['rank'] = rank

    return {
        'date': date,
        'total_units': total_units,
        'has_meeting': has_meeting,
        'valid_data': valid_data,
        'exception_count': exception_count,
        'transcription_failed': no_transcript,
        'warnings': warnings[:3],  # 最多3条预警
        'rankings': rankings
    }


def generate_summary(data):
    """生成简版摘要"""

    # 顶部统计
    coverage = int(data['valid_data'] / data['total_units'] * 100) if data['total_units'] > 0 else 0
    summary = f"""📊 早会报告 {data['date']} | {data['total_units']}单元

✅ 有完整转写: {data['valid_data']}个（{coverage}%）
❌ 未找到听记: {data['total_units'] - data['has_meeting']}个
🟣 权限错误: {data['exception_count'] - (data['total_units'] - data['has_meeting'])}个

---

"""

    # 预警信息
    if data['warnings']:
        summary += "🔴 预警\n"
        for warning in data['warnings']:
            summary += f"• {warning}\n"
        summary += "\n---\n\n"

    # 完整排名
    summary += "📊 完整排名\n\n"

    rankings = data['rankings']
    if not rankings:
        summary += "**暂无有效数据**\n\n"
    else:
        # 按评级分组
        excellent = [r for r in rankings if r['score'] >= 18]
        good = [r for r in rankings if 15 <= r['score'] < 18]
        pass_level = [r for r in rankings if 12 <= r['score'] < 15]
        fail = [r for r in rankings if r['score'] < 12]

        if excellent:
            summary += "**🌟 优秀（18-20分）**\n"
            for r in excellent:
                medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(r['rank'], '')
                summary += f"{medal} #{r['rank']} {r['name']} {r['score']}/20\n"
            summary += "\n"

        if good:
            summary += "**✅ 良好（15-17分）**\n"
            for r in good:
                summary += f"#{r['rank']} {r['name']} {r['score']}/20\n"
            summary += "\n"

        if pass_level:
            summary += "**➡️ 及格（12-14分）**\n"
            for r in pass_level:
                summary += f"#{r['rank']} {r['name']} {r['score']}/20\n"
            summary += "\n"

        if fail:
            summary += "**⚠️ 不合格（12分以下）**\n"
            for r in fail:
                summary += f"#{r['rank']} {r['name']} {r['score']}/20\n"
            summary += "\n"

    summary += "---\n\n"

    # 激励机制
    summary += """🎁 激励机制
🍽️ 前三累计10次 → 朱文雷请客
☕ 后五累计10次 → 张建栋请茶

---

"""

    return summary


def main():
    parser = argparse.ArgumentParser(description='生成简版摘要')
    parser.add_argument('--report', required=True, help='完整报告文件路径')
    parser.add_argument('--output', help='输出文件路径（可选）')

    args = parser.parse_args()

    # 读取报告
    report_path = Path(args.report)
    if not report_path.exists():
        print(f"❌ 报告文件不存在: {args.report}")
        return 1

    content = report_path.read_text(encoding='utf-8')

    # 解析并生成摘要
    data = parse_report(content)
    summary = generate_summary(data)

    # 输出
    if args.output:
        Path(args.output).write_text(summary, encoding='utf-8')
        print(f"✅ 摘要已保存: {args.output}")
    else:
        print(summary)

    return 0


if __name__ == '__main__':
    exit(main())
