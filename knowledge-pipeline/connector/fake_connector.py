"""
Fixture-backed connector implementation.

Returns data conforming to the CourseContentConnector interface using
static fixture data in place of a live content source. Allows
downstream pipeline stages (chunking, embedding, storage, search) to
be developed and tested independently of external API availability.
"""

from connector.base import CourseContentConnector
from schemas.models import RawContentItem
from fixtures.sample_courses import FAKE_COURSE_DATA


class FakeConnector(CourseContentConnector):
    def __init__(self, simulated_latency: bool = False):
        self._data = FAKE_COURSE_DATA
        self._simulated_latency = simulated_latency

    def fetch_all(self, tenant_id: str | None = None) -> list[RawContentItem]:
        if tenant_id is None:
            return list(self._data)
        return [item for item in self._data if item.tenant_id == tenant_id]

    def fetch_course(self, tenant_id: str, course_id: str) -> list[RawContentItem]:
        return [
            item for item in self._data
            if item.tenant_id == tenant_id and item.course_id == course_id
        ]
