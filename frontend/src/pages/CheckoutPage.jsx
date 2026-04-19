import { useCallback, useEffect, useState, startTransition } from "react";
import { Link } from "react-router-dom";
import { cartRemove, checkout, fetchCart } from "../api";
import { useApp } from "../context/useApp";

export default function CheckoutPage() {
  const { sessionId, refreshCart } = useApp();
  const [data, setData] = useState(null);
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const d = await fetchCart(sessionId);
      setData(d);
    } catch {
      setData({ items: [], subtotal: 0, count: 0 });
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    startTransition(() => {
      void load();
    });
  }, [load]);

  const onRemove = async (productId) => {
    await cartRemove(sessionId, productId);
    await load();
    await refreshCart();
  };

  const onCheckout = async () => {
    try {
      const r = await checkout(sessionId);
      setMsg(r.message || "Order placed.");
      await load();
      await refreshCart();
    } catch {
      setMsg("Something went wrong.");
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[30vh] items-center justify-center text-sm text-slate-500">Loading…</div>
    );
  }

  return (
    <div className="mx-auto max-w-md px-4 py-10 sm:px-6">
      <Link to="/" className="text-sm font-medium text-blue-600 hover:underline">
        ← Continue shopping
      </Link>
      <h1 className="mt-6 text-xl font-semibold text-slate-900">Your cart</h1>

      {msg ? (
        <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-900 ring-1 ring-emerald-200/80">
          {msg}
        </p>
      ) : null}

      <ul className="mt-6 divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white shadow-sm">
        {(data?.items ?? []).length === 0 ? (
          <li className="px-4 py-12 text-center text-sm text-slate-500">Your cart is empty.</li>
        ) : (
          data.items.map((line) => (
            <li key={line.product.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-4 text-sm">
              <span className="font-medium text-slate-900">{line.product.name}</span>
              <span className="tabular-nums text-slate-600">
                ×{line.quantity} · ${line.line_total}
              </span>
              <button
                type="button"
                className="text-xs text-red-600 hover:underline"
                onClick={() => onRemove(line.product.id)}
              >
                Remove
              </button>
            </li>
          ))
        )}
      </ul>

      {(data?.items ?? []).length > 0 ? (
        <>
          <p className="mt-6 text-right text-base font-semibold text-slate-900">
            Total ${Number(data.subtotal).toFixed(2)}
          </p>
          <button
            type="button"
            onClick={onCheckout}
            className="mt-4 w-full rounded-xl bg-blue-600 py-3.5 text-sm font-semibold text-white shadow-md transition hover:bg-blue-700"
          >
            Checkout
          </button>
        </>
      ) : null}
    </div>
  );
}
