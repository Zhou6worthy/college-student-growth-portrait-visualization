"""Calculations documented in docs/metrics.md. Inputs are dictionary rows."""

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from math import isfinite
from statistics import mean

METRICS = (
    ("academic", "学业表现", 0.40, "各课程历史均分的等权平均"),
    ("reading", "阅读素养", 0.12, "累计借阅12次为满分参考"),
    ("sport", "运动健康", 0.12, "最近56天累计运动1200分钟为满分参考"),
    ("routine", "作息规律", 0.12, "早餐消费日覆盖率与非夜宵占比的加权分"),
    ("consumption", "消费理性", 0.12, "正餐、水果和日用品占消费金额的比例"),
    ("diversity", "生活丰富度", 0.12, "消费地点、品类与运动类型的多样性"),
)


def average(values):
    values = list(values)
    return round(mean(values), 2) if values else 0


def grade(enrollment_date, as_of):
    enrolled = date.fromisoformat(enrollment_date)
    if enrolled > as_of:
        return "未入学"
    academic_year = lambda d: d.year - (d.month < 9)
    year = academic_year(as_of) - academic_year(enrolled) + 1
    return ("大一", "大二", "大三", "大四")[year - 1] if year <= 4 else "已毕业"


def basic_info(student):
    return {
        "student_id": student["student_id"], "name": student["name"],
        "gender": student["gender"], "major": student["major"],
        "enroll_year": date.fromisoformat(student["enrollment_date"]).year,
        "enroll_date": student["enrollment_date"],
    }


def grouped_values(rows, key, value):
    groups = defaultdict(list)
    for row in rows:
        groups[row[key]].append(row[value])
    return [{"label": label, "value": average(values)} for label, values in sorted(groups.items())]


def counts(rows, field):
    counter = Counter(row[field] for row in rows)
    return [{"label": key, "value": value} for key, value in sorted(counter.items(), key=lambda p: (-p[1], p[0]))]


