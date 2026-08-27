"""
Smoke test: ingest fake data, then run realistic student questions
against the search, checking both relevance and tenant isolation.

Run with: python -m tests.test_search   (from project root)
"""

from pipeline.ingest import build_default_pipeline, ingest


def run_query(store, embedder, tenant_id: str, question: str, top_k: int = 3):
    query_embedding = embedder.embed([question])[0]
    results = store.search(tenant_id=tenant_id, query_embedding=query_embedding, top_k=top_k)
    print(f"\nQuery: \"{question}\"  (tenant={tenant_id})")
    if not results:
        print("  (no results)")
    for r in results:
        print(f"  score={r.score:.3f}  [{r.lesson_title}]  {r.text[:80]}...")
    return results


def main():
    connector, embedder, store = build_default_pipeline()
    ingest(connector, embedder, store)

    # --- Relevance checks: does the right content come back? ---
    results = run_query(store, embedder, "harare-high-01", "how does a while loop work")
    assert any("loop" in r.lesson_title.lower() for r in results), \
        "Expected a loops-related lesson to come back for a loop question"

    results = run_query(store, embedder, "bulawayo-college-02", "what happens during mitosis")
    assert any("mitosis" in r.lesson_title.lower() for r in results), \
        "Expected the mitosis lesson to come back for a mitosis question"

    # --- Isolation check: does a biology question against the CS school return nothing relevant? ---
    results = run_query(store, embedder, "harare-high-01", "what happens during mitosis")
    assert all("mitosis" not in r.text.lower() for r in results), \
        "harare-high-01 should never see bulawayo-college-02's biology content"

    # --- Hard isolation check: try to search bulawayo content using harare's tenant_id ---
    # This proves filtering happens at the store level, not just "good relevance".
    bio_embedding = embedder.embed(["mitosis cell division"])[0]
    cross_tenant_results = store.search(tenant_id="harare-high-01", query_embedding=bio_embedding, top_k=5)
    for r in cross_tenant_results:
        assert "bio201" not in r.chunk_id, f"LEAK: bulawayo content ({r.chunk_id}) returned for harare-high-01"

    print("\nAll relevance and isolation checks passed.")


if __name__ == "__main__":
    main()
