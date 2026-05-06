#!/usr/bin/env python3
"""钉钉早会报告自动推送系统"""
import argparse
import base64
import hashlib
import hmac
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import requests


# 钉钉配置
DINGTALK_WORKSPACE_ID = "lPDmr9BoD10l6Xxd"
DINGTALK_FOLDER_ID = "R1zknDm0WR3jbR0bS2GNjLvpVBQEx5rG"
GUIDELINE_DOC_URL = "https://alidocs.dingtalk.com/i/nodes/ydxXB52LJq7gx2ZxtMmwBYleWqjMp697"


def get_sign(secret):
    """生成钉钉机器人安全签名"""
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = f'{timestamp}\n{secret}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def send_markdown_to_dingtalk(webhook_url, secret, title, text):
    """发送Markdown消息到钉钉群"""
    url = webhook_url
    if secret:
        timestamp, sign = get_sign(secret)
        url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text
        }
    }

    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    return response.json()


def remove_frontmatter(content):
    """去除Markdown文件的frontmatter"""
    lines = content.split('\n')
    if lines[0].strip() != '---':
        return content

    # 找到第二个 '---'
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == '---':
            # 返回从下一行开始的内容
            return '\n'.join(lines[i+1:])

    return content


def create_dingtalk_doc(report_path, date):
    """创建钉钉文档"""
    print(f"📄 创建钉钉文档...")

    # 读取报告内容
    content = Path(report_path).read_text(encoding='utf-8')

    # 去除frontmatter
    doc_content = remove_frontmatter(content)

    # 使用dws创建文档
    cmd = [
        'dws', 'doc', 'create',
        '--name', f'早会分析报告 {date}',
        '--workspace', DINGTALK_WORKSPACE_ID,
        '--folder', DINGTALK_FOLDER_ID,
        '--markdown', doc_content,
        '--format', 'json'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response = json.loads(result.stdout)

        if response.get('success'):
            doc_url = response.get('docUrl')
            print(f"✅ 文档创建成功: {doc_url}")
            return doc_url
        else:
            print(f"❌ 文档创建失败: {response}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"❌ dws命令执行失败: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ 解析响应失败: {e}")
        return None


def generate_summary_with_links(summary_path, report_url):
    """在摘要末尾添加文档链接"""
    summary = Path(summary_path).read_text(encoding='utf-8')

    # 添加文档链接
    links = f"""📄 完整报告（含详细点评）
→ [点击查看今日报告]({report_url})

📋 评分标准（晨会规范）
→ [业务单元每日晨会规范与评分标准]({GUIDELINE_DOC_URL})
"""

    return summary + links


def main():
    parser = argparse.ArgumentParser(description='钉钉早会报告自动推送')
    parser.add_argument('--date', required=True, help='报告日期 (YYYY-MM-DD)')
    parser.add_argument('--report', help='完整报告路径（可选，默认从vault读取）')
    parser.add_argument('--summary', help='摘要文件路径（可选，将自动生成）')
    parser.add_argument('--webhook', help='钉钉webhook URL（可选，从配置读取）')
    parser.add_argument('--secret', help='钉钉加签密钥（可选，从配置读取）')
    parser.add_argument('--skip-doc', action='store_true', help='跳过创建钉钉文档（调试用）')
    parser.add_argument('--test', action='store_true', help='测试模式，发送简短测试消息')

    args = parser.parse_args()

    # 测试模式
    if args.test:
        print("📤 测试模式 - 发送测试消息...")
        webhook = args.webhook
        secret = args.secret

        if not webhook:
            # 从配置读取
            config_path = Path('/Users/zhangniandong/repos/dingchecker/config/dingtalk_webhook.json')
            if config_path.exists():
                config = json.loads(config_path.read_text())
                webhook = config.get('webhook_url')
                secret = config.get('secret')

        if not webhook:
            print("❌ 缺少webhook URL")
            return 1

        test_message = f"""# 🤖 钉钉机器人测试

**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ Webhook配置正确
✅ 消息推送成功

---
*此为测试消息，请忽略*
"""
        result = send_markdown_to_dingtalk(webhook, secret, "测试消息", test_message)

        if result.get('errcode') == 0:
            print("✅ 测试消息发送成功!")
            return 0
        else:
            print(f"❌ 测试失败: {result}")
            return 1

    # 正常流程
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  早会报告推送 - {args.date}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # 1. 确定报告路径
    if args.report:
        report_path = args.report
    else:
        report_path = f"/Users/zhangniandong/.claude/Obsidian Vault/ai-output/dingtalk-minutes/report_{args.date}.md"

    if not Path(report_path).exists():
        print(f"❌ 报告文件不存在: {report_path}")
        return 1

    print(f"📖 读取报告: {report_path}")

    # 2. 创建钉钉文档
    report_url = None
    if not args.skip_doc:
        report_url = create_dingtalk_doc(report_path, args.date)
        if not report_url:
            print("⚠️  文档创建失败，继续推送摘要（不含报告链接）")
    else:
        print("⏭️  跳过文档创建")

    # 3. 生成摘要
    print()
    print("📝 生成简版摘要...")

    if args.summary and Path(args.summary).exists():
        summary_text = Path(args.summary).read_text(encoding='utf-8')
    else:
        # 自动生成摘要
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from generate_summary import parse_report, generate_summary

        content = Path(report_path).read_text(encoding='utf-8')
        data = parse_report(content)
        summary_text = generate_summary(data)

    # 添加文档链接
    if report_url:
        tmp_summary = Path('/tmp/summary.md')
        tmp_summary.write_text(summary_text, encoding='utf-8')
        summary_with_links = generate_summary_with_links(tmp_summary, report_url)
    else:
        summary_with_links = summary_text + "\n📄 完整报告生成失败，请检查系统日志\n"

    # 4. 推送到钉钉群
    print()
    print("📤 推送到钉钉群...")

    # 读取webhook配置
    webhook = args.webhook
    secret = args.secret

    if not webhook:
        config_path = Path('/Users/zhangniandong/repos/dingchecker/config/dingtalk_webhook.json')
        if not config_path.exists():
            print(f"❌ 配置文件不存在: {config_path}")
            return 1

        config = json.loads(config_path.read_text())
        webhook = config.get('webhook_url')
        secret = config.get('secret')
        enabled = config.get('enabled', True)

        if not enabled:
            print("⚠️  推送功能已禁用（配置中enabled=false）")
            return 0

    if not webhook:
        print("❌ 缺少webhook URL")
        return 1

    # 发送
    result = send_markdown_to_dingtalk(
        webhook_url=webhook,
        secret=secret,
        title=f"早会报告 {args.date}",
        text=summary_with_links
    )

    # 检查结果
    if result.get('errcode') == 0:
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  ✅ 推送完成")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        print(f"   日期: {args.date}")
        print(f"   摘要长度: {len(summary_with_links)} 字符")
        if report_url:
            print(f"   钉钉文档: {report_url}")
        return 0
    else:
        print(f"❌ 推送失败: {result}")
        return 1


if __name__ == '__main__':
    exit(main())
