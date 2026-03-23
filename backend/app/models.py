from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String, nullable=False)
    source = Column(String, nullable=False)
    city = Column(String, nullable=False)
    city_name = Column(String, nullable=False)
    state = Column(String, nullable=False)
    file_number = Column(String, nullable=True)
    title = Column(String, nullable=False)
    type_name = Column(String, nullable=True)
    status = Column(String, nullable=True)
    body_name = Column(String, nullable=True)
    intro_date = Column(DateTime, nullable=True)
    agenda_date = Column(DateTime, nullable=True)
    passed_date = Column(DateTime, nullable=True)
    enactment_number = Column(String, nullable=True)
    enactment_date = Column(DateTime, nullable=True)
    url = Column(String, nullable=True)
    topics = Column(Text, nullable=True)  # JSON-encoded list of topic strings
    updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("source", "source_id", "city", name="uq_source_bill"),
        Index("ix_bills_city", "city"),
        Index("ix_bills_status", "status"),
        Index("ix_bills_type_name", "type_name"),
        Index("ix_bills_intro_date", "intro_date"),
    )

    def __repr__(self) -> str:
        return f"<Bill(id={self.id}, city={self.city}, file_number={self.file_number})>"


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(12), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    items = relationship(
        "CollectionItem",
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, slug={self.slug}, name={self.name})>"


class CollectionItem(Base):
    __tablename__ = "collection_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(
        Integer,
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    bill_id = Column(
        Integer,
        ForeignKey("bills.id", ondelete="CASCADE"),
        nullable=False,
    )
    note = Column(Text, nullable=True)
    added_at = Column(DateTime, server_default=func.now())

    collection = relationship("Collection", back_populates="items")
    bill = relationship("Bill", lazy="joined")

    __table_args__ = (
        UniqueConstraint("collection_id", "bill_id", name="uq_collection_bill"),
    )

    def __repr__(self) -> str:
        return f"<CollectionItem(id={self.id}, collection_id={self.collection_id}, bill_id={self.bill_id})>"


class BillBriefing(Base):
    __tablename__ = "bill_briefings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(
        Integer,
        ForeignKey("bills.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    summary = Column(Text, nullable=True)
    impact = Column(Text, nullable=True)
    organizing = Column(Text, nullable=True)
    reception = Column(Text, nullable=True)
    news_json = Column(Text, nullable=True)  # JSON list of {title, url, source, date}
    generated_at = Column(DateTime, server_default=func.now())

    bill = relationship("Bill", lazy="joined")

    def __repr__(self) -> str:
        return f"<BillBriefing(id={self.id}, bill_id={self.bill_id})>"


class BillEmbedding(Base):
    __tablename__ = "bill_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(
        Integer,
        ForeignKey("bills.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    embedding_json = Column(Text, nullable=False)  # JSON array of floats

    def __repr__(self) -> str:
        return f"<BillEmbedding(id={self.id}, bill_id={self.bill_id})>"
