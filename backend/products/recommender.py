from datetime import timedelta
import pandas as pd
import numpy as np
from django.utils import timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import InteractionLog, Product, ProductFeedback

MAX_RECOMMENDATIONS = 3
INTEREST_LOOKBACK_DAYS = 7
MAX_HISTORY_EVENTS = 40


def _popularity_scores(df: pd.DataFrame) -> np.ndarray:
    """Fallback ranking: blends normalised rating and log(view_count+1)."""
    ratings = df["rating"].fillna(4.5).astype(float).values
    views = np.log1p(df.get("view_count", pd.Series(0, index=df.index)).fillna(0).astype(float).values)
    r_norm = ratings / ratings.max() if ratings.max() > 0 else ratings
    v_norm = views / views.max() if views.max() > 0 else views
    return 0.6 * r_norm + 0.4 * v_norm


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


def _get_collaborative_scores(session_key: str | None, product_ids: list[int]) -> np.ndarray:
    """
    Item-Item Collaborative Filtering using interaction matrix.
    Returns an array of scores aligned with product_ids.
    """
    n_products = len(product_ids)
    if not session_key:
        return np.zeros(n_products)

    # 1. Fetch interactions for matrix
    # We will use product views as implicit feedback
    logs = InteractionLog.objects.filter(action="product_view", product_id__isnull=False).values("session_key", "product_id")
    feedbacks = ProductFeedback.objects.filter(
        feedback_type__in=[ProductFeedback.LIKE, ProductFeedback.RATED]
    ).values("session_key", "product_id", "rating")

    data = []
    for log in logs:
        data.append({"user": log["session_key"], "item": log["product_id"], "weight": 1.0})
    for fb in feedbacks:
        w = 3.0 # Strong explicit signal
        if fb.get("rating") is not None and fb["rating"] < 3.0:
            continue # Ignore negative ratings here, they are excluded anyway
        data.append({"user": fb["session_key"], "item": fb["product_id"], "weight": w})

    if not data:
        return np.zeros(n_products)

    df_interactions = pd.DataFrame(data)
    # Aggregate weights for duplicate user-item pairs
    df_interactions = df_interactions.groupby(["user", "item"])["weight"].sum().reset_index()

    if session_key not in df_interactions["user"].values:
        # Cold start for this user in CF
        return np.zeros(n_products)

    # Build User-Item Matrix
    ui_matrix = df_interactions.pivot(index="user", columns="item", values="weight").fillna(0)
    
    # Calculate Item-Item Similarity (Cosine)
    item_sim = cosine_similarity(ui_matrix.T)
    item_sim_df = pd.DataFrame(item_sim, index=ui_matrix.columns, columns=ui_matrix.columns)

    # Get the user's interaction vector
    user_vector = ui_matrix.loc[session_key]

    # Predict scores: dot product of user vector and item similarities
    # CF Score for Item i = Sum(User_Weight_j * Similarity(i, j))
    cf_scores = {}
    for item in ui_matrix.columns:
        score = np.dot(item_sim_df[item], user_vector)
        cf_scores[item] = score

    # Map scores back to the ordered product_ids list
    scores = np.array([cf_scores.get(pid, 0.0) for pid in product_ids])
    
    # Normalize scores between 0 and 1
    if scores.max() > 0:
        scores = scores / scores.max()
        
    return scores


def _explain(
    q: str,
    interest: str,
    row_name: str,
    row_desc: str,
    has_query_signal: bool,
    has_history_signal: bool,
    cf_weight: float,
) -> tuple[str, list[str]]:
    """Human-readable explanation for Hybrid transparency."""
    signals: list[str] = []
    text_blob = f"{row_name} {row_desc}".lower()
    qlow = q.lower().strip() if q else ""

    if qlow and qlow in text_blob:
        signals.append("search_overlap")
    if interest:
        signals.append("session_history")
    if cf_weight > 0.3:
        signals.append("collaborative")

    if "collaborative" in signals and "search_overlap" in signals:
        return (
            "Recommended because it matches your search and is popular among users with similar tastes.",
            signals,
        )
    if "collaborative" in signals:
        return (
            "Recommended based on interaction patterns of other shoppers similar to you.",
            signals,
        )
    if q and interest:
        return (
            "Recommended because your current search and recent browsing overlap with this item.",
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
        "Suggested from the catalog using content similarity (baseline).",
        ["fallback"],
    )


def get_recommendations(
    query: str,
    session_key: str | None = None,
    top_k: int = MAX_RECOMMENDATIONS,
) -> list[dict]:
    """
    Hybrid Recommender: Combines Content-Based (TF-IDF) and Collaborative Filtering.
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
            "view_count",
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

    # --- 1. Content-Based Scores ---
    content_scores = np.zeros(n)
    if combined:
        try:
            vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
            tfidf_matrix = vectorizer.fit_transform(df["content"])
            query_vec = vectorizer.transform([combined])
            content_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
            if content_scores.max() > 0:
                 content_scores = content_scores / content_scores.max()
        except ValueError:
            pass

    # --- 2. Collaborative Filtering Scores ---
    product_ids = df["id"].tolist()
    cf_scores = _get_collaborative_scores(session_key, product_ids)

    # --- 3. Hybrid Blend ---
    # If search query present → lean content; no query → lean CF.
    alpha = 0.7 if q else 0.4

    # Cold-start: CF matrix is empty → pure content
    if cf_scores.max() == 0:
        alpha = 1.0

    final_scores = (alpha * content_scores) + ((1.0 - alpha) * cf_scores)

    # Get top K indices; fall back to popularity when all hybrid scores are 0
    if final_scores.max() == 0:
        pop = _popularity_scores(df)
        idx = pop.argsort()[-k:][::-1]
    else:
        idx = final_scores.argsort()[-k:][::-1]

    out_list = []
    for pos in idx:
        row = df.iloc[int(pos)]
        d = _row_to_dict(row)
        
        c_score = content_scores[int(pos)]
        cf_score = cf_scores[int(pos)]
        f_score = final_scores[int(pos)]
        
        qlow = q.lower() if q else ""
        blob = f"{row['name']} {row['description']}".lower()
        has_q = bool(qlow and qlow in blob)
        has_hist = bool(interest)

        exp, sig = _explain(q, interest, str(row["name"]), str(row["description"]), has_q, has_hist, cf_score)

        # Label engine by which signal dominated
        if alpha == 1.0 and cf_score == 0:
            engine_label = "content"
        elif cf_score > 0 and c_score == 0:
            engine_label = "collaborative"
        elif cf_score > 0 and c_score > 0:
            engine_label = "hybrid"
        else:
            engine_label = "content"

        d["_rec"] = {
            "explanation": exp,
            "signals": sig,
            "engine": engine_label,
            "score": round(float(f_score), 4),
            "content_score": round(float(c_score), 4),
            "cf_score": round(float(cf_score), 4),
        }
        out_list.append(d)
    return out_list
