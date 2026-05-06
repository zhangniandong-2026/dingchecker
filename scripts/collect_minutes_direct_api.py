#!/usr/bin/env python3
"""
使用企业应用access_token直接调用钉钉API采集会议数据
绕过dws CLI的个人OAuth token限制
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests


# 应用凭证
CLIENT_ID = "dingnqr0t2bwcvzbcv0v"
CLIENT_SECRET = "d4_TJEWq-uRTfih7lJ1lPG8W3jBuGjPOy_3bht9Y7SGr7fgPUkLmFevFsXoui2fL"

# Token缓存
TOKEN_CACHE = Path.home() / ".dingchecker_app_token.json"

# AiTable配置
AITABLE_BASE_ID = "93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"
AITABLE_TABLE_ID = "tblP0FrsqYnUZcNQ"


def get_access_token() -> str:
    """获取企业应用access_token（带缓存）"""
    # 检查缓存
    if TOKEN_CACHE.exists():
        try:
            cache = json.loads(TOKEN_CACHE.read_text())
            if cache.get('expire_time', 0) > time.time() + 60:  # 提前1分钟刷新
                return cache['access_token']
        except Exception:
            pass

    # 获取新token
    print("🔑 获取企业应用access_token...", file=sys.stderr)
    url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"

    response = requests.post(url, json={
        "appKey": CLIENT_ID,
        "appSecret": CLIENT_SECRET
    }, timeout=30)

    if response.status_code != 200:
        raise Exception(f"获取token失败: {response.text}")

    data = response.json()
    access_token = data['accessToken']
    expires_in = data['expireIn']

    # 缓存token
    TOKEN_CACHE.write_text(json.dumps({
        'access_token': access_token,
        'expire_time': time.time() + expires_in
    }))

    print(f"✓ 获取access_token成功（有效期{expires_in}秒）", file=sys.stderr)
    return access_token


def query_aitable_records(access_token: str, date_str: str) -> List[Dict]:
    """查询AiTable中指定日期的听记记录"""
    print(f"📊 查询AiTable: {date_str}", file=sys.stderr)

    url = f"https://api.dingtalk.com/v1.0/aitable/bases/{AITABLE_BASE_ID}/tables/{AITABLE_TABLE_ID}/records"

    headers = {
        "x-acs-dingtalk-access-token": access_token,
        "Content-Type": "application/json"
    }

    # 查询条件：日期匹配
    params = {
        "maxResults": 100
    }

    all_records = []
    next_token = None

    while True:
        if next_token:
            params["nextToken"] = next_token

        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code != 200:
            print(f"⚠️  AiTable查询失败: {response.status_code}", file=sys.stderr)
            print(response.text, file=sys.stderr)
            break

        data = response.json()
        records = data.get('records', [])
        all_records.extend(records)

        next_token = data.get('nextToken')
        if not next_token:
            break

    # 过滤指定日期的记录
    target_records = []
    for record in all_records:
        fields = record.get('fields', {})
        record_date = fields.get('日期', '')
        if record_date == date_str:
            target_records.append(record)

    print(f"✓ 找到 {len(target_records)} 条听记记录", file=sys.stderr)
    return target_records


def get_transcription(access_token: str, task_uuid: str) -> Optional[List[Dict]]:
    """获取会议转写内容"""
    url = "https://api.dingtalk.com/v1.0/ysp/spaces/minutes/transcriptions/query"

    headers = {
        "x-acs-dingtalk-access-token": access_token,
        "Content-Type": "application/json"
    }

    all_paragraphs = []
    next_token = None

    while True:
        payload = {
            "unionId": "",  # 企业应用不需要指定用户
            "bizType": "dingding_meeting",
            "bizId": task_uuid
        }

        if next_token:
            payload["nextToken"] = next_token

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 403:
                # 权限错误
                return None

            if response.status_code != 200:
                print(f"⚠️  API调用失败: {response.status_code}", file=sys.stderr)
                return None

            data = response.json()

            # 检查业务错误
            if not data.get('success'):
                return None

            # 提取段落
            paragraphs = data.get('paragraphList', [])
            all_paragraphs.extend(paragraphs)

            # 检查是否有更多数据
            next_token = data.get('nextToken')
            if not next_token:
                break

        except Exception as e:
            print(f"⚠️  请求异常: {e}", file=sys.stderr)
            return None

    return all_paragraphs if all_paragraphs else None


def collect_minutes(date_str: str, units: Optional[List[str]] = None) -> Dict:
    """采集会议数据"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
    print(f"  采集日期: {date_str}", file=sys.stderr)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
    print(file=sys.stderr)

    # 获取access_token
    try:
        access_token = get_access_token()
    except Exception as e:
        print(f"❌ 获取token失败: {e}", file=sys.stderr)
        return {"error": str(e), "units": []}

    print(file=sys.stderr)

    # 查询AiTable获取听记记录
    try:
        records = query_aitable_records(access_token, date_str)
    except Exception as e:
        print(f"❌ AiTable查询失败: {e}", file=sys.stderr)
        return {"error": str(e), "units": []}

    if not records:
        print("⚠️  未找到听记记录", file=sys.stderr)
        return {"date": date_str, "units": []}

    print(file=sys.stderr)

    # 处理每个业务单元
    results = []
    success_count = 0
    permission_error_count = 0
    no_transcription_count = 0

    for i, record in enumerate(records, 1):
        fields = record.get('fields', {})
        unit_name = fields.get('业务单元', 'Unknown')
        task_uuid = fields.get('taskUuid', '')
        meeting_url = fields.get('听记链接', '')

        # 过滤指定单元
        if units and unit_name not in units:
            continue

        print(f"[{i}/{len(records)}] {unit_name}", file=sys.stderr)

        if not task_uuid:
            print("  ⚠️  无taskUuid", file=sys.stderr)
            results.append({
                "unit": unit_name,
                "status": "no_uuid",
                "meeting_url": meeting_url
            })
            continue

        # 获取转写
        print(f"  获取转写: {task_uuid[:20]}...", file=sys.stderr)
        paragraphs = get_transcription(access_token, task_uuid)

        if paragraphs is None:
            print("  ❌ 权限错误", file=sys.stderr)
            permission_error_count += 1
            results.append({
                "unit": unit_name,
                "task_uuid": task_uuid,
                "permission_error": True,
                "meeting_url": meeting_url
            })
        elif len(paragraphs) == 0:
            print("  🟡 无转写内容", file=sys.stderr)
            no_transcription_count += 1
            results.append({
                "unit": unit_name,
                "task_uuid": task_uuid,
                "status": "no_transcription",
                "meeting_url": meeting_url
            })
        else:
            print(f"  ✅ 获取 {len(paragraphs)} 段转写", file=sys.stderr)
            success_count += 1

            # 格式化转写内容
            transcription_text = "\n".join([
                f"[{p.get('nickName', 'Unknown')}] {p.get('content', '')}"
                for p in paragraphs
            ])

            results.append({
                "unit": unit_name,
                "task_uuid": task_uuid,
                "transcription": transcription_text,
                "paragraph_count": len(paragraphs),
                "meeting_url": meeting_url,
                "aitable_fields": fields
            })

        # 避免请求过快
        time.sleep(0.5)

    print(file=sys.stderr)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
    print(f"  采集完成", file=sys.stderr)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
    print(f"✅ 成功: {success_count}", file=sys.stderr)
    print(f"🟡 无转写: {no_transcription_count}", file=sys.stderr)
    print(f"❌ 权限错误: {permission_error_count}", file=sys.stderr)
    print(file=sys.stderr)

    return {
        "date": date_str,
        "collected_at": datetime.now().isoformat(),
        "method": "direct_api",
        "stats": {
            "total": len(results),
            "success": success_count,
            "no_transcription": no_transcription_count,
            "permission_error": permission_error_count
        },
        "units": results
    }


def main():
    parser = argparse.ArgumentParser(
        description='使用企业应用token直接调用钉钉API采集会议数据'
    )
    parser.add_argument('--date',
                       default=datetime.now().strftime('%Y-%m-%d'),
                       help='日期 (YYYY-MM-DD)')
    parser.add_argument('--units',
                       help='指定业务单元（逗号分隔），不指定则采集所有')
    parser.add_argument('--output',
                       help='输出JSON文件路径')

    args = parser.parse_args()

    # 解析单元列表
    units = None
    if args.units:
        units = [u.strip() for u in args.units.split(',')]

    # 采集数据
    result = collect_minutes(args.date, units)

    # 输出结果
    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output_json, encoding='utf-8')
        print(f"✓ 结果已保存: {args.output}", file=sys.stderr)
    else:
        print(output_json)

    # 返回状态码
    if result.get('stats', {}).get('permission_error', 0) > 0:
        return 1  # 有权限错误
    return 0


if __name__ == '__main__':
    sys.exit(main())
