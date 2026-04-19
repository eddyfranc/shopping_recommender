from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="image",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="product",
            name="rating",
            field=models.FloatField(default=4.5),
        ),
    ]
