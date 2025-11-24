from django.db import migrations, models
from django.utils.text import slugify


def _unique_slug(model, value, pk=None):
    base = slugify(value) or "item"
    slug = base
    suffix = 1
    queryset = model.objects.all()
    if pk is not None:
        queryset = queryset.exclude(pk=pk)

    while queryset.filter(slug=slug).exists():
        suffix += 1
        slug = f"{base}-{suffix}"
    return slug


def populate_navigation(apps, schema_editor):
    Marca = apps.get_model("productos", "Marca")
    Categoria = apps.get_model("productos", "Categoria")
    Departamento = apps.get_model("productos", "Departamento")
    Seccion = apps.get_model("productos", "Seccion")

    for marca in Marca.objects.all():
        if not marca.slug:
            marca.slug = _unique_slug(Marca, marca.nombre, marca.pk)
            marca.save(update_fields=["slug"])

    for categoria in Categoria.objects.all():
        if not categoria.slug:
            categoria.slug = _unique_slug(Categoria, categoria.nombre, categoria.pk)
            categoria.save(update_fields=["slug"])

    layout = [
        {
            "nombre": "Colección Performance",
            "descripcion": "Modelos pensados para entrenamiento y alto rendimiento.",
            "slug": "coleccion-performance",
            "orden": 1,
            "secciones": [
                {
                    "nombre": "Running & Training",
                    "slug": "running-training",
                    "descripcion": "Zapatillas técnicas para correr y entrenar.",
                    "orden": 1,
                    "categorias": ["Running", "Zapatillas Deportivas"],
                },
            ],
        },
        {
            "nombre": "Colección Urbana",
            "descripcion": "Selección curada para el día a día y la ciudad.",
            "slug": "coleccion-urbana",
            "orden": 2,
            "secciones": [
                {
                    "nombre": "Lifestyle & Street",
                    "slug": "lifestyle-street",
                    "descripcion": "Botas y zapatillas urbanas.",
                    "orden": 1,
                    "categorias": ["Botas Urbanas"],
                },
            ],
        },
        {
            "nombre": "Colección Estacional",
            "descripcion": "Propuestas para climas cálidos y descanso.",
            "slug": "coleccion-estacional",
            "orden": 3,
            "secciones": [
                {
                    "nombre": "Sandalias & Slides",
                    "slug": "sandalias-slides",
                    "descripcion": "Modelos ligeros y veraniegos.",
                    "orden": 1,
                    "categorias": ["Sandalias"],
                },
            ],
        },
    ]

    assigned = set()

    for dept_spec in layout:
        dept, _ = Departamento.objects.get_or_create(
            nombre=dept_spec["nombre"],
            defaults={
                "descripcion": dept_spec.get("descripcion", ""),
                "orden": dept_spec.get("orden", 0),
                "slug": dept_spec.get("slug") or _unique_slug(Departamento, dept_spec["nombre"]),
            },
        )
        if not dept.slug:
            dept.slug = _unique_slug(Departamento, dept.nombre, dept.pk)
            dept.save(update_fields=["slug"])

        for section_spec in dept_spec.get("secciones", []):
            seccion, _ = Seccion.objects.get_or_create(
                nombre=section_spec["nombre"],
                departamento=dept,
                defaults={
                    "descripcion": section_spec.get("descripcion", ""),
                    "orden": section_spec.get("orden", 0),
                    "slug": section_spec.get("slug") or _unique_slug(Seccion, section_spec["nombre"]),
                },
            )
            if not seccion.slug:
                seccion.slug = _unique_slug(Seccion, seccion.nombre, seccion.pk)
                seccion.save(update_fields=["slug"])

            for categoria_name in section_spec.get("categorias", []):
                categoria = Categoria.objects.filter(nombre__iexact=categoria_name).first()
                if not categoria or categoria.pk in assigned:
                    continue
                categoria.seccion = seccion
                categoria.save(update_fields=["seccion"])
                assigned.add(categoria.pk)

    fallback_dept, _ = Departamento.objects.get_or_create(
        nombre="Colección General",
        defaults={
            "descripcion": "Agrupa el resto de referencias.",
            "orden": 99,
            "slug": _unique_slug(Departamento, "Colección General"),
        },
    )
    if not fallback_dept.slug:
        fallback_dept.slug = _unique_slug(Departamento, fallback_dept.nombre, fallback_dept.pk)
        fallback_dept.save(update_fields=["slug"])

    fallback_seccion, _ = Seccion.objects.get_or_create(
        nombre="Selección Global",
        departamento=fallback_dept,
        defaults={
            "descripcion": "Productos sin sección asignada.",
            "orden": 99,
            "slug": _unique_slug(Seccion, "Selección Global"),
        },
    )
    if not fallback_seccion.slug:
        fallback_seccion.slug = _unique_slug(Seccion, fallback_seccion.nombre, fallback_seccion.pk)
        fallback_seccion.save(update_fields=["slug"])

    for categoria in Categoria.objects.filter(seccion__isnull=True):
        categoria.seccion = fallback_seccion
        categoria.save(update_fields=["seccion"])


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0003_departamentos_secciones"),
    ]

    operations = [
        migrations.RunPython(populate_navigation, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="marca",
            name="slug",
            field=models.SlugField(blank=True, max_length=160, unique=True),
        ),
        migrations.AlterField(
            model_name="categoria",
            name="slug",
            field=models.SlugField(blank=True, max_length=160, unique=True),
        ),
        migrations.AlterField(
            model_name="departamento",
            name="slug",
            field=models.SlugField(blank=True, max_length=160, unique=True),
        ),
        migrations.AlterField(
            model_name="seccion",
            name="slug",
            field=models.SlugField(blank=True, max_length=160, unique=True),
        ),
    ]
