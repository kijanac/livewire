from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


# Association table for bill sponsors (many-to-many)
bill_sponsors = Table(
    "bill_sponsors",
    Base.metadata,
    Column("bill_id", Integer, ForeignKey("bills.id", ondelete="CASCADE"), primary_key=True),
    Column("official_id", Integer, ForeignKey("officials.id", ondelete="CASCADE"), primary_key=True),
)


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
    enriched_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("source", "source_id", "city", name="uq_source_bill"),
        Index("ix_bills_city", "city"),
        Index("ix_bills_status", "status"),
        Index("ix_bills_type_name", "type_name"),
        Index("ix_bills_intro_date", "intro_date"),
        Index("ix_bills_agenda_date", "agenda_date"),
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
        lazy="select",
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
    bill = relationship("Bill", lazy="select")

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
    power_analysis = Column(Text, nullable=True)  # AI-generated power analysis
    narrative_json = Column(Text, nullable=True)  # JSON: cached narrative frame analysis
    coalition_json = Column(Text, nullable=True)  # JSON: cached coalition brief
    generated_at = Column(DateTime, server_default=func.now())

    bill = relationship("Bill", lazy="select")

    def __repr__(self) -> str:
        return f"<BillBriefing(id={self.id}, bill_id={self.bill_id})>"


class BillDocument(Base):
    __tablename__ = "bill_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(
        Integer,
        ForeignKey("bills.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)

    bill = relationship("Bill")

    __table_args__ = (
        UniqueConstraint("bill_id", "url", name="uq_bill_document"),
        Index("ix_bill_documents_bill_id", "bill_id"),
    )

    def __repr__(self) -> str:
        return f"<BillDocument(id={self.id}, bill_id={self.bill_id}, name={self.name})>"


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
    similar_json = Column(Text, nullable=True)  # JSON: [[bill_id, score], ...]

    def __repr__(self) -> str:
        return f"<BillEmbedding(id={self.id}, bill_id={self.bill_id})>"


class Official(Base):
    __tablename__ = "officials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String, nullable=False)
    city = Column(String, nullable=False)
    city_name = Column(String, nullable=False)
    state = Column(String, nullable=False)
    name = Column(String, nullable=False)
    title = Column(String, nullable=True)
    district = Column(String, nullable=True)
    party = Column(String, nullable=True)
    body_name = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    updated_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("source_id", "city", name="uq_official_source"),
        Index("ix_officials_city", "city"),
    )

    def __repr__(self) -> str:
        return f"<Official(id={self.id}, name={self.name}, city={self.city})>"


class VoteRecord(Base):
    __tablename__ = "vote_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(
        Integer,
        ForeignKey("bills.id", ondelete="CASCADE"),
        nullable=False,
    )
    official_id = Column(
        Integer,
        ForeignKey("officials.id", ondelete="CASCADE"),
        nullable=False,
    )
    vote_value = Column(String, nullable=False)  # Yea, Nay, Abstain, Absent
    vote_date = Column(DateTime, nullable=True)
    action_text = Column(String, nullable=True)

    bill = relationship("Bill")
    official = relationship("Official")

    __table_args__ = (
        UniqueConstraint("bill_id", "official_id", name="uq_vote_bill_official"),
        Index("ix_vote_records_bill_id", "bill_id"),
        Index("ix_vote_records_official_id", "official_id"),
    )

    def __repr__(self) -> str:
        return f"<VoteRecord(id={self.id}, bill_id={self.bill_id}, vote={self.vote_value})>"


class BillAction(Base):
    __tablename__ = "bill_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(
        Integer,
        ForeignKey("bills.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_date = Column(DateTime, nullable=True)
    action_text = Column(String, nullable=True)
    body_name = Column(String, nullable=True)
    result = Column(String, nullable=True)  # Pass, Fail, etc.
    mover_id = Column(Integer, ForeignKey("officials.id"), nullable=True)
    seconder_id = Column(Integer, ForeignKey("officials.id"), nullable=True)

    bill = relationship("Bill")
    mover = relationship("Official", foreign_keys=[mover_id])
    seconder = relationship("Official", foreign_keys=[seconder_id])

    __table_args__ = (
        Index("ix_bill_actions_bill_id", "bill_id"),
    )

    def __repr__(self) -> str:
        return f"<BillAction(id={self.id}, bill_id={self.bill_id}, action={self.action_text})>"
