import csv
import random
from pathlib import Path


OUTPUT_DIR = Path("reports/hw07/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def write_dataset(
    filename: str,
    member_count: int,
    casual_count: int,
    seed: int,
):
    rng = random.Random(seed)
    output_path = OUTPUT_DIR / filename

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "trip_id",
                "duration_min",
                "member_type",
                "day_of_week",
                "start_hour",
            ]
        )

        trip_id = 1

        for _ in range(member_count):
            writer.writerow(
                [
                    trip_id,
                    rng.randint(10, 35),
                    "member",
                    rng.choice(
                        [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                        ]
                    ),
                    rng.randint(7, 18),
                ]
            )
            trip_id += 1

        for _ in range(casual_count):
            writer.writerow(
                [
                    trip_id,
                    rng.randint(15, 60),
                    "casual",
                    rng.choice(
                        [
                            "Saturday",
                            "Sunday",
                            "Friday",
                        ]
                    ),
                    rng.randint(10, 20),
                ]
            )
            trip_id += 1

    print(f"Created {output_path}")
    print(f"Rows: {member_count + casual_count}")
    print(f"Member rides: {member_count}")
    print(f"Casual rides: {casual_count}")


def main():
    write_dataset(
        filename="bikeshare_membership_wins.csv",
        member_count=700,
        casual_count=100,
        seed=9004,
    )

    write_dataset(
        filename="bikeshare_pay_per_use_wins.csv",
        member_count=100,
        casual_count=700,
        seed=269004,
    )


if __name__ == "__main__":
    main()
