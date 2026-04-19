import { useCallback, useEffect, startTransition, useMemo, useState } from "react";
import { searchCatalog } from "../api";
import { ProductCard } from "../components/ProductCard";
import { useApp } from "../context/useApp";

function CardSkeleton() {
  return (
    <div className="max-w-[11rem] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="aspect-square animate-pulse bg-slate-200" />
      <div className="space-y-2 p-2.5">
        <div className="h-3 w-full animate-pulse rounded bg-slate-200" />
        <div className="h-4 w-14 animate-pulse rounded bg-slate-100" />
        <div className="h-8 w-full animate-pulse rounded bg-slate-100" />
      </div>
    </div>
  );
}

export default function HomePage() {
  const { sessionId } = useApp();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");

  const [products, setProducts] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasFetched, setHasFetched] = useState(false);

  const categories = ["All", "Phones", "Laptops", "Accessories"];

  const runSearch = useCallback(
    async (overrides = {}) => {
      setError(null);
      setLoading(true);
      const cat = overrides.category ?? category;
      const q = overrides.query ?? query;
      try {
        const params = { query: q, session_id: sessionId };
        if (cat && cat !== "All") params.category = cat;
        const data = await searchCatalog(params);
        setProducts(data.products ?? []);
        setRecommendations(data.recommendations ?? []);
        setHasFetched(true);
      } catch (e) {
        console.error(e);
        setError("Could not reach the server.");
      } finally {
        setLoading(false);
      }
    },
    [sessionId, query, category]
  );

  useEffect(() => {
    if (!sessionId) return;
    startTransition(() => {
      void runSearch({});
    });

  }, [sessionId]);

  const filterRecs = useMemo(() => {
    if (category === "All") return recommendations;
    return recommendations.filter((p) =>
      p.category?.toLowerCase().includes(category.toLowerCase())
    );
  }, [recommendations, category]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100/80 pb-16">
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <header className="text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Shop
          </h1>
          <p className="mt-2 text-sm text-slate-600">Search the catalog.</p>

          <div className="mx-auto mt-8 flex max-w-lg flex-col gap-3 sm:flex-row sm:items-center">
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runSearch({})}
              placeholder="What are you looking for?"
              className="min-h-11 w-full flex-1 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-sm outline-none ring-slate-200/80 transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
            <button
              type="button"
              onClick={() => runSearch({})}
              disabled={loading}
              className="min-h-11 shrink-0 rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "…" : "Search"}
            </button>
          </div>

          <nav className="mt-6 flex flex-wrap justify-center gap-2" aria-label="Category">
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => {
                  setCategory(cat);
                  runSearch({ category: cat });
                }}
                className={`rounded-full px-4 py-2 text-sm font-medium transition ${category === cat
                    ? "bg-blue-600 text-white shadow-md shadow-blue-600/25"
                    : "bg-white text-slate-700 shadow-sm ring-1 ring-slate-200/80 hover:bg-slate-50"
                  }`}
              >
                {cat}
              </button>
            ))}
          </nav>

          {error ? (
            <p className="mt-4 text-sm text-red-600" role="alert">
              {error}
            </p>
          ) : null}
        </header>

        <section className="mt-12" aria-labelledby="rec">
          <div className="mb-4 text-center">
            <h2 id="rec" className="text-lg font-semibold text-slate-900">
              Recommended for you
            </h2>
            <p className="text-xs text-slate-500">Picks tailored to your searches and browsing</p>
          </div>
          {loading ? (
            <div className="flex flex-wrap justify-center gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <CardSkeleton key={i} />
              ))}
            </div>
          ) : filterRecs.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-200 bg-white/80 py-10 text-center text-sm text-slate-500">
              No recommendations yet. Try a search or open a product.
            </p>
          ) : (
            <div className="flex flex-wrap justify-center gap-4 sm:gap-5">
              {filterRecs.map((p) => (
                <ProductCard key={`rec-${p.id}`} product={p} compact />
              ))}
            </div>
          )}
        </section>

        <section className="mt-14" aria-labelledby="results">
          <div className="mb-4 text-center">
            <h2 id="results" className="text-lg font-semibold text-slate-900">
              {query.trim() ? "Search results" : "Products"}
            </h2>
          </div>
          {loading ? (
            <div className="flex flex-wrap justify-center gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <CardSkeleton key={i} />
              ))}
            </div>
          ) : hasFetched && products.length === 0 ? (
            <p className="rounded-xl border border-slate-200 bg-white py-12 text-center text-sm text-slate-600 shadow-sm">
              No products found.
            </p>
          ) : (
            <div className="flex flex-wrap justify-center gap-4 sm:gap-5">
              {products.map((p) => (
                <ProductCard key={p.id} product={p} compact />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
