import copy
import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import create_app
from metrics import calculate
from metrics.growth import grade

AS_OF = date(2026, 11, 12)
STUDENT = {"student_id": "20250001", "name": "测试甲", "gender": "女", "major": "软件工程", "enrollment_date": "2025-09-04"}


def sample_records():
    return {
        "score": [
            {"record_id": "S1", "student_id": STUDENT["student_id"], "name": STUDENT["name"], "course_name": "数学", "score": 80, "exam_date": "2026-06-20"},
            {"record_id": "S2", "student_id": STUDENT["student_id"], "name": STUDENT["name"], "course_name": "英语", "score": 60, "exam_date": "2026-06-20"},
        ],
        "consume": [
            {"record_id": "C1", "student_id": STUDENT["student_id"], "name": STUDENT["name"], "amount": 10.1, "consume_time": "2026-11-10 07:00:00", "location": "食堂", "item_category": "正餐", "meal_type": "早餐"},
            {"record_id": "C2", "student_id": STUDENT["student_id"], "name": STUDENT["name"], "amount": 9.9, "consume_time": "2026-11-12 22:00:00", "location": "超市", "item_category": "饮品", "meal_type": "夜宵"},
        ],
        "library": [{"record_id": "L1", "student_id": STUDENT["student_id"], "name": STUDENT["name"], "book_name": "Python", "borrow_date": "2026-11-01", "return_date": "2026-11-11"}],
        "sport": [{"record_id": "T1", "student_id": STUDENT["student_id"], "name": STUDENT["name"], "sport_type": "跑步", "duration_minutes": 120, "calories": 600, "sport_time": "2026-11-12 17:00:00"}],
    }


def fixture_db(path, empty=False):
    # Use A's DDL without importing pandas or running A's destructive init pipeline.
    source = (Path(__file__).resolve().parents[2] / "database" / "init_db.py").read_text(encoding="utf-8")
    import ast
    tree = ast.parse(source)
    ddls = [n.args[0].value for n in ast.walk(tree) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute) and n.func.attr == "execute" and n.args
            and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)
            and "CREATE TABLE" in n.args[0].value]
    if len(ddls) != 5:
        raise AssertionError("A's five table definitions changed; review fixture")
    with closing(sqlite3.connect(path)) as conn, conn:
        for ddl in ddls:
            conn.execute(ddl)
        if empty:
            return
        students = [STUDENT, dict(STUDENT, student_id="20250002", name="测试乙", gender="男", major="人工智能")]
        for s in students:
            conn.execute("INSERT INTO student_basic VALUES (?,?,?,?,?)", tuple(s.values()))
        for key, rows in sample_records().items():
            for r in rows:
                conn.execute(f"INSERT INTO {dict(score='score_record',consume='consume_record',library='library_record',sport='sport_record')[key]} ({','.join(r)}) VALUES ({','.join('?' for _ in r)})", tuple(r.values()))


