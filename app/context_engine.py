"""
Context engine.

For a given student question, assembles exactly what the Tutor agent
needs: relevant course content (retrieved here) plus recent conversation
history (so the tutor has short-term memory).

RETRIEVAL NOTE: this uses TF-IDF (keyword-overlap) similarity, not
embeddings + pgvector. It's a real, working retrieval mechanism - just
simpler than production RAG. It works well when course content uses
similar vocabulary to student questions (which is common - students
usually ask about a "polymorphism" using the word "polymorphism").
It will miss purely semantic matches (question and content share no
words but mean the same thing). Swap this file for an embeddings-based
version once that limitation actually shows up in testing - nothing
else in the app needs to change.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.db import get_course_content, get_conversation_history


def retrieve_relevant_content(tenant_id: str, course_id: str, question: str, top_k: int = 3):
    """Returns the top_k most relevant course content chunks for this question."""
    chunks = get_course_content(tenant_id, course_id)

    if not chunks:
        return []

    texts = [c["chunk_text"] for c in chunks]

    # TF-IDF needs at least 2 documents to compute meaningful similarity.
    # With only 1 chunk stored, just return it - there's nothing to rank against.
    if len(texts) == 1:
        return chunks

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(texts + [question])

    question_vector = matrix[-1]
    content_vectors = matrix[:-1]

    similarities = cosine_similarity(question_vector, content_vectors)[0]

    ranked = sorted(zip(chunks, similarities), key=lambda pair: pair[1], reverse=True)
    top_chunks = [chunk for chunk, score in ranked[:top_k] if score > 0]

    return top_chunks


def build_context(tenant_id: str, student_id: str, course_id: str, question: str) -> dict:
    """
    Assembles everything the Tutor agent needs for this turn.
    This is the single function the rest of the app calls - if retrieval
    logic changes later, only this file and context_engine.py need updating.
    """
    relevant_chunks = retrieve_relevant_content(tenant_id, course_id, question)
    history = get_conversation_history(tenant_id, student_id, course_id)

    return {
        "relevant_content": [c["chunk_text"] for c in relevant_chunks],
        "content_titles": [c["title"] for c in relevant_chunks],
        "recent_history": history,
    }
