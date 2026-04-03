import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Bill, Collection, CollectionItem
from app.routers.bills import bill_to_response
from app.schemas import (
    CollectionCreate,
    CollectionItemAdd,
    CollectionItemResponse,
    CollectionItemUpdate,
    CollectionResponse,
    CollectionUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/collections", tags=["collections"])


def _get_collection_by_slug(db: Session, slug: str) -> Collection:
    """Look up a collection by slug or raise 404."""
    collection = (
        db.query(Collection)
        .options(selectinload(Collection.items).selectinload(CollectionItem.bill))
        .filter(Collection.slug == slug)
        .first()
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


def _build_item_response(item: CollectionItem) -> CollectionItemResponse:
    """Convert a CollectionItem ORM object to its response schema."""
    return CollectionItemResponse(
        id=item.id,
        bill_id=item.bill_id,
        bill=bill_to_response(item.bill),
        note=item.note,
        added_at=item.added_at,
    )


def _build_collection_response(collection: Collection) -> CollectionResponse:
    """Convert a Collection ORM object to its response schema."""
    return CollectionResponse(
        id=collection.id,
        slug=collection.slug,
        name=collection.name,
        description=collection.description,
        items=[_build_item_response(item) for item in collection.items],
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.post("", response_model=CollectionResponse, status_code=201)
def create_collection(
    body: CollectionCreate,
    db: Session = Depends(get_db),
) -> CollectionResponse:
    slug = secrets.token_urlsafe(9)  # produces 12 URL-safe characters
    collection = Collection(
        slug=slug,
        name=body.name,
        description=body.description,
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    logger.info(
        "Collection created",
        extra={
            "event": "collection_created",
            "collection_id": collection.id,
            "slug": collection.slug,
        },
    )
    return _build_collection_response(collection)


@router.get("/{slug}", response_model=CollectionResponse)
def get_collection(
    slug: str,
    db: Session = Depends(get_db),
) -> CollectionResponse:
    collection = _get_collection_by_slug(db, slug)
    return _build_collection_response(collection)


@router.patch("/{slug}", response_model=CollectionResponse)
def update_collection(
    slug: str,
    body: CollectionUpdate,
    db: Session = Depends(get_db),
) -> CollectionResponse:
    collection = _get_collection_by_slug(db, slug)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(collection, field, value)
    db.commit()
    db.refresh(collection)
    logger.info(
        "Collection updated",
        extra={
            "event": "collection_updated",
            "collection_id": collection.id,
            "slug": collection.slug,
            "fields_updated": list(update_data.keys()),
        },
    )
    return _build_collection_response(collection)


@router.delete("/{slug}", status_code=204)
def delete_collection(
    slug: str,
    db: Session = Depends(get_db),
) -> Response:
    collection = _get_collection_by_slug(db, slug)
    logger.info(
        "Collection deleted",
        extra={
            "event": "collection_deleted",
            "collection_id": collection.id,
            "slug": collection.slug,
        },
    )
    db.delete(collection)
    db.commit()
    return Response(status_code=204)


@router.post(
    "/{slug}/items",
    response_model=CollectionItemResponse,
    status_code=201,
)
def add_item_to_collection(
    slug: str,
    body: CollectionItemAdd,
    db: Session = Depends(get_db),
) -> CollectionItemResponse:
    collection = _get_collection_by_slug(db, slug)

    bill = db.query(Bill).filter(Bill.id == body.bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    existing = (
        db.query(CollectionItem)
        .filter(
            CollectionItem.collection_id == collection.id,
            CollectionItem.bill_id == body.bill_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="Bill already in collection"
        )

    item = CollectionItem(
        collection_id=collection.id,
        bill_id=body.bill_id,
        note=body.note,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    logger.info(
        "Item added to collection",
        extra={
            "event": "collection_item_added",
            "collection_id": collection.id,
            "slug": collection.slug,
            "bill_id": body.bill_id,
            "item_id": item.id,
        },
    )
    return _build_item_response(item)


@router.patch(
    "/{slug}/items/{item_id}",
    response_model=CollectionItemResponse,
)
def update_collection_item(
    slug: str,
    item_id: int,
    body: CollectionItemUpdate,
    db: Session = Depends(get_db),
) -> CollectionItemResponse:
    collection = _get_collection_by_slug(db, slug)
    item = (
        db.query(CollectionItem)
        .filter(
            CollectionItem.id == item_id,
            CollectionItem.collection_id == collection.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Collection item not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    logger.info(
        "Collection item updated",
        extra={
            "event": "collection_item_updated",
            "collection_id": collection.id,
            "slug": collection.slug,
            "item_id": item.id,
        },
    )
    return _build_item_response(item)


@router.delete("/{slug}/items/{item_id}", status_code=204)
def delete_collection_item(
    slug: str,
    item_id: int,
    db: Session = Depends(get_db),
) -> Response:
    collection = _get_collection_by_slug(db, slug)
    item = (
        db.query(CollectionItem)
        .filter(
            CollectionItem.id == item_id,
            CollectionItem.collection_id == collection.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Collection item not found")

    logger.info(
        "Collection item deleted",
        extra={
            "event": "collection_item_deleted",
            "collection_id": collection.id,
            "slug": collection.slug,
            "item_id": item.id,
            "bill_id": item.bill_id,
        },
    )
    db.delete(item)
    db.commit()
    return Response(status_code=204)
