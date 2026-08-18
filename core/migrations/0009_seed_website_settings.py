from django.db import migrations


MAP_EMBED_URL = (
    "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2388.4698265599195!"
    "2d-6.610529199999999!3d53.227353799999996!2m3!1f0!2f0!3f0!3m2!1i1024!"
    "2i768!4f13.1!3m3!1m2!1s0x48677974a2db18af%3A0x457fc66e2fa74281!"
    "2sLark%20Fencing!5e0!3m2!1sen!2sie!4v1785593540699!5m2!1sen!2sie"
)


def create_website_settings(apps, schema_editor):
    WebsiteSettings = apps.get_model("core", "WebsiteSettings")
    WebsiteSettings.objects.get_or_create(pk=1, defaults={"map_embed_url": MAP_EMBED_URL})


class Migration(migrations.Migration):
    dependencies = [("core", "0008_websitesettings")]
    operations = [migrations.RunPython(create_website_settings, migrations.RunPython.noop)]
