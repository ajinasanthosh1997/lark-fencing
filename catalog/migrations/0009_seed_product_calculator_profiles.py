from decimal import Decimal

from django.db import migrations


CALCULATOR_PRODUCTS = {
    "Solid Cottage Fence Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Solid Arched Cottage Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Arched Cottage Fence Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Weatherboard Fence Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Barrelboard Fence Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Castle Top Fence Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Hit & Miss Fence Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Shiplap Dipped-Treated Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Picket Fence Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Florence Bow Top Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Malvern Fence Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Bastia Fence Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Verona Fence Panel": ("Timber fence panels", "1.80", None, "Panels required", None),
    "Smart Fence Panel": ("SmartFence", "1.80", None, "Panel packs", "smartfence"),
    "Composite Panel 1.8 x 1.8m": ("Composite fencing", "1.80", "1.80", "Panel packs", "228.20"),
    "Composite Panel 1.8 x 1.5m": ("Composite fencing", "1.80", "1.50", "Panel packs", "199.29"),
    "PVC Fence Panel": ("PVC fencing", "1.80", None, "Panels required", None),
    "Slate Concrete Fence Panel": ("Concrete fencing", "1.83", None, "Panels required", None),
    "Plain Concrete Base": ("Concrete fencing", "1.83", None, "Base panels", None),
    "Rock Face Concrete Base": ("Concrete fencing", "1.83", None, "Base panels", None),
}


def seed_profiles(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Profile = apps.get_model("catalog", "ProductCalculatorProfile")
    for display_order, (name, values) in enumerate(CALCULATOR_PRODUCTS.items(), start=1):
        product = Product.objects.filter(name=name).first()
        if not product:
            continue
        group_name, width, height, item_label, special_price = values
        pricing_mode = "quote"
        unit_price_override = None
        if special_price == "smartfence":
            pricing_mode = "smartfence"
        elif special_price:
            pricing_mode = "product"
            unit_price_override = Decimal(special_price)
        elif product.price and product.price > 0:
            pricing_mode = "product"
        Profile.objects.get_or_create(
            product=product,
            defaults={
                "group_name": group_name,
                "panel_width": Decimal(width),
                "default_height": Decimal(height) if height else None,
                "item_label": item_label,
                "post_extra": 1,
                "pricing_mode": pricing_mode,
                "unit_price_override": unit_price_override,
                "calculation_note": (
                    f"{name} estimate uses {width}m-wide bays. Confirm the chosen product size, "
                    "gates, corners, delivery, and site conditions before ordering."
                ),
                "display_order": display_order,
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0008_product_calculator_profiles")]

    operations = [migrations.RunPython(seed_profiles, migrations.RunPython.noop)]
