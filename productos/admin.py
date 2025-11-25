from django.contrib import admin

from .models import (
    Categoria,
    Departamento,
    ImagenProducto,
    Marca,
    Producto,
    Seccion,
    TallaProducto,
)


class ImagenProductoInline(admin.StackedInline):
    model = ImagenProducto
    extra = 0
    max_num = 1
    verbose_name_plural = "Imagen principal"


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Oculta el flag de disponibilidad para que dependa siempre del stock."""

    exclude = ("esta_disponible",)
    inlines = (ImagenProductoInline,)
    list_display = (
        "nombre",
        "marca",
        "categoria",
        "stock",
        "precio",
        "es_destacado",
    )
    list_filter = (
        "categoria__seccion__departamento",
        "categoria__seccion",
        "categoria",
        "marca",
    )
    search_fields = ("nombre",)


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "orden")
    search_fields = ("nombre",)
    readonly_fields = ("slug",)


@admin.register(Seccion)
class SeccionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "departamento", "orden")
    list_filter = ("departamento",)
    search_fields = ("nombre", "departamento__nombre")
    readonly_fields = ("slug",)


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug")
    search_fields = ("nombre",)
    readonly_fields = ("slug",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "seccion")
    list_filter = ("seccion__departamento", "seccion")
    search_fields = ("nombre",)
    readonly_fields = ("slug",)

admin.site.register(TallaProducto)
