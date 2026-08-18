"""
Smoke test: run the chunker over the fake fixture content and inspect
the chunks it produces.

Run with: python -m tests.test_chunker   (from project root)
"""

from connector.fake_connector import FakeConnector
from pipeline.chunker import chunk_content_item


def main():
    connector = FakeConnector()
    items = connector.fetch_all()

    total_chunks = 0
    for item in items:
        chunks = chunk_content_item(item)
        total_chunks += len(chunks)
        print(f"\n=== {item.lesson_title} ({item.tenant_id}) — {len(chunks)} chunk(s) ===")
        for c in chunks:
            print(f"  [{c.chunk_id}] ({c.char_count} chars): {c.text[:90]}...")
            # Verify tenant_id is preserved through chunking.
            assert c.tenant_id == item.tenant_id

    print(f"\nTotal chunks produced: {total_chunks}")
    print("All chunks correctly tagged with source tenant_id.")


if __name__ == "__main__":
    main()