def calculate(student, records, as_of):
    """Return portrait, four chart details and alert reason for one student.

    records: score/consume/library/sport lists using A's field names.
    as_of: datetime.date, inclusive end of the observation window.
    """
    date_fields = {"score": "exam_date", "consume": "consume_time", "library": "borrow_date", "sport": "sport_time"}
    numeric_fields = {"score": (("score", 100),), "consume": (("amount", None),),
                      "library": (), "sport": (("duration_minutes", None), ("calories", None))}
    for key, field in date_fields.items():
        for row in records.get(key, []):
            datetime.fromisoformat(row[field])
            for name, upper in numeric_fields[key]:
                number = float(row[name])
                if not isfinite(number) or number < 0 or (upper is not None and number > upper):
                    raise ValueError(f"Invalid {key}.{name}")
            if key == "library" and row["return_date"] and date.fromisoformat(row["return_date"]) < date.fromisoformat(row[field]):
                raise ValueError("Return date precedes borrowing date")
    filtered = {
        key: [r for r in records.get(key, []) if date.fromisoformat(r[field][:10]) <= as_of]
        for key, field in date_fields.items()
    }
    score, consume, library, sport = (filtered[k] for k in date_fields)
    courses = sorted(grouped_values(score, "course_name", "score"), key=lambda p: (-p["value"], p["label"]))
    score_months = [dict(r, month=r["exam_date"][:7]) for r in score]
    scores_detail = {
        "trend": grouped_values(score_months, "month", "score"), "courses": courses,
        "best_course": courses[0]["label"] if courses else "",
        "weak_course": courses[-1]["label"] if courses else "",
    }

    daily = {r["consume_time"][:10] for r in consume}
    breakfast_days = {r["consume_time"][:10] for r in consume if r["meal_type"] == "早餐"}
    breakfast_rate = len(breakfast_days) / len(daily) if daily else 0
    night_rate = sum(r["meal_type"] == "夜宵" for r in consume) / len(consume) if consume else 0
    amounts = defaultdict(lambda: Decimal(0))
    category_counts = Counter()
    hours = Counter()
    for row in consume:
        amounts[row["item_category"]] += Decimal(str(row["amount"]))
        category_counts[row["item_category"]] += 1
        hours[int(row["consume_time"][11:13])] += 1
    total_amount = sum(amounts.values(), Decimal(0))
    span = (date.fromisoformat(max(daily)) - date.fromisoformat(min(daily))).days + 1 if daily else 1
    consume_detail = {
        "structure": [{"label": k, "value": category_counts[k], "amount": float(v)} for k, v in sorted(amounts.items())],
        "hourly": [{"label": str(i), "value": hours[i]} for i in range(24)],
        "summary": {
            "avg_daily": round(float(total_amount) / span, 2), "total_amount": float(total_amount),
            "record_count": len(consume), "breakfast_rate": round(breakfast_rate, 4), "night_rate": round(night_rate, 4),
        },
    }
    returned_days = [
        (date.fromisoformat(r["return_date"]) - date.fromisoformat(r["borrow_date"])).days
        for r in library if r["return_date"] and date.fromisoformat(r["return_date"]) <= as_of
    ]
    library_detail = {"top": counts(library, "book_name"), "total": len(library), "avg_days": average(returned_days)}

    start = as_of - timedelta(days=55)
    weeks = [0] * 8
    for row in sport:
        day = date.fromisoformat(row["sport_time"][:10])
        if day >= start:
            weeks[(day - start).days // 7] += row["duration_minutes"]
    sport_detail = {
        "types": counts(sport, "sport_type"), "total_minutes": sum(r["duration_minutes"] for r in sport),
        "total_calories": sum(r["calories"] for r in sport),
        "weekly": [{"label": f"第{i + 1}周", "value": v} for i, v in enumerate(weeks)],
    }
    living_amount = sum((amounts[k] for k in ("正餐", "水果", "日用品")), Decimal(0))
    values = {
        "academic": average(c["value"] for c in courses),
        "reading": len(library) / 12 * 100,
        "sport": sum(weeks) / 1200 * 100,
        "routine": 100 * (0.7 * breakfast_rate + 0.3 * (1 - night_rate)) if consume else 0,
        "consumption": float(living_amount / total_amount) * 100 if total_amount else 0,
        "diversity": 100 / 3 * (
            min(len({r["location"] for r in consume}) / 5, 1)
            + min(len(category_counts) / 5, 1) + min(len({r["sport_type"] for r in sport}) / 4, 1)
        ),
    }
    available = {
        "academic": bool(score), "reading": bool(library), "sport": bool(sport),
        "routine": bool(consume), "consumption": bool(consume), "diversity": bool(consume or sport),
    }
    dimensions = [
        {"key": key, "label": label, "value": round(max(0, min(100, values[key])), 2), "desc": desc}
        for key, label, _, desc in METRICS
    ]
    weight = sum(w for key, _, w, _ in METRICS if available[key])
    total = round(sum(m["value"] * spec[2] for m, spec in zip(dimensions, METRICS) if available[m["key"]]) / weight, 2) if weight else 0
    level = next((label for threshold, label in [(80, "优秀"), (70, "良好"), (60, "合格"), (0, "待提升")] if total >= threshold)) if weight else "暂无数据"
    tags = []
    for match, label in [
        (values["academic"] >= 80, "学业稳定"), (len(library) >= 12, "阅读爱好者"),
        (values["sport"] >= 80, "运动达人"), (breakfast_rate >= 0.6 and night_rate <= 0.1, "晨型作息"),
    ]:
        if match:
            tags.append(label)
    reasons = []
    if any(c["value"] < 60 for c in courses):
        reasons.append("学业预警")
    if weight and total < 60:
        reasons.append("综合分偏低")
    return {
        "portrait": {"basic": basic_info(student), "total_score": total, "level": level, "tags": tags,
                     "metrics": dimensions, "missing_metrics": [key for key in values if not available[key]],
                     "as_of": as_of.isoformat(), "metric_version": "v1"},
        "scores": scores_detail, "consume": consume_detail, "library": library_detail,
        "sport": sport_detail, "reason": " / ".join(reasons),
    }


def summarize_group(results):
    portraits = [r["portrait"] for r in results]
    return {
        "students": len(results),
        "avg_score": average(p["total_score"] for p in portraits if len(p["missing_metrics"]) < len(METRICS)),
        "avg_metrics": [
            {"label": label, "value": average(p["metrics"][i]["value"] for p in portraits if key not in p["missing_metrics"])}
            for i, (key, label, _, _) in enumerate(METRICS)
        ],
    }
