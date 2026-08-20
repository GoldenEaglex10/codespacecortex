"""
Production connector implementation. Requires:
  1. Confirmed API base URL and authentication method
  2. Valid credentials (API key / OAuth token)

Implements the same interface as the fixture-backed connector so it
can be substituted in without changes to any other pipeline stage.

Remaining work:
  - BASE_URL
  - auth headers in _headers()
  - endpoint paths in fetch_all / fetch_course
  - response mapping from the source API's JSON to RawContentItem
"""

import requests  # unused until endpoints below are implemented

from connector.base import CourseContentConnector
from schemas.models import RawContentItem, ContentType


class CodespaceConnector(CourseContentConnector):
    BASE_URL = "https://codespace.example.com/api"  # TODO: replace with actual base URL

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",  # TODO: confirm auth scheme
            "Accept": "application/json",
        }

    def fetch_all(self, tenant_id: str | None = None) -> list[RawContentItem]:
        # TODO: endpoint likely of the form:
        #   GET {BASE_URL}/schools/{tenant_id}/content
        # tenant_id is required in this implementation — there is no
        # cross-tenant fetch, so isolation does not depend on
        # post-fetch filtering.
        if tenant_id is None:
            raise ValueError(
                "tenant_id is required — no cross-tenant fetch is supported."
            )
        raise NotImplementedError("Endpoint not yet implemented.")

    def fetch_course(self, tenant_id: str, course_id: str) -> list[RawContentItem]:
        # TODO: e.g. GET {BASE_URL}/schools/{tenant_id}/courses/{course_id}/lessons
        raise NotImplementedError("Endpoint not yet implemented.")

    @staticmethod
    def _map_response_to_items(tenant_id: str, raw_json: dict) -> list[RawContentItem]:
        """
        TODO: map source API response fields onto RawContentItem.
        Target shape:

        RawContentItem(
            tenant_id=tenant_id,
            course_id=raw_json["course"]["id"],
            course_name=raw_json["course"]["name"],
            lesson_id=raw_json["id"],
            lesson_title=raw_json["title"],
            content_type=ContentType.LESSON,
            text=raw_json["body_text"],
            source_url=raw_json.get("url"),
        )
        """
        raise NotImplementedError
