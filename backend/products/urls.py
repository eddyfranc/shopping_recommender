from django.urls import path

from .views import (cart_view, checkout_sim, product_detail, recent_views, record_product_view, search_history,search_products, wishlist_view,register_view, login_view,
)

urlpatterns = [
    path("search/", search_products),
    path("products/<int:pk>/", product_detail),
    path("session/recent-views/", recent_views),
    path("session/search-history/", search_history),
    path("cart/", cart_view),
    path("cart/checkout/", checkout_sim),
    path("wishlist/", wishlist_view),
    path("interactions/view/", record_product_view),
    path("auth/register/", register_view),
    path("auth/login/", login_view),
]