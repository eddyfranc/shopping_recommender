from django.contrib import admin
from .models import CartItem, Interaction, InteractionLog, Product, WishlistItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "rating", "view_count", "created_at")
    search_fields = ("name", "category", "description")
    list_filter = ("category", "rating")


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    pass


@admin.register(InteractionLog)
class InteractionLogAdmin(admin.ModelAdmin):
    list_display = ("session_key", "action", "query", "product", "created_at")
    list_filter = ("action",)
    search_fields = ("session_key", "query")
    readonly_fields = ("created_at",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "quantity", "created_at")
    search_fields = ("product__name",)


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "created_at")
    search_fields = ("product__name",)