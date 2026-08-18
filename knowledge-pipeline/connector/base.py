"""
Connector interface.

Defines the contract all connector implementations must satisfy,
whether backed by fixture data or a production content source.

Downstream stages (chunker, embedder, ingestion) depend only on this
interface, which allows connector implementations to be replaced
without changes elsewhere in the pipeline.
"""

from abc import ABC, abstractmethod
from schemas.models import RawContentItem


class CourseContentConnector(ABC):
    """Abstract base class for all connector implementations."""

    @abstractmethod
    def fetch_all(self, tenant_id: str | None = None) -> list[RawContentItem]:
        """
        Fetch available content. If tenant_id is provided, results are
        scoped to that tenant. Production implementations should
        enforce this scope via an authenticated, tenant-scoped API
        call rather than fetching all data and filtering afterward.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_course(self, tenant_id: str, course_id: str) -> list[RawContentItem]:
        """Fetch all content for a specific course within a specific tenant."""
        raise NotImplementedError
