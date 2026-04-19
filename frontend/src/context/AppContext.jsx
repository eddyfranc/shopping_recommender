import { useCallback, useEffect, useMemo, startTransition, useState } from "react";
import { fetchCart } from "../api";
import { getOrCreateSessionId } from "../session";
import { AppContext } from "./contextCore";

export function AppProvider({ children }) {
  const sessionId = useMemo(() => getOrCreateSessionId(), []);
  const [cartCount, setCartCount] = useState(0);

  const refreshCart = useCallback(async () => {
    try {
      const d = await fetchCart(sessionId);
      setCartCount(d.count ?? 0);
    } catch {
      setCartCount(0);
    }
  }, [sessionId]);

  useEffect(() => {
    startTransition(() => {
      void refreshCart();
    });
  }, [refreshCart]);

  const value = useMemo(
    () => ({ sessionId, cartCount, refreshCart, setCartCount }),
    [sessionId, cartCount, refreshCart]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
