from contextvars import ContextVar

from fastapi import APIRouter, Depends, Query
from sqlalchemy import event, select
from sqlalchemy.orm import Session, selectinload

from auth_db_router import current_user
from database import engine, get_db
from models import Vulnerability

router = APIRouter(
    prefix="/api/benchmark",
    tags=["n-plus-one benchmark"],
)

_query_count: ContextVar[int | None] = ContextVar(
    "query_count",
    default=None,
)


@event.listens_for(engine, "before_cursor_execute")
def count_sql_statements(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    current_count = _query_count.get()

    if current_count is not None:
        _query_count.set(current_count + 1)


def serialize_report(report: Vulnerability) -> dict:
    return {
        "id": report.id,
        "vulnerabilityTitle": report.vulnerability_title,
        "packageName": report.package_name,
        "category": report.category,
        "relatedItems": [
            {
                "id": item.id,
                "text": item.related_text,
            }
            for item in report.related_items
        ],
    }


@router.get("/reports/{mode}")
def benchmark_reports(
    mode: str,
    page_size: int = Query(default=10, ge=1, le=200),
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    if mode not in {"naive", "fixed"}:
        return {
            "error": "mode must be naive or fixed",
        }

    token = _query_count.set(0)

    try:
        base_query = (
            select(Vulnerability)
            .order_by(Vulnerability.id)
            .limit(page_size)
        )

        if mode == "fixed":
            base_query = base_query.options(
                selectinload(Vulnerability.related_items)
            )

        reports = db.scalars(base_query).all()

        rows = [serialize_report(report) for report in reports]
        sql_statements = _query_count.get() or 0

    finally:
        _query_count.reset(token)

    return {
        "mode": mode,
        "page_size": page_size,
        "sql_statements": sql_statements,
        "rows_returned": len(rows),
        "rows": rows,
    }