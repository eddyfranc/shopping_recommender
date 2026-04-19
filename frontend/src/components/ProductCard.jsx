import { useState } from "react";
import { Link } from "react-router-dom";
import { cartAdd, trackProductView } from "../api";
import { useApp } from "../context/useApp";

const PLACEHOLDER =
  "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&q=80&auto=format&fit=crop";

const ENGINE_META = {
  hybrid: {
    label: "Hybrid",
    cls: "bg-violet-500/20 text-violet-300 ring-1 ring-violet-500/30",
    dot: "bg-violet-400",
  },
  collaborative: {
    label: "Collab",
    cls: "bg-sky-500/20 text-sky-300 ring-1 ring-sky-500/30",
    dot: "bg-sky-400",
  },
  content: {
    label: "Content",
    cls: "bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/30",
    dot: "bg-amber-400",
  },
};

function StarRating({ rating }) {
  const stars = Math.round(rating * 2) / 2;
  return (
    <div className="flex items-center gap-0.5" aria-label={`Rating: ${rating}`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <svg
          key={n}
          className={`h-3 w-3 ${n <= stars ? "text-amber-400" : "text-white/15"}`}
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
        </svg>
      ))}
      <span className="ml-1 text-[10px] text-white/40">{Number(rating).toFixed(1)}</span>
    </div>
  );
}

function EngineBadge({ rec }) {
  const [open, setOpen] = useState(false);
  const meta = ENGINE_META[rec?.engine] ?? ENGINE_META.content;

  return (
    <div className="relative">
      <button
        type="button"
        aria-label={`Recommended by ${rec?.engine} engine`}
        onClick={(e) => { e.preventDefault(); e.stopPropagation(); setOpen((v) => !v); }}
        onBlur={() => setOpen(false)}
        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wide transition hover:opacity-80 ${meta.cls}`}
      >
        <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
        {meta.label}
      </button>

      {open && rec?.explanation && (
        <div
          role="tooltip"
          className="absolute bottom-full left-0 z-50 mb-2 w-52 rounded-xl border border-white/10 bg-[#1a1a24] p-3 text-[11px] leading-relaxed text-slate-300 shadow-2xl"
        >
          <p>{rec.explanation}</p>
          {rec.cf_score > 0 && (
            <div className="mt-2 flex gap-2 text-[10px] text-white/30">
              <span>CF {(rec.cf_score * 100).toFixed(0)}%</span>
              <span>·</span>
              <span>Content {(rec.content_score * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ProductCard({ product, compact = false }) {
  const { sessionId, refreshCart } = useApp();
  const [img, setImg] = useState(product.image?.trim() ? product.image : PLACEHOLDER);
  const [busy, setBusy] = useState(false);
  const [added, setAdded] = useState(false);

  const rec = product._rec ?? null;
  const id = product.id;
  const numericId = typeof id === "number" ? id : Number(id);
  const canApi = Number.isFinite(numericId) && numericId > 0;

  const price =
    typeof product.price === "number" ? product.price.toFixed(2) : product.price ?? "—";

  const onOpen = () => {
    if (!canApi || !sessionId) return;
    trackProductView(sessionId, numericId).catch(() => {});
  };

  const onAddCart = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!canApi || !sessionId) return;
    setBusy(true);
    try {
      await cartAdd(sessionId, numericId, 1);
      await refreshCart();
      setAdded(true);
      setTimeout(() => setAdded(false), 1800);
    } finally {
      setBusy(false);
    }
  };

  return (
    <article
      className={`group glass-card gradient-border flex flex-col overflow-hidden rounded-2xl transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-violet-500/10 ${
        compact ? "max-w-[11rem]" : ""
      }`}
    >
      <Link
        to={canApi ? `/product/${numericId}` : "#"}
        onClick={onOpen}
        className="block overflow-hidden focus:outline-none"
      >
        <div className="aspect-square w-full overflow-hidden bg-white/5">
          <img
            src={img}
            alt={product.name}
            loading="lazy"
            onError={() => setImg(PLACEHOLDER)}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        </div>
      </Link>

      <div className={`flex flex-1 flex-col ${compact ? "p-2.5" : "p-4"}`}>
        {rec && (
          <div className="mb-2">
            <EngineBadge rec={rec} />
          </div>
        )}

        <Link to={canApi ? `/product/${numericId}` : "#"} onClick={onOpen}>
          <h3
            className={`line-clamp-2 font-medium leading-snug text-white/90 transition-colors group-hover:text-violet-300 ${
              compact ? "text-xs" : "text-sm"
            }`}
          >
            {product.name}
          </h3>
        </Link>

        {product.rating != null && (
          <div className="mt-1.5">
            <StarRating rating={product.rating} />
          </div>
        )}

        <p className={`mt-1.5 font-bold tabular-nums text-emerald-400 ${compact ? "text-sm" : "text-base"}`}>
          ${price}
        </p>

        {canApi ? (
          <button
            type="button"
            disabled={busy}
            onClick={onAddCart}
            className={`mt-3 w-full rounded-xl py-2 text-xs font-semibold transition-all duration-200 ${
              added
                ? "bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/30"
                : "bg-violet-600 text-white hover:bg-violet-500 active:scale-95 disabled:opacity-40"
            }`}
          >
            {added ? "✓ Added" : busy ? "…" : "Add to cart"}
          </button>
        ) : null}
      </div>
    </article>
  );
}
