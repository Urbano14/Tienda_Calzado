from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="email_contacto",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
