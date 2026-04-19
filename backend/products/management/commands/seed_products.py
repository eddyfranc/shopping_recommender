from django.core.management.base import BaseCommand

from products.models import Product

# Curated sample catalog — Unsplash images (stable query params)
SEED = [
    {
        "name": "iPhone 15 Pro",
        "category": "Phones",
        "description": "Titanium design, A17 Pro chip, advanced camera system for photos and video.",
        "price": 999.0,
        "rating": 4.8,
        "image": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=800&q=80&auto=format&fit=crop",
        "view_count": 120,
    },
    {
        "name": "Samsung Galaxy S24 Ultra",
        "category": "Phones",
        "description": "Large AMOLED display, S Pen, flagship Android performance and long battery life.",
        "price": 1199.0,
        "rating": 4.7,
        "image": "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=800&q=80&auto=format&fit=crop",
        "view_count": 95,
    },
    {
        "name": "Google Pixel 8",
        "category": "Phones",
        "description": "Pure Android experience with excellent computational photography and AI features.",
        "price": 699.0,
        "rating": 4.6,
        "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800&q=80&auto=format&fit=crop",
        "view_count": 78,
    },
    {
        "name": "MacBook Air 15\" M3",
        "category": "Laptops",
        "description": "Thin and light laptop with Apple M3 chip, silent fanless design, all-day battery.",
        "price": 1299.0,
        "rating": 4.9,
        "image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80&auto=format&fit=crop",
        "view_count": 200,
    },
    {
        "name": "Dell XPS 15",
        "category": "Laptops",
        "description": "15-inch OLED option, Intel Core Ultra, ideal for creative and developer workloads.",
        "price": 1599.0,
        "rating": 4.5,
        "image": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800&q=80&auto=format&fit=crop",
        "view_count": 88,
    },
    {
        "name": "Lenovo ThinkPad X1",
        "category": "Laptops",
        "description": "Business-class keyboard and durability, lightweight carbon build, great for travel.",
        "price": 1399.0,
        "rating": 4.6,
        "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80&auto=format&fit=crop",
        "view_count": 64,
    },
    {
        "name": "Wireless Noise-Cancelling Headphones",
        "category": "Accessories",
        "description": "Over-ear comfort, active noise cancellation, 30+ hours playback, USB-C charging.",
        "price": 249.0,
        "rating": 4.5,
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80&auto=format&fit=crop",
        "view_count": 150,
    },
    {
        "name": "Mechanical Keyboard RGB",
        "category": "Accessories",
        "description": "Tactile switches, per-key RGB, aluminum frame, includes wrist rest.",
        "price": 129.0,
        "rating": 4.4,
        "image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&q=80&auto=format&fit=crop",
        "view_count": 72,
    },
    {
        "name": "USB-C Hub 7-in-1",
        "category": "Accessories",
        "description": "HDMI 4K, SD/microSD, USB-A ports, pass-through charging for laptops and tablets.",
        "price": 49.0,
        "rating": 4.3,
        "image": "https://images.unsplash.com/photo-1625948515291-69613efd103f?w=800&q=80&auto=format&fit=crop",
        "view_count": 110,
    },
    {
        "name": "Smart Watch Pro",
        "category": "Accessories",
        "description": "Health tracking, GPS, swim-proof, notifications, multi-day battery in smart mode.",
        "price": 299.0,
        "rating": 4.5,
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80&auto=format&fit=crop",
        "view_count": 134,
    },
    {
        "name": "Portable SSD 1TB",
        "category": "Accessories",
        "description": "USB 3.2 Gen 2 speeds, compact metal enclosure, works with PC and Mac.",
        "price": 99.0,
        "rating": 4.6,
        "image": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=800&q=80&auto=format&fit=crop",
        "view_count": 56,
    },
    {
        "name": "Webcam 4K",
        "category": "Accessories",
        "description": "Auto light correction, dual mics, privacy shutter, clip mount for monitors.",
        "price": 179.0,
        "rating": 4.2,
        "image": "https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?w=800&q=80&auto=format&fit=crop",
        "view_count": 41,
    },
]


class Command(BaseCommand):
    help = "Create or update sample products for development and demos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing products before seeding (also clears related rows).",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Product.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Removed existing products (and related rows where applicable)."))

        created = 0
        updated = 0
        for row in SEED:
            obj, was_created = Product.objects.update_or_create(
                name=row["name"],
                defaults={
                    "category": row["category"],
                    "description": row["description"],
                    "price": row["price"],
                    "image": row["image"],
                    "rating": row["rating"],
                    "view_count": row.get("view_count", 0),
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {created} created, {updated} updated. Total in DB: {Product.objects.count()}."
            )
        )
