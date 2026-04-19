from datetime import timedelta

import pandas as pd
from django.utils import timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import InteractionLog, Product, ProductFeedback

MAX_RECOMMENDATIONS = 6
INTEREST_LOOKBACK_DAYS = 7
MAX_HISTORY_EVENTS = 40


def _row_to_dict(row) -> dict:
    return {
        "id": int(row["id"]),
        "name": str(row["name"]),
        "category": str(row["category"]),
        "description": str(row["description"]),
        "price": float(row["price"]),
        "image": str(row["image"]) if pd.notna(row.get("image")) else "",
        "rating": float(row["rating"]) if pd.notna(row.get("rating")) else 4.5,
    }


def _session_interest_text(session_key: str | None) -> str:
    if not session_key:
        return ""
    since = timezone.now() - timedelta(days=INTEREST_LOOKBACK_DAYS)
    logs = (
        InteractionLog.objects.filter(session_key=session_key, created_at__gte=since)
        .select_related("product")
        .order_by("-created_at")[:MAX_HISTORY_EVENTS]
    )
    parts: list[str] = []
    seen_q: set[str] = set()
    seen_p: set[int] = set()
    for log in logs:
        if log.action == "search" and log.query:
            q = log.query.strip()
            if q and q not in seen_q:
                seen_q.add(q)
                parts.append(q)
        elif log.action == "product_view" and log.product_id and log.product_id not in seen_p:
            seen_p.add(log.product_id)
            p = log.product
            if p:
                desc = (p.description or "")[:160]
                parts.append(f"{p.name} {p.category} {desc}")
    return " ".join(parts)


def _excluded_ids(session_key: str | None) -> set[int]:
    if not session_key:
        return set()
    return set(
        ProductFeedback.objects.filter(
            session_key=session_key,
            feedback_type__in=[
                ProductFeedback.DISLIKE,
                ProductFeedback.NOT_INTERESTED,
            ],
        ).values_list("product_id", flat=True)
    )


def _explain(
    q: str,
    interest: str,
    row_name: str,
    row_desc: str,
    has_query_signal: bool,
    has_history_signal: bool,
) -> tuple[str, list[str]]:
    """Human-readable explanation for dissertation / UI transparency."""
    signals: list[str] = []
    text_blob = f"{row_name} {row_desc}".lower()
    qlow = q.lower().strip() if q else ""

    if qlow and qlow in text_blob:
        signals.append("search_overlap")
    if interest:
        signals.append("session_history")

    if q and interest:
        return (
            "Recommended because your current search and recent browsing overlap with this item (TF‑IDF similarity).",
            signals or ["tfidf"],
        )
    if q:
        return (
            f"Recommended because it is textually similar to your search “{q[:80]}{'…' if len(q) > 80 else ''}”.",
            signals or ["tfidf"],
        )
    if interest:
        return (
            "Recommended based on similarity to your recent searches and viewed products.",
            signals or ["history"],
        )
    return (
        "Suggested from the catalog using content similarity (baseline when little history exists yet).",
        ["fallback"],
    )


def get_recommendations(
    query: str,
    session_key: str | None = None,
    top_k: int = MAX_RECOMMENDATIONS,
) -> list[dict]:
    """
    Content-based TF-IDF; augments query with session interest text.
    Each item includes `_rec`: explanation + signals for UI transparency.
    """
    excluded = _excluded_ids(session_key)

    rows = list(
        Product.objects.all().values(
            "id",
            "name",
            "category",
            "description",
            "price",
            "image",
            "rating",
        )
    )
    if not rows:
        return []

    df = pd.DataFrame(rows)
    if excluded:
        df = df[~df["id"].isin(excluded)]
    if df.empty:
        return []

    df["content"] = (
        df["name"].fillna("").astype(str)
        + " "
        + df["description"].fillna("").astype(str)
        + " "
        + df["category"].fillna("").astype(str)
    )

    interest = _session_interest_text(session_key)
    q = (query or "").strip()
    combined = f"{q} {interest}".strip()

    n = len(df)
    k = min(top_k, n)

    if not combined:
        subset = df.head(k)
        out_list = []
        for i in range(len(subset)):
            row = subset.iloc[i]
            d = _row_to_dict(row)
            exp, sig = _explain("", "", str(row["name"]), str(row["description"]), False, False)
            d["_rec"] = {"explanation": exp, "signals": sig, "engine": "tfidf_content"}
            out_list.append(d)
        return out_list

    try:
        vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
        tfidf_matrix = vectorizer.fit_transform(df["content"])
        query_vec = vectorizer.transform([combined])
    except ValueError:
        subset = df.head(k)
        out_list = []
        for i in range(len(subset)):
            row = subset.iloc[i]
            d = _row_to_dict(row)
            exp, sig = _explain(q, interest, str(row["name"]), str(row["description"]), bool(q), bool(interest))
            d["_rec"] = {"explanation": exp, "signals": sig, "engine": "tfidf_content"}
            out_list.append(d)
        return out_list

    similarity = cosine_similarity(query_vec, tfidf_matrix).flatten()
    idx = similarity.argsort()[-k:][::-1]
    out_list = []
    for pos in idx:
        row = df.iloc[int(pos)]
        d = _row_to_dict(row)
        qlow = q.lower() if q else ""
        blob = f"{row['name']} {row['description']}".lower()
        has_q = bool(qlow and qlow in blob)
        has_hist = bool(interest)
        exp, sig = _explain(q, interest, str(row["name"]), str(row["description"]), has_q, has_hist)
        d["_rec"] = {
            "explanation": exp,
            "signals": sig,
            "engine": "tfidf_content",
            "score": round(float(similarity[int(pos)]), 4),
        }
        out_list.append(d)
    return out_list
