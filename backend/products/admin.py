from django.contrib import admin

# Register your models here.
from .models import CartItem, Interaction, InteractionLog, Product, ProductFeedback, WishlistItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "rating", "view_count", "created_at")
    search_fields = ("name", "category", "description")


admin.site.register(Interaction)


@admin.register(InteractionLog)
class InteractionLogAdmin(admin.ModelAdmin):
    list_display = ("session_key", "action", "query", "product", "created_at")
    list_filter = ("action",)
    search_fields = ("session_key", "query")
    readonly_fields = ("created_at",)


admin.site.register(CartItem)
admin.site.register(WishlistItem)
admin.site.register(ProductFeedback)
