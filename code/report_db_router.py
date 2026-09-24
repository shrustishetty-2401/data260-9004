from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from auth_db_router import current_user
from database import get_db
from models import RelatedItem, Vulnerability

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportCreate(BaseModel):
    vulnerability_title: str = Field(
        min_length=1,
        alias="vulnerabilityTitle",
    )
    package_name: str = Field(
        min_length=1,
        alias="packageName",
    )
    submitter_email: str = Field(
        min_length=3,
        alias="submitterEmail",
    )
    description: str = Field(min_length=26)
    category: str = Field(min_length=1)
    terms_accepted: bool = Field(alias="termsAccepted")

    model_config = ConfigDict(populate_by_name=True)


class ReportUpdate(BaseModel):
    vulnerability_title: str = Field(
        min_length=1,
        alias="vulnerabilityTitle",
    )
    package_name: str = Field(
        min_length=1,
        alias="packageName",
    )

    model_config = ConfigDict(populate_by_name=True)


class RelatedItemOut(BaseModel):
    id: int
    related_text: str

    model_config = ConfigDict(from_attributes=True)


class ReportOut(BaseModel):
    id: int
    vulnerability_title: str = Field(alias="vulnerabilityTitle")
    package_name: str = Field(alias="packageName")
    submitter_email: str = Field(alias="submitterEmail")
    description: str
    category: str
    terms_accepted: bool = Field(alias="termsAccepted")
    submission_date: datetime = Field(alias="submissionDate")
    related_items: list[RelatedItemOut] = []

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


def serialize_report(report: Vulnerability) -> dict:
    return ReportOut.model_validate(report).model_dump(
        by_alias=True,
    )


@router.get("", response_model=list[ReportOut])
def list_reports(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=200),
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    statement = (
        select(Vulnerability)
        .options(selectinload(Vulnerability.related_items))
        .order_by(Vulnerability.id.desc())
        .offset(skip)
        .limit(limit)
    )

    reports = db.scalars(statement).all()
    return [serialize_report(report) for report in reports]


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    statement = (
        select(Vulnerability)
        .options(selectinload(Vulnerability.related_items))
        .where(Vulnerability.id == report_id)
    )

    report = db.scalar(statement)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return serialize_report(report)


@router.post("", response_model=ReportOut, status_code=201)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    if not payload.terms_accepted:
        raise HTTPException(
            status_code=400,
            detail="Terms must be accepted before submitting",
        )

    report = Vulnerability(
        vulnerability_title=payload.vulnerability_title,
        package_name=payload.package_name,
        submitter_email=payload.submitter_email,
        description=payload.description,
        category=payload.category,
        terms_accepted=payload.terms_accepted,
        submission_date=datetime.now(timezone.utc).replace(
            tzinfo=None,
        ),
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return serialize_report(report)


@router.put("/{report_id}", response_model=ReportOut)
def update_report(
    report_id: int,
    payload: ReportUpdate,
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    report = db.get(Vulnerability, report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    report.vulnerability_title = payload.vulnerability_title
    report.package_name = payload.package_name

    db.commit()
    db.refresh(report)

    return serialize_report(report)


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    report = db.get(Vulnerability, report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    db.delete(report)
    db.commit()

    return {
        "message": "Report deleted successfully",
        "deleted_id": report_id,
    }