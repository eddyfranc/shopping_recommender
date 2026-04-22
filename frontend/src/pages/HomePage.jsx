import { useCallback, useEffect, startTransition, useMemo, useState } from "react";
import { searchCatalog } from "../api";
import { ProductCard } from "../components/ProductCard";
import { useApp } from "../context/useApp";

function CardSkeleton() {
  return (
    <div className="max-w-[11rem] overflow-hidden rounded-2xl border border-white/[0.06] bg-white/[0.03]">
      <div className="aspect-square shimmer" />
      <div className="space-y-2 p-2.5">
        <div className="h-3 w-full shimmer rounded-md" />
        <div className="h-3 w-3/4 shimmer rounded-md" />
        <div className="h-4 w-14 shimmer rounded-md" />
        <div className="h-8 w-full shimmer rounded-xl" />
      </div>
    </div>
  );
}

/** Engine breakdown pills */
function EngineBreakdown({ recs }) {
  const counts = useMemo(() => {
    const c = { hybrid: 0, collaborative: 0, content: 0 };
    recs.forEach((p) => {
      const e = p._rec?.engine ?? "content";
      if (e in c) c[e]++;
    });
    return c;
  }, [recs]);

  const pills = [
    { key: "hybrid", label: "Hybrid", cls: "bg-violet-500/15 text-violet-300 ring-1 ring-violet-500/25", dot: "bg-violet-400" },
    { key: "collaborative", label: "Collaborative", cls: "bg-sky-500/15 text-sky-300 ring-1 ring-sky-500/25", dot: "bg-sky-400" },
    { key: "content", label: "Content", cls: "bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/25", dot: "bg-amber-400" },
  ].filter((p) => counts[p.key] > 0);

  if (!pills.length) return null;
  return (
    <div className="mt-2 flex flex-wrap justify-center gap-1.5">
      {pills.map(({ key, label, cls, dot }) => (
        <span key={key} className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${cls}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
          {counts[key]}× {label}
        </span>
      ))}
    </div>
  );
}

const CATEGORIES = ["All", "Phones", "Laptops", "Accessories"];

export default function HomePage() {
  const { sessionId } = useApp();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [products, setProducts] = useState([]);
  const [recommendations, setRecs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasFetched, setHasFetched] = useState(false);

  const runSearch = useCallback(async (overrides = {}) => {
    setError(null);
    setLoading(true);
    const cat = overrides.category ?? category;
    const q = overrides.query ?? query;
    try {
      const params = { query: q, session_id: sessionId };
      if (cat && cat !== "All") params.category = cat;
      const data = await searchCatalog(params);
      setProducts(data.products ?? []);
      setRecs(data.recommendations ?? []);
      setHasFetched(true);
    } catch (e) {
      console.error(e);
      setError("Could not reach the server.");
    } finally {
      setLoading(false);
    }
  }, [sessionId, query, category]);

  useEffect(() => {
    if (!sessionId) return;
    startTransition(() => { void runSearch({}); });
  }, [sessionId]);

  const filterRecs = useMemo(() => {
    if (category === "All") return recommendations;
    return recommendations.filter((p) =>
      p.category?.toLowerCase().includes(category.toLowerCase())
    );
  }, [recommendations, category]);

  return (
    <div className="min-h-screen bg-[#0f0f13] pb-20">
      {/* ── Hero ── */}
      <div className="relative overflow-hidden">
        {/* ambient glow blobs */}
        <div className="pointer-events-none absolute -top-32 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-violet-600/20 blur-[100px]" />
        <div className="pointer-events-none absolute -top-16 left-1/4 h-64 w-64 rounded-full bg-indigo-600/10 blur-[80px]" />

        <div className="relative mx-auto max-w-5xl px-4 pt-16 pb-12 text-center sm:px-6">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-500/25 bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-300">
            <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse" />
            AI-Powered Recommendations
          </div>

          <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl">
            Discover products
            <br />
            <span className="gradient-text">made for you</span>
          </h1>

          {/* Search bar */}
          <div className="mx-auto mt-10 flex max-w-xl items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.06] p-1.5 shadow-xl shadow-black/30 backdrop-blur-md">
            <svg className="ml-2 h-4 w-4 shrink-0 text-white/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runSearch({})}
              placeholder="Search phones, laptops, accessories…"
              className="min-h-10 flex-1 bg-transparent text-sm text-white placeholder-white/25 outline-none"
            />
            <button
              type="button"
              onClick={() => runSearch({})}
              disabled={loading}
              className="shrink-0 rounded-xl bg-violet-600 px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-violet-600/30 transition-all hover:bg-violet-500 active:scale-95 disabled:opacity-50"
            >
              {loading ? (
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
              ) : "Search"}
            </button>
          </div>

          {/* Category pills */}
          <nav className="mt-6 flex flex-wrap justify-center gap-2" aria-label="Category filter">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => { setCategory(cat); runSearch({ category: cat }); }}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-200 ${category === cat
                  ? "bg-violet-600 text-white shadow-lg shadow-violet-600/30"
                  : "border border-white/10 bg-white/[0.05] text-white/60 hover:bg-white/10 hover:text-white"
                  }`}
              >
                {cat}
              </button>
            ))}
          </nav>

          {error && (
            <p className="mt-4 text-sm text-red-400" role="alert">{error}</p>
          )}
        </div>
      </div>

      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        {/* ── Recommendations ── */}
        <section className="mb-16" aria-labelledby="rec-heading">
          <div className="mb-6 flex flex-col items-center gap-1 text-center">
            <div className="flex items-center gap-2">
              <h2 id="rec-heading" className="text-xl font-bold text-white">
                Recommended for you
              </h2>
              <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-violet-500 to-sky-500 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white shadow-lg shadow-violet-500/20">
                ✦ Hybrid AI
              </span>
            </div>

            {!loading && filterRecs.length > 0 && <EngineBreakdown recs={filterRecs} />}
          </div>

          {loading ? (
            <div className="flex flex-wrap justify-center gap-4">
              {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
            </div>
          ) : filterRecs.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] py-14 text-center">
              <div className="text-3xl">✦</div>
              <p className="mt-3 text-sm text-white/40">
                No recommendations yet — try searching or viewing a product
              </p>
            </div>
          ) : (
            <div className="flex flex-wrap justify-center gap-4 sm:gap-5 float-up">
              {filterRecs.map((p) => (
                <ProductCard key={`rec-${p.id}`} product={p} compact />
              ))}
            </div>
          )}
        </section>

        {/* ── Divider ── */}
        <div className="mb-10 flex items-center gap-4">
          <div className="flex-1 border-t border-white/[0.06]" />
          <span className="text-xs font-medium uppercase tracking-widest text-white/25">
            {query.trim() ? "Search results" : "All products"}
          </span>
          <div className="flex-1 border-t border-white/[0.06]" />
        </div>

        {/* ── Products grid ── */}
        <section aria-labelledby="products-heading">
          <h2 id="products-heading" className="sr-only">
            {query.trim() ? "Search results" : "All products"}
          </h2>

          {loading ? (
            <div className="flex flex-wrap justify-center gap-4">
              {Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)}
            </div>
          ) : hasFetched && products.length === 0 ? (
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] py-16 text-center">
              <p className="text-sm text-white/40">No products found. Try a different search.</p>
            </div>
          ) : (
            <div className="flex flex-wrap justify-center gap-4 sm:gap-5 float-up">
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
