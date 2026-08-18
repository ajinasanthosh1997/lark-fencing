from django.db import migrations


def seed_settings(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Settings = apps.get_model("catalog", "ProjectCalculatorSettings")
    default_product = Product.objects.filter(name="Solid Cottage Fence Panel").first()
    Settings.objects.get_or_create(pk=1, defaults={"default_product": default_product})


class Migration(migrations.Migration):
    dependencies = [("catalog", "0010_homepage_project_calculator_settings")]

    operations = [migrations.RunPython(seed_settings, migrations.RunPython.noop)]
