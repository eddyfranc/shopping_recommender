from django.db.models import F, Q
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import CartItem, InteractionLog, Product, WishlistItem
from .recommender import get_recommendations

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

MAX_SEARCH_RESULTS = 24


def _session(request_get, request_data=None) -> str:
    data = request_data or {}
    return (request_get.get("session_id") or data.get("session_id") or "").strip()[:64]


def _product_dict(obj: Product, full: bool = True) -> dict:
    return {
        "id": obj.id,
        "name": obj.name,
        "category": obj.category,
        "description": obj.description if full else (obj.description[:280] + ("…" if len(obj.description) > 280 else "")),
        "price": float(obj.price),
        "image": obj.image or "",
        "rating": float(obj.rating),
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "view_count": int(obj.view_count),
    }


# ---------------- SEARCH ----------------
@api_view(["GET"])
def search_products(request):
    query = (request.GET.get("query") or "").strip()
    session_key = _session(request.GET)
    sort = (request.GET.get("sort") or "").strip()
    cat = (request.GET.get("category") or "").strip()
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")

    base = Product.objects.all()

    if price_min not in (None, ""):
        try:
            base = base.filter(price__gte=float(price_min))
        except ValueError:
            pass

    if price_max not in (None, ""):
        try:
            base = base.filter(price__lte=float(price_max))
        except ValueError:
            pass

    if cat and cat.lower() != "all":
        base = base.filter(category__iexact=cat)

    if query:
        base = base.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        ).distinct()

    order_map = {
        "price_asc": ("price",),
        "price_desc": ("-price",),
        "rating_desc": ("-rating", "-view_count"),
        "newest": ("-created_at",),
        "popularity": ("-view_count", "-rating"),
    }

    base = base.order_by(*order_map.get(sort, ("-view_count", "-rating", "id")))

    products = [_product_dict(p, full=False) for p in base[:MAX_SEARCH_RESULTS]]

    recommendations = get_recommendations(query, session_key=session_key or None)

    if session_key:
        InteractionLog.objects.create(
            session_key=session_key,
            action="search",
            query=query[:500],
        )

    return Response({
        "query": query,
        "session_id": session_key,
        "products": products,
        "recommendations": recommendations,
    })


# ---------------- PRODUCT DETAIL ----------------
@api_view(["GET"])
def product_detail(request, pk: int):
    try:
        p = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"detail": "Not found."}, status=404)

    Product.objects.filter(pk=pk).update(view_count=F("view_count") + 1)
    p.refresh_from_db()

    return Response({"product": _product_dict(p, full=True)})


# ---------------- PRODUCT VIEW LOG ----------------
@api_view(["GET"])
def record_product_view(request):
    session_key = _session(request.GET)
    pid = request.GET.get("product_id")

    if not session_key or not pid:
        return Response({"ok": False}, status=400)

    try:
        pid = int(pid)
    except ValueError:
        return Response({"ok": False}, status=400)

    if not Product.objects.filter(id=pid).exists():
        return Response({"ok": False}, status=404)

    InteractionLog.objects.create(
        session_key=session_key,
        action="product_view",
        product_id=pid
    )

    return Response({"ok": True})


# ---------------- RECENT VIEWS ----------------
@api_view(["GET"])
def recent_views(request):
    session_key = _session(request.GET)
    if not session_key:
        return Response({"products": []})

    logs = InteractionLog.objects.filter(
        session_key=session_key,
        action="product_view",
        product__isnull=False
    ).select_related("product").order_by("-created_at")[:40]

    seen = []
    out = []

    for log in logs:
        if log.product_id in seen:
            continue
        seen.append(log.product_id)
        out.append(_product_dict(log.product, full=False))
        if len(out) >= 8:
            break

    return Response({"products": out})


# ---------------- SEARCH HISTORY ----------------
@api_view(["GET"])
def search_history(request):
    session_key = _session(request.GET)
    if not session_key:
        return Response({"queries": []})

    rows = InteractionLog.objects.filter(
        session_key=session_key,
        action="search"
    ).exclude(query="").order_by("-created_at").values_list("query", flat=True)[:40]

    unique = []
    for q in rows:
        if q not in unique:
            unique.append(q)
        if len(unique) >= 12:
            break

    return Response({"queries": unique})


