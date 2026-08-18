"""
Smoke test: proves the connector interface + fake fixtures work,
and that tenant filtering behaves correctly.

Run with: python -m tests.test_connector   (from project root)
"""

from connector.fake_connector import FakeConnector


def main():
    connector = FakeConnector()

    print("=== fetch_all() — everything ===")
    all_items = connector.fetch_all()
    for item in all_items:
        print(f"  [{item.tenant_id}] {item.course_name} / {item.lesson_title}")
    print(f"  total: {len(all_items)}\n")

    print("=== fetch_all(tenant_id='harare-high-01') ===")
    harare_items = connector.fetch_all(tenant_id="harare-high-01")
    for item in harare_items:
        print(f"  [{item.tenant_id}] {item.lesson_title}")
    assert all(i.tenant_id == "harare-high-01" for i in harare_items), "Tenant leak!"
    print(f"  total: {len(harare_items)} — all correctly scoped to harare-high-01\n")

    print("=== fetch_course('bulawayo-college-02', 'bio201') ===")
    bio_items = connector.fetch_course("bulawayo-college-02", "bio201")
    for item in bio_items:
        print(f"  {item.lesson_title}: {item.text[:60]}...")
    print(f"  total: {len(bio_items)}\n")

    print("All checks passed.")


if __name__ == "__main__":
    main()
