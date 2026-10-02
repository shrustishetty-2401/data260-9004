from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from auth_db_router import current_user
from database import get_db
from models import Package, RelatedItem, Vulnerability


router = APIRouter(prefix="/api/reports", tags=["reports"])
package_router = APIRouter(prefix="/api/packages", tags=["packages"])


class PackageCreate(BaseModel):
    name: str = Field(min_length=1)
    ecosystem: str = Field(min_length=1)
    package_code: str = Field(
        min_length=1,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )


class PackageUpdate(PackageCreate):
    pass


class PackageOut(BaseModel):
    id: int
    name: str
    ecosystem: str
    package_code: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
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
    package_id: int
    vulnerability_code: str
    available_count: int
    vulnerability_title: str = Field(alias="vulnerabilityTitle")
    package_name: str = Field(alias="packageName")
    submitter_email: str = Field(alias="submitterEmail")
    description: str
    category: str
    terms_accepted: bool = Field(alias="termsAccepted")
    submission_date: datetime = Field(alias="submissionDate")
    created_at: datetime
    updated_at: datetime
    related_items: list[RelatedItemOut] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


def serialize_report(report: Vulnerability) -> dict:
    return ReportOut.model_validate(report).model_dump(
        by_alias=True,
    )


def package_code_for_name(package_name: str) -> str:
    safe_name = package_name.strip().lower()
    safe_name = safe_name.replace(" ", "-")
    return f"pkg-{safe_name}"


def get_or_create_package(
    package_name: str,
    db: Session,
) -> Package:
    package_code = package_code_for_name(package_name)

    package = db.scalar(
        select(Package).where(
            Package.package_code == package_code,
        )
    )

    if package is not None:
        return package

    package = Package(
        name=package_name,
        ecosystem="python",
        package_code=package_code,
    )

    db.add(package)
    db.flush()

    return package


@package_router.post(
    "",
    response_model=PackageOut,
    status_code=201,
)
def create_package(
    payload: PackageCreate,
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    existing_package = db.scalar(
        select(Package).where(
            Package.package_code == payload.package_code,
        )
    )

    if existing_package is not None:
        raise HTTPException(
            status_code=409,
            detail="Package code already exists",
        )

    package = Package(
        name=payload.name,
        ecosystem=payload.ecosystem,
        package_code=payload.package_code,
    )

    db.add(package)
    db.commit()
    db.refresh(package)

    return package


@package_router.get(
    "",
    response_model=list[PackageOut],
)
def list_packages(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=200),
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    statement = (
        select(Package)
        .order_by(Package.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return db.scalars(statement).all()


@package_router.get(
    "/{package_id}",
    response_model=PackageOut,
)
def get_package(
    package_id: int,
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    package = db.get(Package, package_id)

    if package is None:
        raise HTTPException(
            status_code=404,
            detail="Package not found",
        )

    return package


@package_router.put(
    "/{package_id}",
    response_model=PackageOut,
)
def update_package(
    package_id: int,
    payload: PackageUpdate,
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    package = db.get(Package, package_id)

    if package is None:
        raise HTTPException(
            status_code=404,
            detail="Package not found",
        )

    duplicate = db.scalar(
        select(Package).where(
            Package.package_code == payload.package_code,
            Package.id != package_id,
        )
    )

    if duplicate is not None:
        raise HTTPException(
            status_code=409,
            detail="Package code already exists",
        )

    package.name = payload.name
    package.ecosystem = payload.ecosystem
    package.package_code = payload.package_code

    db.commit()
    db.refresh(package)

    return package


@package_router.delete(
    "/{package_id}",
)
def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    package = db.get(Package, package_id)

    if package is None:
        raise HTTPException(
            status_code=404,
            detail="Package not found",
        )

    linked_vulnerability = db.scalar(
        select(Vulnerability.id)
        .where(Vulnerability.package_id == package_id)
        .limit(1)
    )

    if linked_vulnerability is not None:
        raise HTTPException(
            status_code=409,
            detail="Package cannot be deleted while vulnerabilities use it",
        )

    db.delete(package)
    db.commit()

    return {
        "message": "Package deleted successfully",
        "deleted_id": package_id,
    }


@package_router.get(
    "/{package_id}/vulnerabilities",
    response_model=list[ReportOut],
)
def list_package_vulnerabilities(
    package_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=200),
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    package = db.get(Package, package_id)

    if package is None:
        raise HTTPException(
            status_code=404,
            detail="Package not found",
        )

    statement = (
        select(Vulnerability)
        .options(selectinload(Vulnerability.related_items))
        .where(Vulnerability.package_id == package_id)
        .order_by(Vulnerability.id.desc())
        .offset(skip)
        .limit(limit)
    )

    reports = db.scalars(statement).all()

    return [
        serialize_report(report)
        for report in reports
    ]


@router.get(
    "",
    response_model=list[ReportOut],
)
def list_reports(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=200),
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    statement = (
        select(Vulnerability)
        .options(
            selectinload(Vulnerability.related_items),
            selectinload(Vulnerability.package),
        )
        .order_by(Vulnerability.id.desc())
        .offset(skip)
        .limit(limit)
    )

    reports = db.scalars(statement).all()

    return [
        serialize_report(report)
        for report in reports
    ]


@router.get(
    "/{report_id}",
    response_model=ReportOut,
)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    _user=Depends(current_user),
):
    statement = (
        select(Vulnerability)
        .options(
            selectinload(Vulnerability.related_items),
            selectinload(Vulnerability.package),
        )
        .where(Vulnerability.id == report_id)
    )

    report = db.scalar(statement)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return serialize_report(report)


@router.post(
    "",
    response_model=ReportOut,
    status_code=201,
)
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

    package = get_or_create_package(
        payload.package_name,
        db,
    )

    report = Vulnerability(
        package_id=package.id,
        vulnerability_code=f"VULN-{uuid4().hex}",
        available_count=0,
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


@router.put(
    "/{report_id}",
    response_model=ReportOut,
)
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

    package = get_or_create_package(
        payload.package_name,
        db,
    )

    report.package_id = package.id
    report.package_name = payload.package_name
    report.vulnerability_title = payload.vulnerability_title

    db.commit()
    db.refresh(report)

    return serialize_report(report)


@router.delete(
    "/{report_id}",
)
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