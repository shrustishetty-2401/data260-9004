import random
from datetime import datetime, timedelta

from sqlalchemy import delete

from database import SessionLocal
from models import RelatedItem, Vulnerability

SEED = 9004
PRIMARY_ROWS = 5000
RELATED_ROWS = 200


def main() -> None:
    rng = random.Random(SEED)

    with SessionLocal() as db:
        db.execute(delete(RelatedItem))
        db.execute(delete(Vulnerability))
        db.commit()

        start_time = datetime(2026, 1, 1)
        vulnerabilities = []

        for row_number in range(1, PRIMARY_ROWS + 1):
            vulnerabilities.append(
                Vulnerability(
                    vulnerability_title=(
                        f"Seeded vulnerability {row_number}"
                    ),
                    package_name=f"package-{row_number % 250}",
                    submitter_email=(
                        f"researcher{row_number}@example.com"
                    ),
                    description=(
                        "Deterministic seeded vulnerability record for "
                        "the DATA-260 HW4 database benchmark."
                    ),
                    category=(
                        "Dependency Risk"
                        if row_number % 2 == 0
                        else "Input Validation"
                    ),
                    terms_accepted=True,
                    submission_date=start_time + timedelta(
                        minutes=row_number,
                    ),
                )
            )

        db.add_all(vulnerabilities)
        db.commit()

        vulnerability_ids = [
            item.id for item in vulnerabilities
        ]

        related_items = []

        for related_number in range(1, RELATED_ROWS + 1):
            vulnerability_id = rng.choice(vulnerability_ids)

            related_items.append(
                RelatedItem(
                    vulnerability_id=vulnerability_id,
                    related_text=(
                        f"Related benchmark note {related_number} "
                        f"for vulnerability {vulnerability_id}."
                    ),
                )
            )

        db.add_all(related_items)
        db.commit()

    print(f"Seeded vulnerabilities: {PRIMARY_ROWS}")
    print(f"Seeded related items: {RELATED_ROWS}")
    print(f"Seed: {SEED}")


if __name__ == "__main__":
    main()