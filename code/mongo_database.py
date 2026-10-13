import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "s9004_doc")

mongo_client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=3000,
)

mongo_db = mongo_client[MONGO_DB_NAME]

vulnerabilities_collection = mongo_db["vulnerabilities"]
messages_collection = mongo_db["messages"]
summaries_collection = mongo_db["summaries"]
episodes_collection = mongo_db["episodes"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_mongo_setup() -> None:
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "title",
                "severity",
                "status",
                "discovered_at",
                "created_at",
                "updated_at",
            ],
            "properties": {
                "title": {
                    "bsonType": "string",
                    "maxLength": 100,
                },
                "description": {
                    "bsonType": ["string", "null"],
                    "maxLength": 5000,
                },
                "severity": {
                    "enum": ["low", "medium", "high", "critical"],
                },
                "status": {
                    "enum": ["open", "triaged", "resolved"],
                },
                "discovered_at": {
                    "bsonType": "date",
                },
                "created_at": {
                    "bsonType": "date",
                },
                "updated_at": {
                    "bsonType": "date",
                },
            },
        }
    }

    collection_names = mongo_db.list_collection_names()

    if "vulnerabilities" not in collection_names:
        mongo_db.create_collection(
            "vulnerabilities",
            validator=validator,
            validationLevel="strict",
            validationAction="error",
        )
    else:
        mongo_db.command(
            "collMod",
            "vulnerabilities",
            validator=validator,
            validationLevel="strict",
            validationAction="error",
        )

    vulnerabilities_collection.create_index(
        [("created_at", DESCENDING)]
    )

    messages_collection.create_index(
        [("user_id", ASCENDING), ("session_id", ASCENDING), ("created_at", DESCENDING)]
    )

    summaries_collection.create_index(
        [("user_id", ASCENDING), ("scope", ASCENDING), ("created_at", DESCENDING)]
    )

    episodes_collection.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)]
    )


def check_mongo_connection() -> dict:
    result = mongo_client.admin.command("ping")

    return {
        "ok": result.get("ok") == 1.0,
        "database": MONGO_DB_NAME,
    }
