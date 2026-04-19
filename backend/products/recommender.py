import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Product

def get_recommendations(query):
    products = Product.objects.all()
    df = pd.DataFrame(list(products.values()))

    if df.empty:
        return []

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['description'])

    similarity = cosine_similarity(tfidf_matrix)

    index = 0  # simple fallback
    scores = list(enumerate(similarity[index]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    recommended = [df.iloc[i[0]].to_dict() for i in scores[1:6]]
    return recommended