# ---------------- CART ----------------
@api_view(["GET", "POST"])
def cart_view(request):
    session_key = _session(request.GET, request.data if request.method != "GET" else None)

    if request.method == "GET":
        if not session_key:
            return Response({"items": [], "subtotal": 0.0, "count": 0})

        items = []
        subtotal = 0.0

        for row in CartItem.objects.filter(session_key=session_key).select_related("product"):
            line = float(row.product.price) * row.quantity
            subtotal += line
            items.append({
                "quantity": row.quantity,
                "line_total": round(line, 2),
                "product": _product_dict(row.product, full=False),
            })

        return Response({
            "items": items,
            "subtotal": round(subtotal, 2),
            "count": sum(i["quantity"] for i in items),
        })

    action = (request.data.get("action") or "add").lower()
    session_key = _session({}, request.data)

    if not session_key:
        return Response({"ok": False}, status=400)

    if action == "add":
        pid = int(request.data.get("product_id"))
        qty = max(1, min(int(request.data.get("quantity") or 1), 99))

        if not Product.objects.filter(id=pid).exists():
            return Response({"ok": False}, status=404)

        obj, created = CartItem.objects.get_or_create(
            session_key=session_key,
            product_id=pid,
            defaults={"quantity": qty}
        )

        if not created:
            obj.quantity = min(99, obj.quantity + qty)
            obj.save(update_fields=["quantity"])

        return Response({"ok": True})

    if action == "remove":
        pid = int(request.data.get("product_id"))
        CartItem.objects.filter(session_key=session_key, product_id=pid).delete()
        return Response({"ok": True})

    if action == "set":
        pid = int(request.data.get("product_id"))
        qty = int(request.data.get("quantity") or 1)

        if qty <= 0:
            CartItem.objects.filter(session_key=session_key, product_id=pid).delete()
        else:
            obj, created = CartItem.objects.get_or_create(
                session_key=session_key,
                product_id=pid,
                defaults={"quantity": qty}
            )
            if not created:
                obj.quantity = min(99, qty)
                obj.save(update_fields=["quantity"])

        return Response({"ok": True})

    return Response({"ok": False}, status=400)


# ---------------- AUTH ----------------
@api_view(["POST"])
def register_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"ok": False}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"ok": False}, status=400)

    user = User.objects.create_user(username=username, password=password)
    token, _ = Token.objects.get_or_create(user=user)

    return Response({"ok": True, "token": token.key})


@api_view(["POST"])
def login_view(request):
    user = authenticate(
        username=request.data.get("username"),
        password=request.data.get("password")
    )

    if not user:
        return Response({"ok": False}, status=401)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"ok": True, "token": token.key})


# ---------------- CHECKOUT ----------------
@api_view(["POST"])
def checkout_sim(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")

    if not auth.startswith("Token "):
        return Response({"ok": False}, status=401)

    token = auth.split(" ")[1]

    try:
        user = Token.objects.get(key=token).user
    except Token.DoesNotExist:
        return Response({"ok": False}, status=401)

    session_key = _session({}, request.data)
    if not session_key:
        return Response({"ok": False}, status=400)

    deleted, _ = CartItem.objects.filter(session_key=session_key).delete()

    return Response({
        "ok": True,
        "message": f"Checkout complete for {user.username} — {deleted} items cleared"
    })


# ---------------- WISHLIST ----------------
@api_view(["GET", "POST"])
def wishlist_view(request):
    session_key = _session(
        request.GET,
        request.data if request.method == "POST" else None
    )

    if not session_key:
        return Response({"product_ids": [], "products": []})

    if request.method == "GET":
        ids = list(WishlistItem.objects.filter(
            session_key=session_key
        ).values_list("product_id", flat=True))

        products = [_product_dict(p, full=False) for p in Product.objects.filter(id__in=ids)]

        return Response({"product_ids": ids, "products": products})

    pid = int(request.data.get("product_id"))

    if not Product.objects.filter(id=pid).exists():
        return Response({"ok": False}, status=404)

    obj = WishlistItem.objects.filter(session_key=session_key, product_id=pid)

    if obj.exists():
        obj.delete()
        return Response({"ok": True, "wishlisted": False})

    WishlistItem.objects.create(session_key=session_key, product_id=pid)
    return Response({"ok": True, "wishlisted": True})