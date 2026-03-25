#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""报告结构化数据的构建与兼容解析。"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from typing import Any

DIMENSION_KEYS = ["战果汇报", "任务聚焦", "协同效率", "情报敏感", "点评效率"]

DIMENSION_ALIASES = {
    "战果汇报": ["战果汇报质量", "目标清晰度"],
    "任务聚焦": ["任务聚焦度", "复盘闭环率"],
    "协同效率": ["协同效率", "协作敏捷度"],
    "情报敏感": ["情报敏感度", "信息增量"],
    "点评效率": ["领导点评效率", "问题聚焦度"],
}

PRIORITY_LABELS = {
    "high": "高优先级",
    "medium": "中优先级",
    "low": "低优先级",
}


def format_duration_label(seconds: int) -> str:
    """格式化秒数，便于报告展示。"""
    minutes, remain = divmod(max(int(seconds or 0), 0), 60)
    return f"{minutes}分{remain:02d}秒"


def normalize_discipline_alerts(alerts: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """归一化会议纪律提醒。"""
    normalized: list[dict[str, Any]] = []
    for alert in alerts or []:
        duration_seconds = int(alert.get("duration_seconds", 0) or 0)
        normalized.append(
            {
                "speaker": str(alert.get("speaker", "") or "").strip(),
                "start_label": str(alert.get("start_label", "") or "").strip(),
                "end_label": str(alert.get("end_label", "") or "").strip(),
                "duration_seconds": duration_seconds,
                "duration_label": str(alert.get("duration_label", "") or format_duration_label(duration_seconds)),
                "excerpt": str(alert.get("excerpt", "") or "").strip(),
            }
        )
    return normalized


def parse_score_from_line(line: str) -> int:
    """从评分行中提取分数。"""
    match = re.search(r"[:：]\s*(\d+)\s*分", line)
    if match:
        return int(match.group(1))
    return 0


def build_default_dimension_entry(score: int = 0) -> dict[str, Any]:
    """创建维度详情默认结构。"""
    return {
        "score": score,
        "strengths": [],
        "improvements": [],
        "highlight": "",
    }


def normalize_unit(unit: dict[str, Any]) -> dict[str, Any]:
    """补齐业务单元缺失字段。"""
    normalized = {
        "name": unit.get("name", "").strip(),
        "scores": dict(unit.get("scores", {})),
        "dimensions": dict(unit.get("dimensions", {})),
        "total": int(unit.get("total", 0) or 0),
        "max_total": int(unit.get("max_total", 25) or 25),
        "percentage": int(unit.get("percentage", 0) or 0),
        "rank": unit.get("rank"),
        "priority_suggestions": {
            "high": list(unit.get("priority_suggestions", {}).get("high", [])),
            "medium": list(unit.get("priority_suggestions", {}).get("medium", [])),
            "low": list(unit.get("priority_suggestions", {}).get("low", [])),
        },
        "discipline_alerts": normalize_discipline_alerts(unit.get("discipline_alerts", [])),
    }

    for dimension in DIMENSION_KEYS:
        entry = normalized["dimensions"].get(dimension)
        if not isinstance(entry, dict):
            entry = build_default_dimension_entry()
        normalized["dimensions"][dimension] = {
            "score": int(entry.get("score", normalized["scores"].get(dimension, 0)) or 0),
            "strengths": list(entry.get("strengths", [])),
            "improvements": list(entry.get("improvements", [])),
            "highlight": str(entry.get("highlight", "") or ""),
        }
        normalized["scores"][dimension] = int(
            normalized["scores"].get(dimension, normalized["dimensions"][dimension]["score"]) or 0
        )

    if normalized["total"] <= 0:
        normalized["total"] = sum(normalized["scores"].values())
    if normalized["percentage"] <= 0 and normalized["max_total"] > 0:
        normalized["percentage"] = round(normalized["total"] / normalized["max_total"] * 100)

    return normalized


def collect_report_unit_names(report_data: dict[str, Any]) -> list[str]:
    """按出现顺序收集报告中的业务单元名称。"""
    names: list[str] = []
    seen: set[str] = set()

    for item in report_data.get("results", []):
        name = str(item.get("sheet", "") or "").strip()
        if name and name not in seen:
            names.append(name)
            seen.add(name)

    for unit in report_data.get("analysis", {}).get("units", []):
        name = str(unit.get("name", "") or "").strip()
        if name and name not in seen:
            names.append(name)
            seen.add(name)

    return names


def summarize_unit_names(unit_names: list[str], max_names: int = 4) -> str:
    """压缩业务单元名称列表，避免标题过长。"""
    if not unit_names:
        return ""
    if len(unit_names) <= max_names:
        return "、".join(unit_names)
    return f"{'、'.join(unit_names[:max_names])}等{len(unit_names)}个业务单元"


def build_report_title(report_data: dict[str, Any]) -> str:
    """根据业务范围生成报告标题。"""
    unit_names = collect_report_unit_names(report_data)
    scope_label = os.environ.get("DINGCHECK_REPORT_SCOPE_LABEL", "").strip()

    if len(unit_names) == 1:
        return f"{unit_names[0]} 早会质量评估报告"

    if scope_label and unit_names:
        return f"{scope_label}业务单元横向比较报告（{summarize_unit_names(unit_names)}）"

    if scope_label:
        return f"{scope_label}业务单元横向比较报告"

    if unit_names:
        return f"业务单元横向比较报告（{summarize_unit_names(unit_names)}）"

    return "早会质量评估报告"


def finalize_report_data(report_data: dict[str, Any]) -> dict[str, Any]:
    """补齐报告的衍生统计字段。"""
    metadata = report_data.setdefault("metadata", {})
    summary = report_data.setdefault("summary", {})
    analysis = report_data.setdefault("analysis", {})
    groups = report_data.setdefault("groups", [])
    results = report_data.setdefault("results", [])

    units = [normalize_unit(unit) for unit in analysis.get("units", []) if unit.get("name")]
    units.sort(key=lambda item: (item.get("total", 0), item.get("percentage", 0), item["name"]), reverse=True)
    for index, unit in enumerate(units, 1):
        unit["rank"] = index
    analysis["units"] = units

    if results and not groups:
        grouped_results: dict[str, list[dict[str, Any]]] = defaultdict(list)
        ordered_group_names: list[str] = []
        for item in results:
            group_name = item.get("group", "未分组")
            if group_name not in grouped_results:
                ordered_group_names.append(group_name)
            grouped_results[group_name].append(item)

        for group_name in ordered_group_names:
            group_results = grouped_results[group_name]
            groups.append(
                {
                    "name": group_name,
                    "total": len(group_results),
                    "success": sum(1 for item in group_results if item.get("status") == "成功"),
                    "no_link": sum(1 for item in group_results if item.get("status") == "无"),
                    "no_permission": sum(1 for item in group_results if item.get("status") == "无权限"),
                    "error": sum(
                        1 for item in group_results if item.get("status") in {"错误", "无法访问", "无表格"}
                    ),
                }
            )

    if results:
        summary.setdefault("total_units", len(results))
        summary.setdefault("success_count", sum(1 for item in results if item.get("status") == "成功"))
        summary.setdefault("no_link_count", sum(1 for item in results if item.get("status") == "无"))
        summary.setdefault("no_table_count", sum(1 for item in results if item.get("status") == "无表格"))
        summary.setdefault("no_permission_count", sum(1 for item in results if item.get("status") == "无权限"))
        summary.setdefault(
            "error_count",
            sum(1 for item in results if item.get("status") in {"错误", "无法访问"}),
        )
        summary.setdefault(
            "discipline_alert_count",
            sum(len(normalize_discipline_alerts(item.get("discipline_alerts", []))) for item in results),
        )
        summary.setdefault(
            "discipline_unit_count",
            sum(1 for item in results if normalize_discipline_alerts(item.get("discipline_alerts", []))),
        )
    else:
        summary.setdefault("discipline_alert_count", 0)
        summary.setdefault("discipline_unit_count", 0)

    summary["evaluated_unit_count"] = len(units)
    if units:
        summary["average_total"] = round(sum(unit["total"] for unit in units) / len(units), 1)
        summary["average_percentage"] = round(sum(unit["percentage"] for unit in units) / len(units), 1)
    else:
        summary["average_total"] = 0
        summary["average_percentage"] = 0

    dimension_best = {
        key: {"unit": "暂无数据", "score": 0}
        for key in DIMENSION_KEYS
    }
    dimension_averages = {key: 0 for key in DIMENSION_KEYS}

    if units:
        for key in DIMENSION_KEYS:
            scores = [unit["scores"].get(key, 0) for unit in units]
            dimension_averages[key] = round(sum(scores) / len(scores), 1)
            best_unit = max(units, key=lambda item: item["scores"].get(key, 0))
            best_score = best_unit["scores"].get(key, 0)
            if best_score > 0:
                dimension_best[key] = {"unit": best_unit["name"], "score": best_score}

    analysis["dimension_best"] = dimension_best
    analysis["dimension_averages"] = dimension_averages
    analysis["rankings"] = [
        {"name": unit["name"], "total": unit["total"], "percentage": unit["percentage"], "rank": unit["rank"]}
        for unit in units
    ]

    result_alerts = {
        str(item.get("sheet", "")).strip(): normalize_discipline_alerts(item.get("discipline_alerts", []))
        for item in results
    }
    for unit in units:
        unit["discipline_alerts"] = result_alerts.get(unit["name"], normalize_discipline_alerts(unit.get("discipline_alerts", [])))

    title = str(metadata.get("title", "") or "").strip()
    if not title or title == "早会质量评估报告":
        metadata["title"] = build_report_title(report_data)
    else:
        metadata["title"] = title
    metadata.setdefault("report_date", "")
    metadata.setdefault("generated_at", "")
    metadata.setdefault("run_id", "")
    report_data["version"] = report_data.get("version", 2)
    return report_data


def parse_unit_scores(content: str) -> list[dict[str, Any]]:
    """从 AI 文本报告中提取业务单元评分详情。"""
    units: list[dict[str, Any]] = []
    current_unit: dict[str, Any] | None = None
    current_dimension: str | None = None
    current_dimension_mode: str | None = None
    current_priority: str | None = None

    score_section = content
    section_match = re.search(
        r"第三部分：详细评分（对每个业务单元）(.*?)(?:第四部分：综合分析与团队建议|$)",
        content,
        re.DOTALL,
    )
    if section_match:
        score_section = section_match.group(1)

    def finalize_current_unit() -> None:
        nonlocal current_unit, current_dimension, current_dimension_mode, current_priority
        if not current_unit:
            return
        normalized = normalize_unit(current_unit)
        if normalized["name"] and (normalized["total"] > 0 or any(normalized["scores"].values())):
            units.append(normalized)
        current_unit = None
        current_dimension = None
        current_dimension_mode = None
        current_priority = None

    for raw_line in score_section.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if re.match(r"^(?:##\s*)?[一二三四五六七八九十]+、", line):
            finalize_current_unit()
            unit_name = re.sub(r"^(?:##\s*)?[一二三四五六七八九十]+、\s*", "", line).strip()
            current_unit = {
                "name": unit_name,
                "scores": {},
                "dimensions": {},
                "total": 0,
                "max_total": 25,
                "percentage": 0,
                "rank": None,
                "priority_suggestions": {"high": [], "medium": [], "low": []},
            }
            continue

        if not current_unit:
            continue

        if "综合得分" in line:
            match = re.search(r"(\d+)\s*/\s*(\d+)\s*\((\d+)%\)", line)
            if match:
                current_unit["total"] = int(match.group(1))
                current_unit["max_total"] = int(match.group(2))
                current_unit["percentage"] = int(match.group(3))
            rank_match = re.search(r"排名[:：]?\s*#?(\d+)", line)
            if rank_match:
                current_unit["rank"] = int(rank_match.group(1))
            continue

        matched_dimension = None
        for dimension, aliases in DIMENSION_ALIASES.items():
            if any(alias in line for alias in aliases):
                matched_dimension = dimension
                break
        if matched_dimension:
            score = parse_score_from_line(line)
            current_unit["scores"][matched_dimension] = score
            current_unit["dimensions"][matched_dimension] = build_default_dimension_entry(score)
            current_dimension = matched_dimension
            current_dimension_mode = None
            current_priority = None
            continue

        if current_dimension and line.startswith("✅ 优点"):
            current_dimension_mode = "strengths"
            continue
        if current_dimension and line.startswith("⚠️ 待改进"):
            current_dimension_mode = "improvements"
            continue
        if current_dimension and "✨ 亮点" in line:
            highlight = re.sub(r"^.*?✨\s*亮点[:：]\s*", "", line).strip()
            current_unit["dimensions"][current_dimension]["highlight"] = highlight
            continue
        if line.startswith("📋 改进建议"):
            current_dimension = None
            current_dimension_mode = None
            current_priority = None
            continue
        if re.match(r"^\d+\.\s*[🔴🟡🟢]?\s*高优先级", line):
            current_priority = "high"
            continue
        if re.match(r"^\d+\.\s*[🔴🟡🟢]?\s*中优先级", line):
            current_priority = "medium"
            continue
        if re.match(r"^\d+\.\s*[🔴🟡🟢]?\s*低优先级", line):
            current_priority = "low"
            continue

        bullet_match = re.match(r"^[-•]\s*(.+)$", line)
        if not bullet_match:
            continue
        bullet_text = bullet_match.group(1).strip()

        if current_dimension and current_dimension_mode:
            current_unit["dimensions"][current_dimension][current_dimension_mode].append(bullet_text)
        elif current_priority:
            current_unit["priority_suggestions"][current_priority].append(bullet_text)

    finalize_current_unit()
    return units


def build_report_data(
    target_date: str,
    generated_at: str,
    results: list[dict[str, Any]],
    analysis_text: str,
    run_id: str = "",
) -> dict[str, Any]:
    """基于抓取结果和 AI 分析构建结构化报告。"""
    grouped_results: dict[str, list[dict[str, Any]]] = defaultdict(list)
    ordered_group_names: list[str] = []
    normalized_results: list[dict[str, Any]] = []

    for item in results:
        normalized_item = {
            "sheet": item.get("sheet", ""),
            "group": item.get("group", "未分组"),
            "status": item.get("status", ""),
            "link": item.get("link"),
            "content_length": len(item.get("content") or "") if item.get("status") == "成功" else 0,
            "discipline_alerts": normalize_discipline_alerts(item.get("discipline_alerts", [])),
        }
        normalized_results.append(normalized_item)
        group_name = normalized_item["group"]
        if group_name not in grouped_results:
            ordered_group_names.append(group_name)
        grouped_results[group_name].append(normalized_item)

    report_data = {
        "metadata": {
            "title": "",
            "report_date": target_date,
            "generated_at": generated_at,
            "run_id": run_id,
        },
        "summary": {},
        "groups": [],
        "results": normalized_results,
        "analysis": {
            "units": parse_unit_scores(analysis_text),
            "raw_text": analysis_text.strip(),
        },
    }

    for group_name in ordered_group_names:
        group_results = grouped_results[group_name]
        report_data["groups"].append(
            {
                "name": group_name,
                "total": len(group_results),
                "success": sum(1 for item in group_results if item["status"] == "成功"),
                "no_link": sum(1 for item in group_results if item["status"] == "无"),
                "no_permission": sum(1 for item in group_results if item["status"] == "无权限"),
                "error": sum(
                    1 for item in group_results if item["status"] in {"错误", "无法访问", "无表格"}
                ),
            }
        )

    return finalize_report_data(report_data)


def build_report_data_from_text(content: str) -> dict[str, Any]:
    """从旧版 TXT 报告兼容解析结构化数据。"""
    report_date = ""
    generated_at = ""

    report_date_match = re.search(r"^日期:\s*(.+)$", content, re.MULTILINE)
    if report_date_match:
        report_date = report_date_match.group(1).strip()

    generated_at_match = re.search(r"^生成时间:\s*(.+)$", content, re.MULTILINE)
    if generated_at_match:
        generated_at = generated_at_match.group(1).strip()

    summary = {
        "total_units": _extract_int(content, r"总计:\s*(\d+)\s*个业务单元"),
        "success_count": _extract_int(content, r"成功提取:\s*(\d+)"),
        "no_link_count": _extract_int(content, r"无听记链接:\s*(\d+)"),
        "no_table_count": _extract_int(content, r"无表格数据:\s*(\d+)"),
        "no_permission_count": _extract_int(content, r"无权限:\s*(\d+)"),
        "error_count": _extract_int(content, r"错误/无法访问:\s*(\d+)"),
    }

    report_data = {
        "metadata": {
            "title": "",
            "report_date": report_date,
            "generated_at": generated_at,
            "run_id": "",
        },
        "summary": summary,
        "groups": [],
        "results": [],
        "analysis": {
            "units": parse_unit_scores(content),
            "raw_text": _extract_ai_analysis_text(content),
        },
    }
    return finalize_report_data(report_data)


def load_report_data(report_file: str) -> dict[str, Any]:
    """加载 JSON 或 TXT 报告并归一化。"""
    extension = os.path.splitext(report_file)[1].lower()
    if extension == ".json":
        with open(report_file, "r", encoding="utf-8") as handle:
            return finalize_report_data(json.load(handle))

    with open(report_file, "r", encoding="utf-8") as handle:
        return build_report_data_from_text(handle.read())


def render_text_report(report_data: dict[str, Any]) -> str:
    """将结构化报告回写为兼容 TXT。"""
    report_data = finalize_report_data(report_data)
    metadata = report_data["metadata"]
    summary = report_data["summary"]
    groups = report_data.get("groups", [])
    results = report_data.get("results", [])
    raw_text = (report_data.get("analysis", {}).get("raw_text") or "").strip()

    lines = [
        metadata.get("title", "早会质量评估报告"),
        "=" * 80,
        f"日期: {metadata.get('report_date', '')}",
        f"生成时间: {metadata.get('generated_at', '')}",
        "=" * 80,
        "",
        "总体统计:",
        f"  总计: {summary.get('total_units', 0)} 个业务单元",
        f"  ✓ 成功提取: {summary.get('success_count', 0)}",
        f"  - 无听记链接: {summary.get('no_link_count', 0)}",
        f"  - 无表格数据: {summary.get('no_table_count', 0)}",
        f"  ⚠ 无权限: {summary.get('no_permission_count', 0)}",
        f"  ✗ 错误/无法访问: {summary.get('error_count', 0)}",
        f"  ⏱ 超2分钟提醒: {summary.get('discipline_alert_count', 0)} 段",
        "",
        "=" * 80,
        "分组统计",
        "=" * 80,
        "",
    ]

    for group in groups:
        lines.append(f"【{group.get('name', '未分组')}】")
        lines.append(
            "  总计: {total} | 成功: {success} | 无链接: {no_link} | 无权限: {no_permission} | 错误: {error}".format(
                total=group.get("total", 0),
                success=group.get("success", 0),
                no_link=group.get("no_link", 0),
                no_permission=group.get("no_permission", 0),
                error=group.get("error", 0),
            )
        )
        lines.append("")

    lines.extend(
        [
            "",
            "=" * 80,
            "详细内容",
            "=" * 80,
            "",
        ]
    )

    grouped_results: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        grouped_results[item.get("group", "未分组")].append(item)

    for group in groups:
        group_name = group.get("name", "未分组")
        group_results = grouped_results.get(group_name, [])
        lines.extend(
            [
                "",
                "=" * 80,
                f"【{group_name}】",
                "=" * 80,
                "",
            ]
        )
        for item in group_results:
            lines.extend(
                [
                    "",
                    "-" * 80,
                    f"▸ {item.get('sheet', '')}",
                    "-" * 80,
                    f"状态: {item.get('status', '')}",
                ]
            )
            if item.get("link"):
                lines.append(f"链接: {item['link']}")
            alerts = normalize_discipline_alerts(item.get("discipline_alerts", []))
            if alerts:
                lines.append("会议纪律提醒:")
                for alert in alerts:
                    time_range = " - ".join(
                        part for part in [alert.get("start_label", ""), alert.get("end_label", "")] if part
                    )
                    if time_range:
                        time_range = f"（{time_range}）"
                    lines.append(
                        f"  ⚠ {alert.get('speaker', '未知发言人')} 连续发言 {alert.get('duration_label', '')}{time_range}"
                    )

    if raw_text:
        lines.extend(["", raw_text])

    return "\n".join(lines) + "\n"


def _extract_int(content: str, pattern: str) -> int:
    match = re.search(pattern, content)
    if match:
        return int(match.group(1))
    return 0


def _extract_ai_analysis_text(content: str) -> str:
    for pattern in [
        r"(第一部分[:：].*)",
        r"(第三部分[:：].*)",
        r"(^[^\n]+报告.*\n={80}.*)",
    ]:
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""
