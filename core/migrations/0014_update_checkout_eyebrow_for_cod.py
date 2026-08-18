from django.db import migrations


def update_checkout_eyebrow(apps, schema_editor):
    WebsiteContent = apps.get_model("core", "WebsiteContent")
    WebsiteContent.objects.filter(
        key="checkout_hero_eyebrow",
        value="Online payment",
    ).update(value="Cash on delivery")


def restore_checkout_eyebrow(apps, schema_editor):
    WebsiteContent = apps.get_model("core", "WebsiteContent")
    WebsiteContent.objects.filter(
        key="checkout_hero_eyebrow",
        value="Cash on delivery",
    ).update(value="Online payment")


class Migration(migrations.Migration):
    dependencies = [("core", "0013_update_checkout_content_for_cod")]

    operations = [migrations.RunPython(update_checkout_eyebrow, restore_checkout_eyebrow)]
