"""Run from the repository root: python -m uvicorn api.main:app."""

import logging
import os
import sqlite3
from collections import defaultdict
from datetime import date
from decimal import InvalidOperation
from pathlib import Path

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from metrics import calculate, summarize_group
from .repository import Repository

logger = logging.getLogger(__name__)


def response(data=None, code=0, message="ok", status=200):
    return JSONResponse({"code": code, "message": message, "data": data}, status_code=status)


def filters(
    major: str | None = Query(None, max_length=100),
    grade: str | None = Query(None, max_length=10),
    gender: str | None = Query(None, max_length=10),
    keyword: str | None = Query(None, max_length=100),
):
    return dict(major=major, grade_filter=grade, gender=gender, keyword=keyword)


def create_app(db_path=None, as_of=None):
    """App factory permits isolated fixture databases without global mutations."""
    app = FastAPI(title="大学生成长画像 API", version="0.2.0")
    path = db_path or os.getenv("GROWTH_DB_PATH") or Path(__file__).resolve().parents[1] / "college_growth.db"
    fixed_day = as_of or os.getenv("GROWTH_AS_OF")
    if isinstance(fixed_day, str):
        fixed_day = date.fromisoformat(fixed_day)
    origins = os.getenv("GROWTH_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
    app.add_middleware(CORSMiddleware, allow_origins=[s.strip() for s in origins if s.strip()], allow_methods=["GET"], allow_headers=["*"])

    def repository():
        return Repository(path, fixed_day or date.today())

    @app.middleware("http")
    async def protect_errors(request: Request, call_next):
        try:
            return await call_next(request)
        except (sqlite3.Error, ValueError, TypeError, KeyError, InvalidOperation):
            logger.exception("Database or source data unavailable")
            return response(code=503, message="数据尚未就绪，请检查数据库及数据字典", status=503)
        except Exception:
            logger.exception("Unhandled API error")
            return response(code=500, message="服务暂时不可用，请稍后重试", status=500)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        message = "资源不存在" if exc.status_code == 404 else "请求失败"
        if isinstance(exc.detail, str) and exc.detail != "Not Found":
            message = exc.detail
        return response(code=exc.status_code, message=message, status=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return response(code=422, message="请求参数不合法，请检查分页和筛选条件", status=422)

    def load_results(repo, selected):
        students, records = repo.load(**selected)
        return [calculate(s, records[s["student_id"]], repo.as_of) for s in students]

    def individual(student_id, repo):
        results = load_results(repo, {"student_id": student_id})
        if not results:
            raise HTTPException(404, "学生不存在")
        return results[0]

    def list_item(result):
        p = result["portrait"]
        basic = {k: v for k, v in p["basic"].items() if k != "enroll_date"}
        return dict(basic, total_score=p["total_score"], level=p["level"], academic=p["metrics"][0]["value"])

    @app.get("/api/meta/filters")
    def get_filters(repo=Depends(repository)):
        return response(repo.filters())

    @app.get("/api/students")
    def students(
        page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
        selected: dict = Depends(filters), repo=Depends(repository),
    ):
        results = load_results(repo, selected)
        start = (page - 1) * page_size
        return response({"list": [list_item(r) for r in results[start:start + page_size]],
                         "total": len(results), "page": page, "page_size": page_size})

    @app.get("/api/students/{student_id}/portrait")
    def portrait(student_id: str, repo=Depends(repository)):
        return response(individual(student_id, repo)["portrait"])

    @app.get("/api/students/{student_id}/scores")
    def scores(student_id: str, repo=Depends(repository)):
        return response(individual(student_id, repo)["scores"])

    @app.get("/api/students/{student_id}/consume")
    def consume(student_id: str, repo=Depends(repository)):
        return response(individual(student_id, repo)["consume"])

    @app.get("/api/students/{student_id}/library")
    def library(student_id: str, repo=Depends(repository)):
        return response(individual(student_id, repo)["library"])

    @app.get("/api/students/{student_id}/sport")
    def sport(student_id: str, repo=Depends(repository)):
        return response(individual(student_id, repo)["sport"])

    def major_groups(results):
        groups = defaultdict(list)
        for r in results:
            groups[r["portrait"]["basic"]["major"]].append(r)
        summaries = []
        for major, rows in sorted(groups.items()):
            summary = summarize_group(rows)
            summaries.append({"major": major, "students": summary["students"],
                              "avg_score": summary["avg_score"], "dims": summary["avg_metrics"]})
        return summaries

    @app.get("/api/analytics/overview")
    def overview(selected: dict = Depends(filters), repo=Depends(repository)):
        results = load_results(repo, selected)
        groups = major_groups(results)
        eligible = {r["portrait"]["basic"]["major"] for r in results if len(r["portrait"]["missing_metrics"]) < 6}
        ranked = sorted((g for g in groups if g["major"] in eligible), key=lambda g: (-g["avg_score"], g["major"]))
        return response(dict(summarize_group(results), alert_count=sum(bool(r["reason"]) for r in results),
                             top_major=ranked[0]["major"] if ranked else ""))

    @app.get("/api/analytics/majors")
    def majors(selected: dict = Depends(filters), repo=Depends(repository)):
        return response(major_groups(load_results(repo, selected)))

    @app.get("/api/analytics/alerts")
    def alerts(selected: dict = Depends(filters), repo=Depends(repository)):
        results = [r for r in load_results(repo, selected) if r["reason"]]
        results.sort(key=lambda r: (r["portrait"]["total_score"], r["portrait"]["basic"]["student_id"]))
        return response([{k: v for k, v in dict(list_item(r), reason=r["reason"]).items()
                          if k not in ("gender", "enroll_year", "academic")} for r in results])

    return app


app = create_app()
