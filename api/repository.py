"""Read A's existing SQLite database; never create or mutate it."""

import sqlite3
from contextlib import closing
from pathlib import Path

from metrics.growth import grade

TABLES = {"score": "score_record", "consume": "consume_record", "library": "library_record", "sport": "sport_record"}


class Repository:
    def __init__(self, path, as_of):
        self.path = Path(path).resolve()
        self.as_of = as_of

    def load(self, major=None, grade_filter=None, gender=None, keyword=None, student_id=None):
        clauses, args = [], []
        for column, value in (("major", major), ("gender", gender), ("student_id", student_id)):
            if value is not None:
                clauses.append(f"b.{column} = ?")
                args.append(value)
        if keyword:
            # instr treats SQL wildcard characters as literal search characters.
            clauses.append("(instr(b.name, ?) > 0 OR instr(b.student_id, ?) > 0)")
            args.extend([keyword, keyword])
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with closing(sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, timeout=5)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only = ON")
            conn.execute("BEGIN")
            students = [dict(r) for r in conn.execute("SELECT b.* FROM student_basic b" + where + " ORDER BY b.student_id", args)]
            if grade_filter is not None:
                students = [s for s in students if grade(s["enrollment_date"], self.as_of) == grade_filter]
            records = {s["student_id"]: {key: [] for key in TABLES} for s in students}
            if students:
                # Five queries per group request, rather than one query per student.
                for key, table in TABLES.items():
                    rows = conn.execute(f"SELECT r.* FROM {table} r JOIN student_basic b ON r.student_id = b.student_id" + where + " ORDER BY r.record_id", args)
                    for row in rows:
                        if row["student_id"] in records:
                            records[row["student_id"]][key].append(dict(row))
        return students, records

    def filters(self):
        with closing(sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True)) as conn:
            rows = conn.execute("SELECT major, gender, enrollment_date FROM student_basic").fetchall()
        grades = {grade(r[2], self.as_of) for r in rows}
        return {
            "majors": sorted({r[0] for r in rows if r[0]}),
            "grades": [g for g in ("未入学", "大一", "大二", "大三", "大四", "已毕业") if g in grades],
            "genders": sorted({r[1] for r in rows if r[1]}),
        }
