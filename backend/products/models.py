from django.db import models

from django.utils import timezone





class Product(models.Model):

    name = models.CharField(max_length=255)

    category = models.CharField(max_length=100)

    description = models.TextField()

    price = models.FloatField()

    image = models.URLField(max_length=500, blank=True)

    rating = models.FloatField(default=4.5)

    created_at = models.DateTimeField(default=timezone.now)

    view_count = models.PositiveIntegerField(default=0)



    class Meta:

        ordering = ["-created_at"]





class Interaction(models.Model):

    user_id = models.IntegerField()

    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    action = models.CharField(max_length=50)





class InteractionLog(models.Model):

    """Anonymous session events for personalization (search queries and product views)."""



    session_key = models.CharField(max_length=64, db_index=True)

    action = models.CharField(max_length=32)  # search | product_view

    query = models.CharField(max_length=500, blank=True)

    product = models.ForeignKey(

        Product, null=True, blank=True, on_delete=models.CASCADE, related_name="interaction_logs"

    )

    created_at = models.DateTimeField(auto_now_add=True)



    class Meta:

        ordering = ["-created_at"]





class CartItem(models.Model):

    session_key = models.CharField(max_length=64, db_index=True)

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")

    quantity = models.PositiveSmallIntegerField(default=1)



    class Meta:

        constraints = [

            models.UniqueConstraint(fields=["session_key", "product"], name="unique_cart_session_product"),

        ]





class WishlistItem(models.Model):

    session_key = models.CharField(max_length=64, db_index=True)

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlist_items")



    class Meta:

        constraints = [

            models.UniqueConstraint(fields=["session_key", "product"], name="unique_wishlist_session_product"),

        ]





class ProductFeedback(models.Model):

    LIKE = "like"

    DISLIKE = "dislike"

    NOT_INTERESTED = "not_interested"

    RATED = "rated"

    FEEDBACK_TYPES = [

        (LIKE, "like"),

        (DISLIKE, "dislike"),

        (NOT_INTERESTED, "not_interested"),

        (RATED, "rated"),

    ]



    session_key = models.CharField(max_length=64, db_index=True)

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="feedback_entries")

    feedback_type = models.CharField(max_length=24, choices=FEEDBACK_TYPES)

    rating = models.FloatField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)



    class Meta:

        constraints = [

            models.UniqueConstraint(fields=["session_key", "product"], name="unique_feedback_session_product"),

        ]

