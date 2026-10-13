from fastapi import APIRouter, HTTPException, Response, status
from bson import ObjectId
from pymongo.errors import PyMongoError

from document_schemas import (
    VulnerabilityCreate,
    VulnerabilityResponse,
    VulnerabilityUpdate,
)
from mongo_database import utc_now, vulnerabilities_collection


router = APIRouter(
    prefix="/api/documents",
    tags=["MongoDB documents"],
)


def get_object_id(document_id: str) -> ObjectId:
    if not ObjectId.is_valid(document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID",
        )

    return ObjectId(document_id)


def serialize_document(document: dict) -> dict:
    return {
        "id": str(document["_id"]),
        "title": document["title"],
        "description": document.get("description"),
        "severity": document["severity"],
        "status": document["status"],
        "discovered_at": document["discovered_at"],
        "created_at": document["created_at"],
        "updated_at": document["updated_at"],
    }


@router.post(
    "",
    response_model=VulnerabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document(payload: VulnerabilityCreate):
    now = utc_now()

    document = payload.model_dump()
    document["severity"] = payload.severity.value
    document["status"] = payload.status.value
    document["created_at"] = now
    document["updated_at"] = now

    try:
        result = vulnerabilities_collection.insert_one(document)
        saved_document = vulnerabilities_collection.find_one(
            {"_id": result.inserted_id}
        )
        return serialize_document(saved_document)
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {error}",
        ) from error


@router.get(
    "",
    response_model=list[VulnerabilityResponse],
)
def get_all_documents():
    try:
        documents = vulnerabilities_collection.find().sort(
            "created_at",
            -1,
        )
        return [serialize_document(document) for document in documents]
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {error}",
        ) from error


@router.get(
    "/{document_id}",
    response_model=VulnerabilityResponse,
)
def get_document(document_id: str):
    object_id = get_object_id(document_id)
    document = vulnerabilities_collection.find_one({"_id": object_id})

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return serialize_document(document)


@router.put(
    "/{document_id}",
    response_model=VulnerabilityResponse,
)
def update_document(
    document_id: str,
    payload: VulnerabilityUpdate,
):
    object_id = get_object_id(document_id)
    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field is required for update",
        )

    if payload.severity is not None:
        changes["severity"] = payload.severity.value

    if payload.status is not None:
        changes["status"] = payload.status.value

    changes["updated_at"] = utc_now()

    result = vulnerabilities_collection.update_one(
        {"_id": object_id},
        {"$set": changes},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    updated_document = vulnerabilities_collection.find_one(
        {"_id": object_id}
    )

    return serialize_document(updated_document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(document_id: str):
    object_id = get_object_id(document_id)
    result = vulnerabilities_collection.delete_one({"_id": object_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
