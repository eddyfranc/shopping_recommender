import { useContext } from "react";
import { AppContext } from "./contextCore";

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp outside AppProvider");
  return ctx;
}
