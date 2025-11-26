from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0002_pedido_email_contacto"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="stripe_charge_id",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="pedido",
            name="stripe_payment_intent_id",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="pedido",
            name="stripe_payment_status",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="pedido",
            name="stripe_receipt_url",
            field=models.URLField(blank=True),
        ),
    ]
