from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0005_imagenproducto_unique_imagen_por_producto"),
    ]

    operations = [
        migrations.AlterField(
            model_name="producto",
            name="nombre",
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="producto",
            name="categoria",
            field=models.ForeignKey(
                db_index=True,
                on_delete=models.CASCADE,
                related_name="productos",
                to="productos.categoria",
            ),
        ),
        migrations.AlterField(
            model_name="producto",
            name="marca",
            field=models.ForeignKey(
                db_index=True,
                on_delete=models.CASCADE,
                related_name="productos",
                to="productos.marca",
            ),
        ),
    ]
