import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { cartAdd, fetchProduct, trackProductView } from "../api";
import { useApp } from "../context/useApp";

export default function ProductDetailPage() {
  const { id } = useParams();
  const { sessionId, refreshCart } = useApp();
  const [product, setProduct] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const p = await fetchProduct(id);
        if (!cancelled) setProduct(p);
        if (sessionId && id) {
          trackProductView(sessionId, Number(id)).catch(() => {});
        }
      } catch {
        if (!cancelled) setErr("Product not found.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, sessionId]);

  if (err) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-red-600">{err}</p>
        <Link to="/" className="mt-4 inline-block text-sm font-medium text-blue-600 hover:underline">
          Back to shop
        </Link>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <p className="text-sm text-slate-500">Loading…</p>
      </div>
    );
  }

  const onAdd = async () => {
    setBusy(true);
    try {
      await cartAdd(sessionId, product.id, 1);
      await refreshCart();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <Link to="/" className="text-sm font-medium text-blue-600 hover:underline">
        ← Back
      </Link>
      <div className="mt-8 grid gap-8 sm:grid-cols-2 sm:gap-10">
        <div className="overflow-hidden rounded-2xl bg-slate-100 shadow-inner">
          <img
            src={product.image || "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=800"}
            alt={product.name}
            className="aspect-square w-full object-cover"
          />
        </div>
        <div className="flex flex-col">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{product.category}</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">{product.name}</h1>
          <p className="mt-3 text-3xl font-bold tabular-nums text-rose-600">${Number(product.price).toFixed(2)}</p>
          <p className="mt-2 text-sm text-slate-600">
            {product.rating != null ? `${product.rating} ★` : null}
          </p>
          <p className="mt-6 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{product.description}</p>
          <button
            type="button"
            disabled={busy}
            onClick={onAdd}
            className="mt-8 w-full rounded-xl bg-blue-600 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition hover:bg-blue-700 disabled:opacity-50 sm:max-w-xs"
          >
            Add to cart
          </button>
        </div>
      </div>
    </div>
  );
}
