import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_interactionlog"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="product",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddField(
            model_name="product",
            name="created_at",
            field=models.DateTimeField(default=timezone.now),
        ),
        migrations.AddField(
            model_name="product",
            name="view_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(db_index=True, max_length=64)),
                ("quantity", models.PositiveSmallIntegerField(default=1)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cart_items",
                        to="products.product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProductFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(db_index=True, max_length=64)),
                (
                    "feedback_type",
                    models.CharField(
                        choices=[
                            ("like", "like"),
                            ("dislike", "dislike"),
                            ("not_interested", "not_interested"),
                            ("rated", "rated"),
                        ],
                        max_length=24,
                    ),
                ),
                ("rating", models.FloatField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="feedback_entries",
                        to="products.product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WishlistItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(db_index=True, max_length=64)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishlist_items",
                        to="products.product",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(fields=("session_key", "product"), name="unique_cart_session_product"),
        ),
        migrations.AddConstraint(
            model_name="wishlistitem",
            constraint=models.UniqueConstraint(
                fields=("session_key", "product"), name="unique_wishlist_session_product"
            ),
        ),
        migrations.AddConstraint(
            model_name="productfeedback",
            constraint=models.UniqueConstraint(
                fields=("session_key", "product"), name="unique_feedback_session_product"
            ),
        ),
    ]
