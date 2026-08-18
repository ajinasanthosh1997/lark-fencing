import re
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import Category
from catalog.models import Product


class Command(BaseCommand):
    help = "Import the original LARK template catalogue into Product and Category."

    def handle(self, *args, **options):
        script = Path(settings.BASE_DIR.parent, "static", "assets", "js", "main.js").read_text(encoding="utf-8")
        match = re.search(r"const products=\[(.*?)\]\.map\(\(product,index\)", script, re.S)
        if not match:
            self.stderr.write(self.style.ERROR("Could not find the template product catalogue."))
            return

        category_names = {
            "timber": "Timber Fencing",
            "smart": "Smart Fencing",
            "pvc": "PVC Fencing",
            "composite": "Composite Fencing",
            "concrete": "Concrete Fencing",
        }
        categories = {
            key: Category.objects.get_or_create(name=name)[0]
            for key, name in category_names.items()
        }
        pattern = re.compile(
            r"\{name:'(?P<name>[^']+)',category:'(?P<category>[^']+)',file:'(?P<file>[^']+)'"
            r"(?:,price:'(?P<price>[^']+)')?,description:'(?P<description>[^']*)'\}"
        )
        created = updated = 0
        for index, item in enumerate(pattern.finditer(match.group(1)), 1):
            data = item.groupdict()
            price_match = re.search(r"\d+(?:\.\d+)?", data["price"] or "")
            price = Decimal(price_match.group()) if price_match else Decimal("0.00")
            sku = f"LARK-{data['category'].upper()}-{index:03d}"
            _, was_created = Product.objects.update_or_create(
                slug=slugify(data["name"]),
                defaults={
                    "name": data["name"],
                    "sku": sku,
                    "description": data["description"],
                    "category": categories[data["category"]],
                    "image_name": data["file"],
                    "price": price,
                    "stock_quantity": 100,
                    "is_active": True,
                },
            )
            created += was_created
            updated += not was_created
        self.stdout.write(self.style.SUCCESS(f"Storefront seeded: {created} created, {updated} updated."))
