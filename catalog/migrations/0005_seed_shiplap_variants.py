from decimal import Decimal

from django.db import migrations


VARIANTS = (
    ("1.8m (W) × 1.8m (H)", "43.00"),
    ("1.8m × 1.5m", "39.00"),
    ("1.8m × 1.2m", "35.00"),
    ("1.8m × 0.9m", "31.00"),
    ("1.8m × 0.6m", "27.00"),
)


def seed_shiplap_variants(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    ProductVariant = apps.get_model("catalog", "ProductVariant")
    product = Product.objects.filter(sku="LARK-TIMBER-010").first()
    if not product:
        return
    product.price = Decimal("43.00")
    product.save(update_fields=["price"])
    for order, (size, price) in enumerate(VARIANTS):
        style = "Pressure Treated"
        ProductVariant.objects.update_or_create(
            product=product,
            size=size,
            style=style,
            defaults={
                "name": f"{size} — {style}",
                "sku": f"{product.sku}-PT-{order + 1}",
                "price": Decimal(price),
                "stock_quantity": product.stock_quantity,
                "display_order": order,
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_remove_productvariant_unique_variant_name_per_product_and_more")]
    operations = [migrations.RunPython(seed_shiplap_variants, migrations.RunPython.noop)]
