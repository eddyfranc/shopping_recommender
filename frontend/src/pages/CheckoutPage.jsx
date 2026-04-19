import { useCallback, useEffect, useState, startTransition } from "react";
import { Link } from "react-router-dom";
import { cartRemove, checkout, fetchCart } from "../api";
import { useApp } from "../context/useApp";
import AuthForm from "../components/AuthForm";

export default function CheckoutPage() {
  const { sessionId, refreshCart } = useApp();
  const [data, setData]       = useState(null);
  const [msg, setMsg]         = useState(null);
  const [msgType, setMsgType] = useState("success"); // "success" | "error"
  const [loading, setLoading] = useState(true);
  const [busy, setBusy]       = useState(false);
  const [token, setToken]     = useState(localStorage.getItem("authToken") || null);
  const [username, setUsername] = useState(localStorage.getItem("authUsername") || null);

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
    startTransition(() => { void load(); });
  }, [load]);

  const onRemove = async (productId) => {
    await cartRemove(sessionId, productId);
    await load();
    await refreshCart();
  };

  const onCheckout = async () => {
    if (!token) return;
    setBusy(true);
    try {
      const r = await checkout(sessionId, token);
      setMsg(r.message || "Order placed successfully!");
      setMsgType("success");
      await load();
      await refreshCart();
    } catch (err) {
      if (err.response?.status === 401) {
        setToken(null);
        setUsername(null);
        localStorage.removeItem("authToken");
        localStorage.removeItem("authUsername");
        setMsg("Your session expired. Please log in again.");
      } else {
        setMsg("Something went wrong. Please try again.");
      }
      setMsgType("error");
    } finally {
      setBusy(false);
    }
  };

  const handleAuthSuccess = (newToken, newUsername) => {
    setToken(newToken);
    setUsername(newUsername);
    localStorage.setItem("authToken", newToken);
    localStorage.setItem("authUsername", newUsername);
  };

  if (loading) return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/10 border-t-violet-500" />
        <p className="text-sm text-white/30">Loading cart…</p>
      </div>
    </div>
  );

  const items = data?.items ?? [];
  const hasItems = items.length > 0;

  return (
    <div className="mx-auto max-w-lg px-4 py-10 sm:px-6 float-up">
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm font-medium text-white/40 transition hover:text-violet-400">
        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <polyline points="15 18 9 12 15 6" />
        </svg>
        Continue shopping
      </Link>

      <h1 className="mt-6 text-2xl font-bold text-white">Your cart</h1>

      {msg && (
        <div className={`mt-4 rounded-xl px-4 py-3 text-sm ${
          msgType === "success"
            ? "bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/25"
            : "bg-red-500/15 text-red-300 ring-1 ring-red-500/25"
        }`}>
          {msg}
        </div>
      )}

      {/* Cart items */}
      <div className="mt-6 overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.03]">
        {!hasItems ? (
          <div className="px-4 py-14 text-center">
            <div className="text-4xl">🛒</div>
            <p className="mt-3 text-sm text-white/35">Your cart is empty.</p>
            <Link to="/" className="mt-4 inline-block text-sm font-medium text-violet-400 hover:underline">
              Browse products →
            </Link>
          </div>
        ) : (
          <ul className="divide-y divide-white/[0.05]">
            {items.map((line) => (
              <li key={line.product.id} className="flex items-center gap-3 px-4 py-4">
                <div className="flex-1 min-w-0">
                  <p className="truncate text-sm font-medium text-white/90">{line.product.name}</p>
                  <p className="mt-0.5 text-xs text-white/35">
                    {line.product.category} · qty {line.quantity}
                  </p>
                </div>
                <span className="shrink-0 font-semibold tabular-nums text-emerald-400 text-sm">
                  ${line.line_total}
                </span>
                <button
                  type="button"
                  onClick={() => onRemove(line.product.id)}
                  className="shrink-0 rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs font-medium text-white/40 transition hover:border-red-500/40 hover:bg-red-500/10 hover:text-red-400"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {hasItems && (
        <>
          {/* Subtotal */}
          <div className="mt-5 flex items-center justify-between rounded-xl border border-white/[0.07] bg-white/[0.03] px-5 py-4">
            <span className="text-sm text-white/50">Order total</span>
            <span className="text-xl font-bold tabular-nums text-white">
              ${Number(data.subtotal).toFixed(2)}
            </span>
          </div>

          {/* Auth / checkout */}
          <div className="mt-6">
            {token ? (
              <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6">
                <div className="mb-5 flex items-center justify-between">
                  <div>
                    <p className="text-xs text-white/40">Logged in as</p>
                    <p className="text-sm font-semibold text-white">{username}</p>
                  </div>
                  <button
                    onClick={() => {
                      setToken(null);
                      setUsername(null);
                      localStorage.removeItem("authToken");
                      localStorage.removeItem("authUsername");
                    }}
                    className="text-xs text-white/30 hover:text-white/60 transition hover:underline"
                  >
                    Log out
                  </button>
                </div>
                <button
                  type="button"
                  onClick={onCheckout}
                  disabled={busy}
                  className="w-full rounded-xl bg-violet-600 py-3.5 text-sm font-bold text-white shadow-xl shadow-violet-600/25 transition-all hover:bg-violet-500 active:scale-95 disabled:opacity-50"
                >
                  {busy ? "Processing…" : "Place order"}
                </button>
              </div>
            ) : (
              <AuthForm onAuthSuccess={handleAuthSuccess} />
            )}
          </div>
        </>
      )}
    </div>
  );
}