class MetricTests(unittest.TestCase):
    def test_hand_calculated_six_dimensions(self):
        result = calculate(STUDENT, sample_records(), AS_OF)
        self.assertEqual([m["value"] for m in result["portrait"]["metrics"]], [70, 8.33, 10, 50, 50.5, 35])
        self.assertEqual(result["portrait"]["total_score"], 46.46)
        self.assertEqual(result["portrait"]["level"], "待提升")
        self.assertEqual(result["reason"], "综合分偏低")

    def test_empty_evidence_does_not_trigger_alert(self):
        result = calculate(STUDENT, {}, AS_OF)
        self.assertEqual(result["portrait"]["level"], "暂无数据")
        self.assertEqual(len(result["portrait"]["missing_metrics"]), 6)
        self.assertEqual(result["reason"], "")
        self.assertEqual(result["scores"]["courses"], [])
        self.assertEqual(result["scores"]["best_course"], "")
        self.assertEqual(len(result["consume"]["hourly"]), 24)
        self.assertEqual(len(result["sport"]["weekly"]), 8)

    def test_missing_dimensions_reweight(self):
        result = calculate(STUDENT, {"score": sample_records()["score"]}, AS_OF)
        self.assertEqual(result["portrait"]["total_score"], 70)
        self.assertEqual(result["portrait"]["level"], "良好")

    def test_course_equal_weight_and_month_aggregation(self):
        records = sample_records()
        records["score"].append(dict(records["score"][0], record_id="S3", score=100, exam_date="2026-07-20"))
        result = calculate(STUDENT, records, AS_OF)
        self.assertEqual(result["portrait"]["metrics"][0]["value"], 75)
        self.assertEqual(result["scores"]["trend"], [{"label": "2026-06", "value": 70}, {"label": "2026-07", "value": 100}])

    def test_future_records_are_excluded_and_input_is_unchanged(self):
        records = sample_records()
        fields = dict(score="exam_date", consume="consume_time", library="borrow_date", sport="sport_time")
        for key, field in fields.items():
            records[key].append(dict(records[key][0], **{field: "2027-01-01" + (" 12:00:00" if key in ("consume", "sport") else "")}))
        records["library"][-1]["return_date"] = "2027-01-11"
        before = copy.deepcopy(records)
        self.assertEqual(calculate(STUDENT, records, AS_OF), calculate(STUDENT, sample_records(), AS_OF))
        self.assertEqual(records, before)

    def test_sport_56_day_boundaries(self):
        records = sample_records()
        records["sport"] = [dict(records["sport"][0], sport_time=d + " 17:00:00") for d in ("2026-09-17", "2026-09-18", "2026-11-12", "2026-11-13")]
        result = calculate(STUDENT, records, AS_OF)["sport"]
        self.assertEqual([r["value"] for r in result["weekly"]], [120, 0, 0, 0, 0, 0, 0, 120])
        self.assertEqual(result["total_minutes"], 360)

    def test_old_sport_is_observed_zero(self):
        records = {"sport": [dict(sample_records()["sport"][0], sport_time="2025-01-01 17:00:00")]}
        result = calculate(STUDENT, records, AS_OF)["portrait"]
        self.assertNotIn("sport", result["missing_metrics"])
        self.assertEqual(result["metrics"][2]["value"], 0)

    def test_consumption_daily_span_and_rates(self):
        result = calculate(STUDENT, sample_records(), AS_OF)["consume"]
        self.assertEqual(result["summary"], {"avg_daily": 6.67, "total_amount": 20, "record_count": 2, "breakfast_rate": 0.5, "night_rate": 0.5})
        self.assertEqual(sum(r["value"] for r in result["hourly"]), 2)

    def test_zero_amount_is_finite(self):
        records = sample_records()
        for row in records["consume"]:
            row["amount"] = 0
        self.assertEqual(calculate(STUDENT, records, AS_OF)["portrait"]["metrics"][4]["value"], 0)

    def test_unreturned_library_excluded_from_average(self):
        records = sample_records()
        records["library"].append(dict(records["library"][0], record_id="L2", return_date="2027-01-01"))
        detail = calculate(STUDENT, records, AS_OF)["library"]
        self.assertEqual(detail["total"], 2)
        self.assertEqual(detail["avg_days"], 10)

    def test_invalid_source_values_fail(self):
        for amount in (-1, float("nan"), float("inf")):
            records = sample_records()
            records["consume"][0]["amount"] = amount
            with self.assertRaises(ValueError):
                calculate(STUDENT, records, AS_OF)

    def test_grade_boundaries(self):
        self.assertEqual(grade("2025-09-04", date(2026, 8, 31)), "大一")
        self.assertEqual(grade("2025-09-04", date(2026, 9, 1)), "大二")
        self.assertEqual(grade("2025-02-27", AS_OF), "大三")
        self.assertEqual(grade("2022-09-04", AS_OF), "已毕业")
        self.assertEqual(grade("2027-09-04", AS_OF), "未入学")

    def test_level_thresholds(self):
        for score, level in ((100, "优秀"), (80, "优秀"), (79, "良好"), (70, "良好"), (69, "合格"), (60, "合格"), (59, "待提升")):
            records = {"score": [dict(sample_records()["score"][0], score=score)]}
            with self.subTest(score=score):
                self.assertEqual(calculate(STUDENT, records, AS_OF)["portrait"]["level"], level)

    def test_caps_and_two_alert_reasons(self):
        records = sample_records()
        records["library"] *= 20
        records["sport"][0]["duration_minutes"] = 2000
        result = calculate(STUDENT, records, AS_OF)
        self.assertEqual(result["portrait"]["metrics"][1]["value"], 100)
        self.assertEqual(result["portrait"]["metrics"][2]["value"], 100)
        self.assertTrue(all(0 <= m["value"] <= 100 for m in result["portrait"]["metrics"]))
        records = {"score": [dict(sample_records()["score"][0], score=40)]}
        self.assertEqual(calculate(STUDENT, records, AS_OF)["reason"], "学业预警 / 综合分偏低")


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "fixture.db"
        fixture_db(self.db)
        self.client = TestClient(create_app(self.db, AS_OF), raise_server_exceptions=False)
        self.addCleanup(self.client.close)

    def get(self, path, status=200):
        result = self.client.get(path)
        self.assertEqual(result.status_code, status, result.text)
        body = result.json()
        self.assertEqual(set(body), {"code", "message", "data"})
        self.assertEqual(body["code"], 0 if status == 200 else status)
        return body["data"]

    def test_all_ten_endpoints(self):
        paths = ["/api/meta/filters", "/api/students", "/api/analytics/overview", "/api/analytics/majors", "/api/analytics/alerts"]
        paths += [f"/api/students/20250001/{suffix}" for suffix in ("portrait", "scores", "consume", "library", "sport")]
        for path in paths:
            with self.subTest(path=path):
                self.get(path)

    def test_response_shapes_and_student_id(self):
        row = self.get("/api/students")["list"][0]
        self.assertEqual(row["student_id"], "20250001")
        self.assertEqual(row["academic"], 70)
        portrait = self.get("/api/students/20250001/portrait")
        self.assertEqual(portrait["basic"]["enroll_date"], "2025-09-04")
        self.assertEqual([m["key"] for m in portrait["metrics"]], ["academic", "reading", "sport", "routine", "consumption", "diversity"])
        self.assertEqual(portrait["as_of"], "2026-11-12")

    def test_pagination_and_all_filters(self):
        first = self.get("/api/students?page_size=1")
        second = self.get("/api/students?page=2&page_size=1")
        self.assertEqual(first["total"], 2)
        self.assertNotEqual(first["list"][0]["student_id"], second["list"][0]["student_id"])
        self.assertEqual(self.get("/api/students?page=99")["list"], [])
        query = "?major=软件工程&grade=大二&gender=女&keyword=测试"
        self.assertEqual(self.get("/api/students" + query)["total"], 1)
        self.assertEqual(self.get("/api/analytics/overview" + query)["students"], 1)
        self.assertEqual(len(self.get("/api/analytics/majors" + query)), 1)
        self.assertEqual(len(self.get("/api/analytics/alerts" + query)), 1)

    def test_literal_search_and_injection(self):
        for keyword in ("%", "_", "' OR 1=1 --"):
            result = self.client.get("/api/students", params={"keyword": keyword})
            self.assertEqual(result.json()["data"]["total"], 0)
        self.assertEqual(self.client.get("/api/students", params={"major": "' OR 1=1 --"}).json()["data"]["total"], 0)

    def test_filters_from_actual_values(self):
        self.assertEqual(self.get("/api/meta/filters"), {"majors": ["人工智能", "软件工程"], "grades": ["大二"], "genders": ["女", "男"]})

    def test_group_averages_exclude_missing_and_alert_count_matches(self):
        result = self.get("/api/analytics/overview")
        self.assertEqual(result["students"], 2)
        self.assertEqual(result["avg_score"], 46.46)
        self.assertEqual(result["top_major"], "软件工程")
        self.assertEqual(result["alert_count"], len(self.get("/api/analytics/alerts")))
        self.assertEqual(result["avg_metrics"][0]["value"], 70)

    def test_unknown_filter_empty_overview(self):
        result = self.get("/api/analytics/overview?major=不存在")
        self.assertEqual(result["students"], 0)
        self.assertEqual(result["top_major"], "")
        self.assertEqual(result["avg_score"], 0)

    def test_404_and_422_envelopes(self):
        self.get("/api/students/absent/portrait", 404)
        self.get("/api/no-such-route", 404)
        for query in ("page=0", "page=-1", "page_size=101", "page_size=0", "page=hello"):
            self.get("/api/students?" + query, 422)

    def test_read_only_database_unchanged(self):
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        self.get("/api/students")
        self.get("/api/analytics/overview")
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(), before)

    def test_missing_db_returns_503_without_creating_file(self):
        missing = Path(self.temp.name) / "missing.db"
        with TestClient(create_app(missing, AS_OF), raise_server_exceptions=False) as client, self.assertLogs("api.main", level="ERROR"):
            r = client.get("/api/students")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.json()["data"], None)
        self.assertFalse(missing.exists())

    def test_missing_table_returns_503(self):
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute("DROP TABLE score_record")
        with self.assertLogs("api.main", level="ERROR"):
            self.get("/api/students", 503)

    def test_invalid_source_returns_503(self):
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute("UPDATE consume_record SET amount = -1")
        with self.assertLogs("api.main", level="ERROR"):
            self.get("/api/students", 503)

    def test_empty_database(self):
        empty = Path(self.temp.name) / "empty.db"
        fixture_db(empty, empty=True)
        with TestClient(create_app(empty, AS_OF)) as client:
            self.assertEqual(client.get("/api/students").json()["data"]["total"], 0)
            self.assertEqual(client.get("/api/analytics/alerts").json()["data"], [])

    def test_cors_and_openapi(self):
        result = self.client.get("/api/meta/filters", headers={"Origin": "http://127.0.0.1:5173"})
        self.assertEqual(result.headers["access-control-allow-origin"], "http://127.0.0.1:5173")
        result = self.client.get("/api/meta/filters", headers={"Origin": "https://example.com"})
        self.assertNotIn("access-control-allow-origin", result.headers)
        self.assertEqual(len(self.client.get("/openapi.json").json()["paths"]), 10)


if __name__ == "__main__":
    unittest.main()
