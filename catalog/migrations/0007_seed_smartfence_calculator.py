from decimal import Decimal

from django.db import migrations


RATES = {
    "trellis": (
        ("Anthracite", "anthracite-swatch", "26.60"),
        ("Goosewing Grey", "goosewing-swatch", "24.20"),
        ("Merlin Grey", "merlin-swatch", "24.20"),
        ("Olive Green", "olive-swatch", "24.20"),
        ("Buttermilk Cream", "buttermilk-swatch", "30.40"),
    ),
    "plinth": (
        ("Anthracite", "anthracite-swatch", "74.50"),
        ("Goosewing Grey", "goosewing-swatch", "67.50"),
        ("Merlin Grey", "merlin-swatch", "67.50"),
        ("Olive Green", "olive-swatch", "67.50"),
    ),
    "caps": (
        ("Anthracite", "anthracite-swatch", "60.50"),
        ("Goosewing Grey", "goosewing-swatch", "55.10"),
        ("Merlin Grey", "merlin-swatch", "55.10"),
        ("Olive Green", "olive-swatch", "55.10"),
    ),
}


def seed_calculator(apps, schema_editor):
    Settings = apps.get_model("catalog", "SmartFenceCalculatorSettings")
    Rate = apps.get_model("catalog", "SmartFenceCalculatorRate")
    Settings.objects.get_or_create(pk=1)
    for component, rates in RATES.items():
        for order, (name, swatch, price) in enumerate(rates):
            Rate.objects.get_or_create(
                component=component,
                name=name,
                defaults={
                    "swatch_class": swatch,
                    "unit_price": Decimal(price),
                    "display_order": order,
                    "is_active": True,
                },
            )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0006_smartfencecalculatorsettings_and_more")]
    operations = [migrations.RunPython(seed_calculator, migrations.RunPython.noop)]
