from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_orderitem_variant_orderitem_variant_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="inventory_restocked_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="staff_notes",
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name="OrderStatusHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("previous_status", models.CharField(blank=True, choices=[("pending_payment", "Pending payment"), ("confirmed", "Confirmed"), ("processing", "Processing"), ("ready", "Ready for collection / dispatch"), ("dispatched", "Dispatched"), ("delivered", "Delivered"), ("cancelled", "Cancelled"), ("partially_refunded", "Partially refunded"), ("refunded", "Refunded")], max_length=30)),
                ("new_status", models.CharField(choices=[("pending_payment", "Pending payment"), ("confirmed", "Confirmed"), ("processing", "Processing"), ("ready", "Ready for collection / dispatch"), ("dispatched", "Dispatched"), ("delivered", "Delivered"), ("cancelled", "Cancelled"), ("partially_refunded", "Partially refunded"), ("refunded", "Refunded")], max_length=30)),
                ("note", models.TextField(blank=True, max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="order_status_changes", to=settings.AUTH_USER_MODEL)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="status_history", to="orders.order")),
            ],
            options={"verbose_name_plural": "order status histories", "ordering": ["-created_at", "-pk"]},
        ),
    ]
