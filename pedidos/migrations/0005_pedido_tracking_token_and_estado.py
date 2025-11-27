import uuid

from django.db import migrations, models


def forward_update_estados(apps, schema_editor):
    Pedido = apps.get_model("pedidos", "Pedido")
    Pedido.objects.filter(estado="preparando").update(estado="procesando")


def backward_update_estados(apps, schema_editor):
    Pedido = apps.get_model("pedidos", "Pedido")
    Pedido.objects.filter(estado="procesando").update(estado="preparando")


def populate_tracking_tokens(apps, schema_editor):
    Pedido = apps.get_model("pedidos", "Pedido")
    for pedido in Pedido.objects.filter(tracking_token__isnull=True):
        pedido.tracking_token = uuid.uuid4()
        pedido.save(update_fields=["tracking_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0004_alter_pedido_metodo_pago"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="tracking_token",
            field=models.UUIDField(
                db_index=True,
                default=None,
                editable=False,
                unique=True,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="pedido",
            name="estado",
            field=models.CharField(
                choices=[
                    ("pendiente", "Pendiente"),
                    ("procesando", "Procesando"),
                    ("enviado", "Enviado"),
                    ("entregado", "Entregado"),
                    ("cancelado", "Cancelado"),
                ],
                default="pendiente",
                max_length=20,
            ),
        ),
        migrations.RunPython(populate_tracking_tokens),
        migrations.AlterField(
            model_name="pedido",
            name="tracking_token",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
        migrations.RunPython(
            forward_update_estados,
            backward_update_estados,
        ),
    ]
