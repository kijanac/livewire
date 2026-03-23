from abc import ABC, abstractmethod

from sqlalchemy.orm import Session


class BaseIngester(ABC):
    @abstractmethod
    def ingest(self, session: Session) -> tuple[int, int]:
        """Run ingestion and return (added_count, updated_count)."""
        ...
