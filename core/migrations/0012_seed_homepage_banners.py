from django.db import migrations


BANNERS = (
    {
        "eyebrow": "Pressure-treated timber",
        "title": "Natural privacy, made to last.",
        "image": "banners/home-hero-fence-v3.png",
        "image_alt": "Horizontal timber privacy fence in a landscaped modern garden",
        "link_url": "/catalog/",
        "link_label": "Shop timber",
        "display_order": 1,
    },
    {
        "eyebrow": "Low-maintenance SmartFence",
        "title": "Never needs painting.",
        "image": "banners/smartfence-product-hero-v2.png",
        "image_alt": "Anthracite SmartFence installed in a landscaped garden",
        "link_url": "/smart-fence/#fence-builder",
        "link_label": "Design your fence",
        "display_order": 2,
    },
    {
        "eyebrow": "Composite panel systems",
        "title": "Complete panels from €199.29.",
        "image": "banners/composite-v1.png",
        "image_alt": "Modern composite fencing installed in a garden",
        "link_url": "/catalog/",
        "link_label": "View composite",
        "display_order": 3,
    },
)


def seed_banners(apps, schema_editor):
    Banner = apps.get_model("core", "Banner")
    for values in BANNERS:
        Banner.objects.get_or_create(
            title=values["title"],
            defaults={**values, "is_active": True},
        )


def remove_seeded_banners(apps, schema_editor):
    Banner = apps.get_model("core", "Banner")
    Banner.objects.filter(title__in=[banner["title"] for banner in BANNERS]).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0011_seed_website_content")]

    operations = [migrations.RunPython(seed_banners, remove_seeded_banners)]
