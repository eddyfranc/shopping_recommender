import { useState } from "react";
import { Link } from "react-router-dom";
import { cartAdd, trackProductView } from "../api";
import { useApp } from "../context/useApp";

const PLACEHOLDER =
  "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&q=80&auto=format&fit=crop";

export function ProductCard({ product, compact = false }) {
  const { sessionId, refreshCart } = useApp();
  const [img, setImg] = useState(product.image?.trim() ? product.image : PLACEHOLDER);
  const [busy, setBusy] = useState(false);

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
    } finally {
      setBusy(false);
    }
  };

  return (
    <article
      className={`group flex flex-col overflow-hidden rounded-xl border border-slate-200/90 bg-white shadow-sm transition hover:border-slate-300 hover:shadow-md ${
        compact ? "max-w-[11rem]" : ""
      }`}
    >
      <Link
        to={canApi ? `/product/${numericId}` : "#"}
        onClick={onOpen}
        className="block overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/80"
      >
        <div className="aspect-square w-full bg-slate-100">
          <img
            src={img}
            alt={product.name}
            loading="lazy"
            onError={() => setImg(PLACEHOLDER)}
            className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.02]"
          />
        </div>
      </Link>
      <div className={`flex flex-1 flex-col ${compact ? "p-2.5" : "p-3"}`}>
        <Link to={canApi ? `/product/${numericId}` : "#"} onClick={onOpen}>
          <h3
            className={`line-clamp-2 font-medium leading-snug text-slate-900 group-hover:text-blue-700 ${
              compact ? "text-xs" : "text-sm"
            }`}
          >
            {product.name}
          </h3>
        </Link>
        <p
          className={`mt-1.5 font-semibold tabular-nums text-rose-600 ${
            compact ? "text-sm" : "text-base"
          }`}
        >
          ${price}
        </p>
        {canApi ? (
          <button
            type="button"
            disabled={busy}
            onClick={onAddCart}
            className="mt-3 w-full rounded-lg bg-slate-900 py-2 text-xs font-medium text-white transition hover:bg-slate-800 disabled:opacity-50"
          >
            Add to cart
          </button>
        ) : null}
      </div>
    </article>
  );
}
