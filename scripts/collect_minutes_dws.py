#!/usr/bin/env python3
"""通过 dws CLI 收集钉钉听记数据并分析"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# 钉钉 2026早会AI听记 Base
BASE_ID = "93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"

# 认证错误关键词
AUTH_ERROR_KEYWORDS = ("unauthorized", "authentication", "auth", "login", "token", "401")


class DWSAuthError(Exception):
    """dws 认证失败，需要重新登录"""


def dws(*args, timeout=60):
    """统一 dws 调用，返回解析后的数据。认证错误抛 DWSAuthError"""
    cmd = ["dws", *args, "-f", "json", "--yes"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            err = r.stderr.lower()
            if any(k in err for k in AUTH_ERROR_KEYWORDS):
                raise DWSAuthError(r.stderr.strip())
            # 识别权限错误
            if "no permission" in r.stderr:
                return {"_permission_error": True}
            print(f"⚠️  dws {' '.join(args)} 失败: {r.stderr.strip()}", file=sys.stderr)
            return None
        data = json.loads(r.stdout)
        return data.get("result") or data.get("data") or data
    except DWSAuthError:
        raise
    except Exception as e:
        print(f"⚠️  dws {' '.join(args)} 异常: {e}", file=sys.stderr)
        return None


def extract_task_uuid(url):
    """从听记链接提取 taskUuid"""
    match = re.search(r'/transcribes/([a-f0-9_]+)', url)
    return match.group(1) if match else None


def get_full_transcription(task_uuid):
    """循环获取完整逐字稿（处理分页）"""
    all_paragraphs = []
    next_token = None

    while True:
        args = ["minutes", "get", "transcription", "--id", task_uuid]
        if next_token:
            args.extend(["--next-token", next_token])

        result = dws(*args)
        if not result:
            break

        paragraphs = result.get("paragraphList", [])
        all_paragraphs.extend(paragraphs)

        if not result.get("hasNext"):
            break
        next_token = result.get("nextToken")
        if not next_token:
            break

    return all_paragraphs


def calculate_speaker_stats(paragraphs):
    """计算每个发言人的发言时长和段落数"""
    speaker_stats = {}

    for p in paragraphs:
        speaker = p.get("nickName", "未知")
        start_ms = p.get("startTime", 0)
        end_ms = p.get("endTime", 0)
        duration_ms = end_ms - start_ms

        if speaker not in speaker_stats:
            speaker_stats[speaker] = {
                "paragraph_count": 0,
                "total_duration_ms": 0,
                "total_duration_min": 0
            }

        speaker_stats[speaker]["paragraph_count"] += 1
        speaker_stats[speaker]["total_duration_ms"] += duration_ms

    # 计算分钟
    for speaker in speaker_stats:
        ms = speaker_stats[speaker]["total_duration_ms"]
        speaker_stats[speaker]["total_duration_min"] = ms / 60000

    return speaker_stats


def get_aitable_records(base_id, table_id, date_str):
    """获取指定日期的 AiTable 记录"""
    records_result = dws("aitable", "record", "query",
                        "--base-id", base_id,
                        "--table-id", table_id,
                        "--limit", "100")
    if not records_result:
        return []

    records = records_result.get("records", [])
    filtered = []

    for record in records:
        cells = record.get("cells", {})
        record_date = None
        link_url = None
        creator_user_id = None

        for field_id, value in cells.items():
            # 日期字段 (ISO格式字符串)
            if isinstance(value, str) and date_str in value:
                record_date = value
            # 链接字段
            elif isinstance(value, dict) and "link" in value:
                link_url = value.get("link")
            # 创建者字段
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                creator_user_id = value[0].get("userId")

        if record_date and link_url and "shanji.dingtalk.com" in link_url:
            filtered.append({
                "date": record_date,
                "link": link_url,
                "creator_user_id": creator_user_id,
                "record_id": record.get("recordId")
            })

    return filtered


def analyze_one_meeting(task_uuid, unit_name, quiet=False):
    """分析单条听记，返回字典或 'permission_error' 字符串"""
    if not quiet:
        print(f"   🆔 taskUuid: {task_uuid}")

    # 获取基本信息
    info = dws("minutes", "get", "info", "--id", task_uuid)
    if info and info.get("_permission_error"):
        return "permission_error"
    if not info:
        return None

    title = info.get("title", "未命名")
    duration_ms = info.get("duration", 0)
    duration_min = duration_ms / 60000

    if not quiet:
        print(f"   📋 {title} ({duration_min:.1f}分钟)")

    # 获取完整转写
    paragraphs = get_full_transcription(task_uuid)
    if not paragraphs:
        if not quiet:
            print("   ⚠️  未获取到转写内容")
        # 返回空转写但有基本信息
        return {
            "task_uuid": task_uuid,
            "title": title,
            "unit_name": unit_name,
            "duration_min": duration_min,
            "paragraph_count": 0,
            "speaker_count": 0,
            "speaker_stats": {},
            "long_speakers": [],
            "paragraphs": []
        }

    # 计算发言人统计
    speaker_stats = calculate_speaker_stats(paragraphs)

    # 检测长时间发言
    long_speakers = [
        (speaker, stats["total_duration_min"])
        for speaker, stats in speaker_stats.items()
        if stats["total_duration_min"] > 2
    ]

    if not quiet and long_speakers:
        print(f"   ⚠️  发言超2分钟: {', '.join(f'{s}({d:.1f}分钟)' for s, d in long_speakers)}")

    return {
        "task_uuid": task_uuid,
        "title": title,
        "unit_name": unit_name,
        "duration_min": duration_min,
        "paragraph_count": len(paragraphs),
        "speaker_count": len(speaker_stats),
        "speaker_stats": speaker_stats,
        "long_speakers": [{"speaker": s, "duration_min": d} for s, d in long_speakers],
        "paragraphs": [
            {
                "speaker": p.get("nickName"),
                "text": p.get("paragraph"),
                "start_time_ms": p.get("startTime"),
                "end_time_ms": p.get("endTime"),
            }
            for p in paragraphs
        ]
    }


def collect_unit(unit_name, table_id, date_str, quiet=False):
    """收集单个业务单元的听记"""
    if not quiet:
        print(f"\n{'='*60}")
        print(f"🎯 {unit_name} ({date_str})")
        print(f"{'='*60}")

    records = get_aitable_records(BASE_ID, table_id, date_str)

    if not records:
        if not quiet:
            print(f"⚠️  未找到听记记录")
        return None

    if not quiet:
        print(f"✓ 找到 {len(records)} 条听记")

    meetings = []
    permission_errors = 0

    for idx, record in enumerate(records, 1):
        if not quiet:
            print(f"\n--- 记录 {idx}/{len(records)} ---")
            print(f"📅 {record['date']}")
            print(f"🔗 {record['link']}")

        task_uuid = extract_task_uuid(record['link'])
        if not task_uuid:
            if not quiet:
                print("❌ 无法提取 taskUuid")
            continue

        result = analyze_one_meeting(task_uuid, unit_name, quiet)
        if result == "permission_error":
            permission_errors += 1
        elif result:
            meetings.append(result)

    # 如果所有听记都是权限错误，标记为 permission_error
    if permission_errors > 0 and len(meetings) == 0:
        return {
            "unit_name": unit_name,
            "table_id": table_id,
            "date": date_str,
            "permission_error": True,
            "meeting_count": 0,
            "meetings": []
        }

    return {
        "unit_name": unit_name,
        "table_id": table_id,
        "date": date_str,
        "meeting_count": len(meetings),
        "meetings": meetings
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="日期 YYYY-MM-DD")
    p.add_argument("--units", required=True, help="业务单元名称，逗号分隔")
    p.add_argument("--mapping", required=True, help="业务单元->tableId 映射文件")
    p.add_argument("--output", required=True, help="输出 JSON 路径")
    p.add_argument("--quiet", action="store_true", help="静默模式")
    args = p.parse_args()

    # 加载映射
    mapping_file = Path(args.mapping)
    if not mapping_file.exists():
        print(f"❌ 映射文件不存在: {args.mapping}", file=sys.stderr)
        sys.exit(1)

    unit_mapping = json.loads(mapping_file.read_text())

    # 解析业务单元列表
    units = [u.strip() for u in args.units.split(",") if u.strip()]

    try:
        all_results = []
        for unit_name in units:
            if unit_name not in unit_mapping:
                print(f"⚠️  跳过未知业务单元: {unit_name}", file=sys.stderr)
                continue

            table_id = unit_mapping[unit_name]
            result = collect_unit(unit_name, table_id, args.date, args.quiet)
            if result:
                all_results.append(result)

        output_data = {
            "date": args.date,
            "units": units,
            "unit_count": len(all_results),
            "results": all_results,
            "collected_at": datetime.now().isoformat()
        }

    except DWSAuthError as e:
        print(f"❌ dws 认证失败: {e}", file=sys.stderr)
        sys.exit(2)  # 退出码 2 触发 skill 重新认证后重试

    # 保存结果
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.quiet:
        print(f"\n{'='*60}")
        print(f"✅ 分析完成")
        print(f"📊 业务单元数: {len(all_results)}")
        print(f"📊 总会议数: {sum(r['meeting_count'] for r in all_results)}")
        print(f"💾 输出文件: {out}")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
