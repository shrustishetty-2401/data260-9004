import time

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from bikeshare_tools import calculator, csv_sql, policy_retriever


router = APIRouter(
    prefix="/api/bikeshare",
    tags=["bike-share"],
)


CITI_BIKE_PRICING = {
    "system": "Citi Bike",
    "annual_membership": 239.00,
    "classic_ride_price": 4.99,
    "pricing_basis": "Citi Bike pricing snapshot",
}


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
    total_rides = member_rides + casual_rides

    weekly_membership_cost = CITI_BIKE_PRICING["annual_membership"] / 52
    weekly_pay_per_use_cost = total_rides * CITI_BIKE_PRICING["classic_ride_price"]

    break_even_rides_per_year = round(
        CITI_BIKE_PRICING["annual_membership"]
        / CITI_BIKE_PRICING["classic_ride_price"],
        2,
    )

    if member_rides > casual_rides:
        decision = "Buy Monthly Membership"
        reason = (
            "The uploaded trip history contains more member rides than "
            "casual rides, indicating stronger recurring membership usage."
        )
    elif casual_rides > member_rides:
        decision = "Pay Per Ride/Minute"
        reason = (
            "The uploaded trip history contains more casual rides than "
            "member rides, indicating stronger pay-per-use usage."
        )
    else:
        decision = "Pay Per Ride/Minute"
        reason = (
            "Member and casual rides are balanced, so pay-per-use is the "
            "more conservative starting option."
        )

    return {
        "decision": decision,
        "reason": reason,
        "member_rides": member_rides,
        "casual_rides": casual_rides,
        "total_rides": total_rides,
        "pricing_system": CITI_BIKE_PRICING["system"],
        "annual_membership_cost": CITI_BIKE_PRICING["annual_membership"],
        "classic_ride_price": CITI_BIKE_PRICING["classic_ride_price"],
        "weekly_membership_cost": round(weekly_membership_cost, 2),
        "weekly_pay_per_use_cost": round(weekly_pay_per_use_cost, 2),
        "break_even_rides_per_year": break_even_rides_per_year,
        "pricing_basis": CITI_BIKE_PRICING["pricing_basis"],
        "policy_source": pricing_result["data"]["source_url"],
        "pricing_snapshot_hash": pricing_result["data"]["sha256"],
    }


@router.post("/analyze")
async def analyze_bikeshare(
    file: UploadFile = File(...),
    pricing_url: str = Form(...),
):
    started = time.perf_counter()

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

    calculator_result = calculator(f"{CITI_BIKE_PRICING['annual_membership']} / 52")

    elapsed_ms = round(
        (time.perf_counter() - started) * 1000,
        2,
    )

    return {
        "filename": file.filename,
        "pricing_system": CITI_BIKE_PRICING["system"],
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
        "step_count": 3,
        "total_time_ms": elapsed_ms,
        "stop_reason": "completed",
    }
