from datetime import timedelta
import pandas as pd
import numpy as np
from django.utils import timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import InteractionLog, Product

MAX_RECOMMENDATIONS = 3
INTEREST_LOOKBACK_DAYS = 7
MAX_HISTORY_EVENTS = 40


#  POPULARITY 
def _popularity_scores(df: pd.DataFrame) -> np.ndarray:
    ratings = df["rating"].fillna(4.5).astype(float).values
    views = np.log1p(df["view_count"].fillna(0).astype(float).values)

    r_norm = ratings / ratings.max() if ratings.max() > 0 else ratings
    v_norm = views / views.max() if views.max() > 0 else views

    return 0.6 * r_norm + 0.4 * v_norm


#  UTIL 
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


#  USER HISTORY 
def _session_interest_text(session_key: str | None) -> str:
    if not session_key:
        return ""

    since = timezone.now() - timedelta(days=INTEREST_LOOKBACK_DAYS)

    logs = InteractionLog.objects.filter(
        session_key=session_key,
        created_at__gte=since
    ).select_related("product").order_by("-created_at")[:MAX_HISTORY_EVENTS]

    parts = []
    seen_q = set()
    seen_p = set()

    for log in logs:
        if log.action == "search" and log.query:
            q = log.query.strip()
            if q and q not in seen_q:
                seen_q.add(q)
                parts.append(q)

        elif log.action == "product_view" and log.product_id:
            if log.product_id not in seen_p:
                seen_p.add(log.product_id)
                p = log.product
                if p:
                    parts.append(f"{p.name} {p.category} {p.description[:120]}")

    return " ".join(parts)


#  EXCLUSIONS 
def _excluded_ids(session_key: str | None) -> set[int]:
    return set()


#  COLLABORATIVE FILTERING
def _get_collaborative_scores(session_key: str | None, product_ids: list[int]) -> np.ndarray:
    if not session_key:
        return np.zeros(len(product_ids))

    logs = InteractionLog.objects.filter(
        action="product_view",
        product_id__isnull=False
    ).values("session_key", "product_id")

    data = [
        {"user": l["session_key"], "item": l["product_id"], "weight": 1.0}
        for l in logs
    ]

    if not data:
        return np.zeros(len(product_ids))

    df = pd.DataFrame(data)
    df = df.groupby(["user", "item"])["weight"].sum().reset_index()

    if session_key not in df["user"].values:
        return np.zeros(len(product_ids))

    ui = df.pivot(index="user", columns="item", values="weight").fillna(0)

    sim = cosine_similarity(ui.T)
    sim_df = pd.DataFrame(sim, index=ui.columns, columns=ui.columns)

    user_vec = ui.loc[session_key]

    scores = {}
    for item in ui.columns:
        scores[item] = np.dot(sim_df[item], user_vec)

    arr = np.array([scores.get(pid, 0.0) for pid in product_ids])

    if arr.max() > 0:
        arr = arr / arr.max()

    return arr


#  MAIN RECOMMENDER 
def get_recommendations(query: str, session_key: str | None = None, top_k: int = MAX_RECOMMENDATIONS) -> list[dict]:

    rows = list(Product.objects.all().values(
        "id", "name", "category", "description",
        "price", "image", "rating", "view_count"
    ))

    if not rows:
        return []

    df = pd.DataFrame(rows)

    if df.empty:
        return []

    df["content"] = (
        df["name"].fillna("") + " " +
        df["description"].fillna("") + " " +
        df["category"].fillna("")
    )

    interest = _session_interest_text(session_key)
    q = (query or "").strip()
    combined = f"{q} {interest}".strip()

    n = len(df)
    k = min(top_k, n)

    #  CONTENT BASED 
    content_scores = np.zeros(n)

    if combined:
        try:
            tfidf = TfidfVectorizer(stop_words="english")
            matrix = tfidf.fit_transform(df["content"])
            qvec = tfidf.transform([combined])
            content_scores = cosine_similarity(qvec, matrix).flatten()

            if content_scores.max() > 0:
                content_scores = content_scores / content_scores.max()

        except ValueError:
            pass

    #  COLLABORATIVE 
    product_ids = df["id"].tolist()
    cf_scores = _get_collaborative_scores(session_key, product_ids)

    # HYBRID 
    alpha = 0.7 if q else 0.4

    if cf_scores.max() == 0:
        alpha = 1.0

    final = (alpha * content_scores) + ((1 - alpha) * cf_scores)

    # fallback popularity
    if final.max() == 0:
        final = _popularity_scores(df)

    idx = final.argsort()[-k:][::-1]

    results = []

    for i in idx:
        row = df.iloc[int(i)]

        c = content_scores[int(i)]
        cf = cf_scores[int(i)]
        f = final[int(i)]

        results.append({
            **_row_to_dict(row),
            "_rec": {
                "score": round(float(f), 4),
                "content_score": round(float(c), 4),
                "cf_score": round(float(cf), 4),
                "engine": "hybrid" if cf > 0 and c > 0 else "content"
            }
        })

    return results