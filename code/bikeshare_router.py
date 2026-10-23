from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from bikeshare_tools import (
    calculator,
    csv_sql,
    policy_retriever,
)


router = APIRouter(
    prefix="/api/bikeshare",
    tags=["bike-share"],
)


def build_decision(csv_result, pricing_result):
    if not csv_result["ok"]:
        return {
            "decision": "Unable to analyze CSV",
            "reason": csv_result["error"],
        }

    if not pricing_result["ok"]:
        return {
            "decision": "Unable to retrieve pricing",
            "reason": pricing_result["error"],
        }

    weekly_summary = csv_result["data"]["weekly_summary"]

    member_row = next(row for row in weekly_summary if row["member_type"] == "member")

    casual_row = next(row for row in weekly_summary if row["member_type"] == "casual")

    member_rides = member_row["rides"]
    casual_rides = casual_row["rides"]

    if member_rides > casual_rides:
        decision = "Membership is the stronger starting option"
        reason = (
            "The uploaded trip history contains more member rides than casual rides."
        )
    elif casual_rides > member_rides:
        decision = "Pay-per-use is the stronger starting option"
        reason = (
            "The uploaded trip history contains more casual rides than member rides."
        )
    else:
        decision = "Both options require similar consideration"
        reason = (
            "The uploaded trip history contains an equal number "
            "of member and casual rides."
        )

    return {
        "decision": decision,
        "reason": reason,
        "member_rides": member_rides,
        "casual_rides": casual_rides,
        "policy_source": pricing_result["data"]["source_url"],
        "pricing_snapshot_hash": pricing_result["data"]["sha256"],
    }


@router.post("/analyze")
async def analyze_bikeshare(
    file: UploadFile = File(...),
    pricing_url: str = Form(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="CSV filename is required",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are accepted",
        )

    csv_bytes = await file.read()

    try:
        csv_text = csv_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail="CSV must be UTF-8 encoded",
        ) from error

    csv_result = csv_sql(csv_text)
    pricing_result = policy_retriever(pricing_url)

    decision = build_decision(
        csv_result,
        pricing_result,
    )

    calculator_result = calculator("239 / 52")

    return {
        "filename": file.filename,
        "timeline": [
            {
                "step": 1,
                "tool": "csv_sql",
                "status": "completed",
                "result": csv_result,
            },
            {
                "step": 2,
                "tool": "policy_retriever",
                "status": "completed",
                "result": pricing_result,
            },
            {
                "step": 3,
                "tool": "calculator",
                "status": "completed",
                "result": calculator_result,
            },
        ],
        "csv_analysis": csv_result,
        "pricing_policy": pricing_result,
        "calculation": calculator_result,
        "decision": decision,
        "stop_reason": "completed",
    }
