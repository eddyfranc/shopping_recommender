import axios from "axios";

// export const API_BASE = (import.meta.env.VITE_API_URL ?? "/api").replace(/\/$/, "");
export const API_BASE = "https://shoppingrecommender-production.up.railway.app/api";

export function apiUrl(path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${p}`;
}

export async function searchCatalog(params) {
  const { data } = await axios.get(apiUrl("/search/"), { params });
  return data;
}

export async function fetchProduct(id) {
  const { data } = await axios.get(apiUrl(`/products/${id}/`));
  return data.product;
}

export async function fetchRecentViews(sessionId) {
  const { data } = await axios.get(apiUrl("/session/recent-views/"), {
    params: { session_id: sessionId },
  });
  return data.products ?? [];
}

export async function fetchSearchHistory(sessionId) {
  const { data } = await axios.get(apiUrl("/session/search-history/"), {
    params: { session_id: sessionId },
  });
  return data.queries ?? [];
}

export async function fetchCart(sessionId) {
  const { data } = await axios.get(apiUrl("/cart/"), { params: { session_id: sessionId } });
  return data;
}

export async function cartAdd(sessionId, productId, quantity = 1) {
  await axios.post(apiUrl("/cart/"), {
    action: "add",
    session_id: sessionId,
    product_id: productId,
    quantity,
  });
}

export async function cartRemove(sessionId, productId) {
  await axios.post(apiUrl("/cart/"), {
    action: "remove",
    session_id: sessionId,
    product_id: productId,
  });
}

export async function checkout(sessionId, token) {
  const { data } = await axios.post(apiUrl("/cart/checkout/"), 
    { session_id: sessionId },
    { headers: { Authorization: `Token ${token}` } }
  );
  return data;
}

export async function login(username, password) {
  const { data } = await axios.post(apiUrl("/auth/login/"), { username, password });
  return data;
}

export async function register(username, password) {
  const { data } = await axios.post(apiUrl("/auth/register/"), { username, password });
  return data;
}

export async function toggleWishlist(sessionId, productId) {
  const { data } = await axios.post(apiUrl("/wishlist/"), {
    session_id: sessionId,
    product_id: productId,
  });
  return data;
}

export async function fetchWishlist(sessionId) {
  const { data } = await axios.get(apiUrl("/wishlist/"), { params: { session_id: sessionId } });
  return data;
}

export async function sendFeedback(sessionId, productId, feedbackType, rating = null) {
  const body = {
    session_id: sessionId,
    product_id: productId,
    feedback_type: feedbackType,
  };
  if (rating != null) body.rating = rating;
  await axios.post(apiUrl("/feedback/"), body);
}

export async function trackProductView(sessionId, productId) {
  await axios.get(apiUrl("/interactions/view/"), {
    params: { session_id: sessionId, product_id: productId },
  });
}
