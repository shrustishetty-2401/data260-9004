from datetime import datetime

from mcp.server.fastmcp import FastMCP
from sqlalchemy import func, select

from database import db_session_basede26
from models import Vulnerability

mcp = FastMCP("s9004-domain")


def success(data):
    return {"ok": True, "data": data, "error": None}


def failure(message):
    return {"ok": False, "data": None, "error": message}


def serialize_datetime(value: datetime | None):
    if value is None:
        return None
    return value.isoformat()


def serialize_vulnerability(item):
    return {
        "id": item.id,
        "vulnerability_code": item.vulnerability_code,
        "vulnerability_title": item.vulnerability_title,
        "package_id": item.package_id,
        "package_name": item.package_name,
        "category": item.category,
        "available_count": item.available_count,
        "submission_date": serialize_datetime(item.submission_date),
        "created_at": serialize_datetime(item.created_at),
        "updated_at": serialize_datetime(item.updated_at),
    }


@mcp.tool()
def search_vulnerabilities(query: str, limit: int = 10):
    if not query.strip():
        return failure("query must not be empty")

    if limit < 1 or limit > 50:
        return failure("limit must be between 1 and 50")

    pattern = f"%{query.strip()}%"

    with db_session_basede26() as db:
        statement = (
            select(Vulnerability)
            .where(
                Vulnerability.vulnerability_title.ilike(pattern)
                | Vulnerability.package_name.ilike(pattern)
                | Vulnerability.vulnerability_code.ilike(pattern)
            )
            .order_by(Vulnerability.id.desc())
            .limit(limit)
        )

        results = db.scalars(statement).all()

    return success([serialize_vulnerability(item) for item in results])


@mcp.tool()
def vulnerability_detail(vulnerability_id: int):
    if vulnerability_id < 1:
        return failure("vulnerability_id must be positive")

    with db_session_basede26() as db:
        item = db.get(Vulnerability, vulnerability_id)

    if item is None:
        return failure("vulnerability not found")

    return success(serialize_vulnerability(item))


@mcp.tool()
def vulnerability_aggregate():
    with db_session_basede26() as db:
        total = db.scalar(
            select(func.count()).select_from(Vulnerability)
        )

        category_rows = db.execute(
            select(
                Vulnerability.category,
                func.count(Vulnerability.id),
            )
            .group_by(Vulnerability.category)
            .order_by(Vulnerability.category)
        ).all()

        package_rows = db.execute(
            select(
                Vulnerability.package_name,
                func.count(Vulnerability.id),
            )
            .group_by(Vulnerability.package_name)
            .order_by(func.count(Vulnerability.id).desc())
            .limit(10)
        ).all()

    return success(
        {
            "database": "s9004_rel",
            "total_vulnerabilities": total,
            "by_category": [
                {"category": category, "count": count}
                for category, count in category_rows
            ],
            "top_packages": [
                {"package_name": package, "count": count}
                for package, count in package_rows
            ],
        }
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")