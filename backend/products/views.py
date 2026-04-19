from django.db.models import F, Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    CartItem,
    InteractionLog,
    Product,
    ProductFeedback,
    WishlistItem,
)
from .recommender import get_recommendations
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

MAX_SEARCH_RESULTS = 24


def _session(request_get, request_data=None) -> str:
    data = request_data or {}
    return (request_get.get("session_id") or data.get("session_id") or "").strip()[:64]


def _product_dict(obj: Product, full: bool = True) -> dict:
    d = {
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
    return d


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
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__icontains=query)
        ).distinct()

    order_map = {
        "price_asc": ("price",),
        "price_desc": ("-price",),
        "rating_desc": ("-rating", "-view_count"),
        "newest": ("-created_at",),
        "popularity": ("-view_count", "-rating"),
    }
    if sort in order_map:
        base = base.order_by(*order_map[sort])
    else:
        base = base.order_by("-view_count", "-rating", "id")

    products_qs = base[:MAX_SEARCH_RESULTS]
    products = [_product_dict(p, full=False) for p in products_qs]

    recommendations = get_recommendations(query, session_key=session_key or None)

    if session_key:
        InteractionLog.objects.create(
            session_key=session_key,
            action="search",
            query=query[:500],
        )

    return Response(
        {
            "query": query,
            "session_id": session_key,
            "search_meta": {
                "kind": "keyword_match" if query else "browse",
                "sort": sort or "default",
                "filters": {
                    "category": cat or "All",
                    "price_min": price_min,
                    "price_max": price_max,
                },
            },
            "products": products,
            "recommendations": recommendations,
        }
    )


@api_view(["GET"])
def product_detail(request, pk: int):
    try:
        p = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"detail": "Not found."}, status=404)
    Product.objects.filter(pk=pk).update(view_count=F("view_count") + 1)
    p.refresh_from_db()
    return Response({"product": _product_dict(p, full=True)})


@api_view(["GET"])
def record_product_view(request):
    session_key = _session(request.GET)
    raw_pid = request.GET.get("product_id")
    if not session_key or not raw_pid:
        return Response({"ok": False, "reason": "session_id and product_id required"}, status=400)
    try:
        pid = int(raw_pid)
    except ValueError:
        return Response({"ok": False}, status=400)
    if not Product.objects.filter(id=pid).exists():
        return Response({"ok": False}, status=404)
    InteractionLog.objects.create(session_key=session_key, action="product_view", product_id=pid)
    return Response({"ok": True})


@api_view(["GET"])
def recent_views(request):
    session_key = _session(request.GET)
    if not session_key:
        return Response({"products": []})
    logs = (
        InteractionLog.objects.filter(session_key=session_key, action="product_view", product__isnull=False)
        .select_related("product")
        .order_by("-created_at")[:40]
    )
    seen: list[int] = []
    out: list[dict] = []
    for log in logs:
        pid = log.product_id
        if pid in seen:
            continue
        seen.append(pid)
        out.append(_product_dict(log.product, full=False))
        if len(out) >= 8:
            break
    return Response({"products": out})


@api_view(["GET"])
def search_history(request):
    session_key = _session(request.GET)
    if not session_key:
        return Response({"queries": []})
    rows = (
        InteractionLog.objects.filter(session_key=session_key, action="search")
        .exclude(query__exact="")
        .order_by("-created_at")
        .values_list("query", flat=True)[:40]
    )
    unique: list[str] = []
    for q in rows:
        if q not in unique:
            unique.append(q)
        if len(unique) >= 12:
            break
    return Response({"queries": unique})


