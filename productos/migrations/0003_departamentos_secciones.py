from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0002_tallaproducto"),
    ]

    operations = [
        migrations.CreateModel(
            name="Departamento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=120, unique=True)),
                ("descripcion", models.TextField(blank=True, null=True)),
                ("slug", models.SlugField(blank=True, max_length=160, null=True, unique=True)),
                ("orden", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Departamento",
                "verbose_name_plural": "Departamentos",
                "ordering": ("orden", "nombre"),
            },
        ),
        migrations.CreateModel(
            name="Seccion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=120)),
                ("descripcion", models.TextField(blank=True, null=True)),
                ("slug", models.SlugField(blank=True, max_length=160, null=True, unique=True)),
                ("orden", models.PositiveSmallIntegerField(default=0)),
                (
                    "departamento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="secciones",
                        to="productos.departamento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Sección",
                "verbose_name_plural": "Secciones",
                "ordering": ("orden", "nombre"),
                "unique_together": {("departamento", "nombre")},
            },
        ),
        migrations.AddField(
            model_name="marca",
            name="slug",
            field=models.SlugField(blank=True, max_length=160, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="categoria",
            name="slug",
            field=models.SlugField(blank=True, max_length=160, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="categoria",
            name="seccion",
            field=models.ForeignKey(
                blank=True,
                help_text="Permite replicar la jerarquía física de la tienda.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="categorias",
                to="productos.seccion",
            ),
        ),
    ]
