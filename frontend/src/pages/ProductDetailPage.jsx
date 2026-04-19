import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { cartAdd, fetchProduct, trackProductView } from "../api";
import { useApp } from "../context/useApp";

const PLACEHOLDER = "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=800&q=80&auto=format&fit=crop";

function StarRating({ rating }) {
  return (
    <div className="flex items-center gap-1">
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((n) => (
          <svg key={n} className={`h-4 w-4 ${n <= Math.round(rating) ? "text-amber-400" : "text-white/15"}`} viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        ))}
      </div>
      <span className="text-sm text-white/50">{Number(rating).toFixed(1)}</span>
    </div>
  );
}

export default function ProductDetailPage() {
  const { id } = useParams();
  const { sessionId, refreshCart } = useApp();
  const [product, setProduct] = useState(null);
  const [err, setErr]         = useState(null);
  const [busy, setBusy]       = useState(false);
  const [added, setAdded]     = useState(false);
  const [imgSrc, setImgSrc]   = useState(PLACEHOLDER);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const p = await fetchProduct(id);
        if (!cancelled) {
          setProduct(p);
          setImgSrc(p.image?.trim() ? p.image : PLACEHOLDER);
        }
        if (sessionId && id) trackProductView(sessionId, Number(id)).catch(() => {});
      } catch {
        if (!cancelled) setErr("Product not found.");
      }
    })();
    return () => { cancelled = true; };
  }, [id, sessionId]);

  if (err) return (
    <div className="mx-auto max-w-lg px-4 py-20 text-center">
      <p className="text-red-400">{err}</p>
      <Link to="/" className="mt-4 inline-block text-sm font-medium text-violet-400 hover:underline">← Back to shop</Link>
    </div>
  );

  if (!product) return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/10 border-t-violet-500" />
        <p className="text-sm text-white/30">Loading…</p>
      </div>
    </div>
  );

  const onAdd = async () => {
    setBusy(true);
    try {
      await cartAdd(sessionId, product.id, 1);
      await refreshCart();
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 float-up">
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm font-medium text-white/40 transition hover:text-violet-400">
        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <polyline points="15 18 9 12 15 6" />
        </svg>
        Back to shop
      </Link>

      <div className="mt-8 grid gap-10 sm:grid-cols-2 lg:gap-16">
        {/* Image */}
        <div className="relative overflow-hidden rounded-3xl bg-white/[0.04] ring-1 ring-white/[0.07]">
          <div className="pointer-events-none absolute inset-0 rounded-3xl bg-gradient-to-br from-violet-500/5 to-transparent" />
          <img
            src={imgSrc}
            alt={product.name}
            onError={() => setImgSrc(PLACEHOLDER)}
            className="aspect-square w-full object-cover"
          />
        </div>

        {/* Info */}
        <div className="flex flex-col">
          <span className="inline-block rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs font-medium uppercase tracking-wider text-white/50">
            {product.category}
          </span>

          <h1 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">
            {product.name}
          </h1>

          {product.rating != null && (
            <div className="mt-3">
              <StarRating rating={product.rating} />
            </div>
          )}

          <p className="mt-4 text-4xl font-extrabold tabular-nums text-emerald-400">
            ${Number(product.price).toFixed(2)}
          </p>

          {product.view_count != null && (
            <p className="mt-1 text-xs text-white/25">{product.view_count} views</p>
          )}

          <p className="mt-6 text-sm leading-relaxed text-white/55 whitespace-pre-wrap">
            {product.description}
          </p>

          <button
            type="button"
            disabled={busy}
            onClick={onAdd}
            className={`mt-8 w-full rounded-2xl py-4 text-sm font-bold tracking-wide shadow-xl transition-all duration-200 sm:max-w-xs ${
              added
                ? "bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/30"
                : "bg-violet-600 text-white shadow-violet-600/30 hover:bg-violet-500 active:scale-95 disabled:opacity-40"
            }`}
          >
            {added ? "✓ Added to cart!" : busy ? "Adding…" : "Add to cart"}
          </button>
        </div>
      </div>
    </div>
  );
}
