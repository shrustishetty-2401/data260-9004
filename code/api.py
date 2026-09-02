from datetime import datetime, timezone
from http.client import HTTPException
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="Open-Source Vulnerability Reports")


class VulnerabilityBase(BaseModel):
    vulnerabilityTitle: str = Field(min_length=1)
    packageName: str = Field(min_length=1)
    submitterEmail: str = Field(min_length=3)
    description: str = Field(min_length=26)
    category: str = Field(min_length=1)
    termsAccepted: bool


class VulnerabilityCreate(VulnerabilityBase):
    pass


class VulnerabilityUpdate(BaseModel):
    vulnerabilityTitle: str = Field(min_length=1)
    packageName: str = Field(min_length=1)


records = [
    {
        "id": 1,
        "vulnerabilityTitle": "Unsafe deserialization in SampleLib",
        "packageName": "samplelib",
        "submitterEmail": "security@example.com",
        "description": "An unsafe deserialization flaw allows attackers to execute unintended code.",
        "category": "Remote Code Execution",
        "termsAccepted": True,
        "submissionDate": datetime.now(timezone.utc).isoformat(),
    }
]
@app.get("/api/reports")
def list_records(search: Optional[str] = None):
    """Return all records or only records matching the search text."""

    if not search:
        return records

    search_text = search.strip().lower()

    return [
        record
        for record in records
        if search_text in record["vulnerabilityTitle"].lower()
        or search_text in record["packageName"].lower()
    ]


@app.post("/api/reports", status_code=201)
def create_record(payload: VulnerabilityCreate):
    """Add a new vulnerability report."""

    if not payload.termsAccepted:
        raise HTTPException(
            status_code=400,
            detail="Terms must be accepted before submitting.",
        )

    next_id = max((record["id"] for record in records), default=0) + 1

    new_record = {
        "id": next_id,
        **payload.model_dump(),
        "submissionDate": datetime.now(timezone.utc).isoformat(),
    }

    records.append(new_record)

    return new_record
@app.put("/api/reports/1")
def update_first_record(payload: VulnerabilityUpdate):
    """Update the record with ID 1."""

    record = next(
        (item for item in records if item["id"] == 1),
        None,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Record with ID 1 was not found.",
        )

    record["vulnerabilityTitle"] = payload.vulnerabilityTitle
    record["packageName"] = payload.packageName

    return record
@app.delete("/api/reports/highest")
def delete_highest_record():
    """Delete the record with the highest ID."""

    if not records:
        raise HTTPException(
            status_code=404,
            detail="No records are available to delete.",
        )

    highest_record = max(records, key=lambda record: record["id"])
    records.remove(highest_record)

    return {
        "deleted": highest_record,
        "remaining_records": records,
    }