@api_view(["GET", "POST"])
def cart_view(request):
    session_key = _session(request.GET, request.data if request.method != "GET" else None)
    if request.method == "GET":
        if not session_key:
            return Response({"items": [], "subtotal": 0.0, "count": 0})
        items = []
        subtotal = 0.0
        for row in CartItem.objects.filter(session_key=session_key).select_related("product"):
            p = row.product
            line = float(p.price) * row.quantity
            subtotal += line
            items.append(
                {
                    "quantity": row.quantity,
                    "line_total": round(line, 2),
                    "product": _product_dict(p, full=False),
                }
            )
        count = sum(i["quantity"] for i in items)
        return Response({"items": items, "subtotal": round(subtotal, 2), "count": count})

    action = (request.data.get("action") or "add").lower()
    session_key = _session({}, request.data)
    if not session_key:
        return Response({"ok": False, "reason": "session_id required"}, status=400)

    if action == "add":
        try:
            pid = int(request.data.get("product_id"))
        except (TypeError, ValueError):
            return Response({"ok": False}, status=400)
        qty = int(request.data.get("quantity") or 1)
        qty = max(1, min(qty, 99))
        if not Product.objects.filter(id=pid).exists():
            return Response({"ok": False}, status=404)
        obj, created = CartItem.objects.get_or_create(
            session_key=session_key, product_id=pid, defaults={"quantity": qty}
        )
        if not created:
            obj.quantity = min(99, obj.quantity + qty)
            obj.save(update_fields=["quantity"])
        return Response({"ok": True})

    if action == "remove":
        try:
            pid = int(request.data.get("product_id"))
        except (TypeError, ValueError):
            return Response({"ok": False}, status=400)
        CartItem.objects.filter(session_key=session_key, product_id=pid).delete()
        return Response({"ok": True})

    if action == "set":
        try:
            pid = int(request.data.get("product_id"))
        except (TypeError, ValueError):
            return Response({"ok": False}, status=400)
        qty = int(request.data.get("quantity") or 1)
        if qty <= 0:
            CartItem.objects.filter(session_key=session_key, product_id=pid).delete()
        else:
            qty = max(1, min(qty, 99))
            obj, created = CartItem.objects.get_or_create(
                session_key=session_key, product_id=pid, defaults={"quantity": qty}
            )
            if not created:
                obj.quantity = qty
                obj.save(update_fields=["quantity"])
        return Response({"ok": True})

    return Response({"ok": False, "reason": "unknown action"}, status=400)


@api_view(["POST"])
def register_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if not username or not password:
        return Response({"ok": False, "reason": "username and password required"}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"ok": False, "reason": "username taken"}, status=400)
    user = User.objects.create_user(username=username, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"ok": True, "token": token.key, "username": user.username})

@api_view(["POST"])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"ok": False, "reason": "invalid credentials"}, status=401)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"ok": True, "token": token.key, "username": user.username})

@api_view(["POST"])
def checkout_sim(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Token "):
        return Response({"ok": False, "reason": "Authentication required to checkout"}, status=401)
    
    token_key = auth_header.split(" ")[1]
    try:
        token = Token.objects.get(key=token_key)
        user = token.user
    except Token.DoesNotExist:
        return Response({"ok": False, "reason": "Invalid token"}, status=401)

    session_key = _session({}, request.data)
    if not session_key:
        return Response({"ok": False, "reason": "session_id required"}, status=400)
    n, _ = CartItem.objects.filter(session_key=session_key).delete()
    return Response({"ok": True, "message": f"Checkout simulated for {user.username} — {n} line(s) cleared (prototype)."})


@api_view(["GET", "POST"])
def wishlist_view(request):
    session_key = _session(request.GET, request.data if request.method == "POST" else None)
    if not session_key:
        if request.method == "GET":
            return Response({"product_ids": [], "products": []})
        return Response({"ok": False}, status=400)

    if request.method == "GET":
        ids = list(
            WishlistItem.objects.filter(session_key=session_key).values_list("product_id", flat=True)
        )
        products = [_product_dict(p, full=False) for p in Product.objects.filter(id__in=ids)]
        return Response({"product_ids": ids, "products": products})

    try:
        pid = int(request.data.get("product_id"))
    except (TypeError, ValueError):
        return Response({"ok": False}, status=400)
    if not Product.objects.filter(id=pid).exists():
        return Response({"ok": False}, status=404)
    qs = WishlistItem.objects.filter(session_key=session_key, product_id=pid)
    if qs.exists():
        qs.delete()
        return Response({"ok": True, "wishlisted": False})
    WishlistItem.objects.create(session_key=session_key, product_id=pid)
    return Response({"ok": True, "wishlisted": True})


@api_view(["POST"])
def feedback_view(request):
    session_key = _session({}, request.data)
    if not session_key:
        return Response({"ok": False}, status=400)
    try:
        pid = int(request.data.get("product_id"))
    except (TypeError, ValueError):
        return Response({"ok": False}, status=400)
    ftype = (request.data.get("feedback_type") or "").strip()
    if ftype not in (
        ProductFeedback.LIKE,
        ProductFeedback.DISLIKE,
        ProductFeedback.NOT_INTERESTED,
        ProductFeedback.RATED,
    ):
        return Response({"ok": False, "reason": "invalid feedback_type"}, status=400)
    rating = request.data.get("rating")
    r_val = None
    if rating is not None:
        try:
            r_val = float(rating)
            r_val = max(1.0, min(5.0, r_val))
        except ValueError:
            r_val = None
    if ftype == ProductFeedback.RATED and r_val is None:
        return Response({"ok": False, "reason": "rating required"}, status=400)

    ProductFeedback.objects.update_or_create(
        session_key=session_key,
        product_id=pid,
        defaults={"feedback_type": ftype, "rating": r_val},
    )
    return Response({"ok": True})
