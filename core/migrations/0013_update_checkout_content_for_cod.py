from django.db import migrations


OLD_CART_INTRO = "Review quantities and prices before continuing to secure online card payment."
NEW_CART_INTRO = "Review quantities and prices before continuing to cash-on-delivery checkout."
OLD_CHECKOUT_INTRO = "Enter your delivery details and continue using secure online card payment."
NEW_CHECKOUT_INTRO = "Enter your delivery details, place your order, and pay cash when it is delivered."


def update_checkout_content(apps, schema_editor):
    WebsiteContent = apps.get_model("core", "WebsiteContent")
    WebsiteContent.objects.filter(key="cart_hero_intro", value=OLD_CART_INTRO).update(value=NEW_CART_INTRO)
    WebsiteContent.objects.filter(key="checkout_hero_intro", value=OLD_CHECKOUT_INTRO).update(value=NEW_CHECKOUT_INTRO)


def restore_checkout_content(apps, schema_editor):
    WebsiteContent = apps.get_model("core", "WebsiteContent")
    WebsiteContent.objects.filter(key="cart_hero_intro", value=NEW_CART_INTRO).update(value=OLD_CART_INTRO)
    WebsiteContent.objects.filter(key="checkout_hero_intro", value=NEW_CHECKOUT_INTRO).update(value=OLD_CHECKOUT_INTRO)


class Migration(migrations.Migration):
    dependencies = [("core", "0012_seed_homepage_banners")]

    operations = [migrations.RunPython(update_checkout_content, restore_checkout_content)]
