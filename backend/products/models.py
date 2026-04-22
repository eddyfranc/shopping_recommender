from django.db import models
from django.utils import timezone


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    price = models.FloatField()
    image = models.URLField(max_length=500, blank=True)
    rating = models.FloatField(default=4.5)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Interaction(models.Model):
    ACTION_CHOICES = [
        ("view", "View"),
        ("click", "Click"),
        ("purchase", "Purchase"),
    ]

    user_id = models.IntegerField(db_index=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="interactions"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User {self.user_id} - {self.product.name} ({self.action})"


class InteractionLog(models.Model):
    ACTION_CHOICES = [
        ("search", "Search"),
        ("product_view", "Product View"),
    ]

    session_key = models.CharField(max_length=64, db_index=True)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    query = models.CharField(max_length=500, blank=True)
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="interaction_logs"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.session_key} - {self.action}"


class CartItem(models.Model):
    session_key = models.CharField(max_length=64, db_index=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items"
    )
    quantity = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session_key", "product"],
                name="unique_cart_session_product"
            ),
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class WishlistItem(models.Model):
    session_key = models.CharField(max_length=64, db_index=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session_key", "product"],
                name="unique_wishlist_session_product"
            ),
        ]

    def __str__(self):
        return self.product.name