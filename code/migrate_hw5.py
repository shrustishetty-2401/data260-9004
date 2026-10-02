from sqlalchemy import inspect, text
from database import engine
from models import Base, Package


def column_exists(table_name: str, column_name: str) -> bool:
    columns = inspect(engine).get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def add_column_if_missing(
    table_name: str,
    column_name: str,
    definition: str,
) -> None:
    if column_exists(table_name, column_name):
        print(f"Column already exists: {table_name}.{column_name}")
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                f"ALTER TABLE {table_name} "
                f"ADD COLUMN {column_name} {definition}"
            )
        )

    print(f"Added column: {table_name}.{column_name}")


def main() -> None:
    Base.metadata.create_all(
        bind=engine,
        tables=[Package.__table__],
    )

    add_column_if_missing(
        "vulnerabilities",
        "package_id",
        "INT NULL",
    )

    add_column_if_missing(
        "vulnerabilities",
        "vulnerability_code",
        "VARCHAR(255) NULL",
    )

    add_column_if_missing(
        "vulnerabilities",
        "available_count",
        "INT NOT NULL DEFAULT 0",
    )

    add_column_if_missing(
        "vulnerabilities",
        "created_at",
        "DATETIME NULL",
    )

    add_column_if_missing(
        "vulnerabilities",
        "updated_at",
        "DATETIME NULL",
    )

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO packages
                    (name, ecosystem, package_code, created_at, updated_at)
                SELECT DISTINCT
                    v.package_name,
                    'python',
                    CONCAT('pkg-', v.package_name),
                    NOW(),
                    NOW()
                FROM vulnerabilities AS v
                LEFT JOIN packages AS p
                    ON p.name = v.package_name
                WHERE p.id IS NULL
                """
            )
        )

        connection.execute(
            text(
                """
                UPDATE vulnerabilities AS v
                JOIN packages AS p
                    ON p.name = v.package_name
                SET v.package_id = p.id
                WHERE v.package_id IS NULL
                """
            )
        )

        connection.execute(
            text(
                """
                UPDATE vulnerabilities
                SET vulnerability_code = CONCAT('VULN-', id)
                WHERE vulnerability_code IS NULL
                """
            )
        )

        connection.execute(
            text(
                """
                UPDATE vulnerabilities
                SET created_at = submission_date
                WHERE created_at IS NULL
                """
            )
        )

        connection.execute(
            text(
                """
                UPDATE vulnerabilities
                SET updated_at = submission_date
                WHERE updated_at IS NULL
                """
            )
        )

    indexes = inspect(engine).get_indexes("vulnerabilities")

    code_index_exists = any(
        index.get("unique")
        and "vulnerability_code" in index.get("column_names", [])
        for index in indexes
    )

    if not code_index_exists:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE vulnerabilities
                    ADD UNIQUE KEY uq_vulnerabilities_code
                    (vulnerability_code)
                    """
                )
            )

    foreign_keys = inspect(engine).get_foreign_keys("vulnerabilities")

    package_foreign_key_exists = any(
        foreign_key.get("referred_table") == "packages"
        and "package_id" in foreign_key.get("constrained_columns", [])
        for foreign_key in foreign_keys
    )

    if not package_foreign_key_exists:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE vulnerabilities
                    ADD CONSTRAINT fk_vulnerabilities_package
                    FOREIGN KEY (package_id)
                    REFERENCES packages(id)
                    ON DELETE RESTRICT
                    """
                )
            )

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE vulnerabilities
                MODIFY COLUMN package_id INT NOT NULL
                """
            )
        )

        connection.execute(
            text(
                """
                ALTER TABLE vulnerabilities
                MODIFY COLUMN vulnerability_code VARCHAR(255) NOT NULL
                """
            )
        )

        connection.execute(
            text(
                """
                ALTER TABLE vulnerabilities
                MODIFY COLUMN created_at DATETIME NOT NULL
                """
            )
        )

        connection.execute(
            text(
                """
                ALTER TABLE vulnerabilities
                MODIFY COLUMN updated_at DATETIME NOT NULL
                """
            )
        )

    print("HW5 database migration completed successfully.")


if __name__ == "__main__":
    main()