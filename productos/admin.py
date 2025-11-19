from django.contrib import admin
from .models import Marca, Categoria, Producto, ImagenProducto, TallaProducto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Oculta el flag de disponibilidad para que dependa siempre del stock."""

    exclude = ("esta_disponible",)
    list_display = ("nombre", "marca", "categoria", "stock", "precio", "es_destacado")
    list_filter = ("categoria", "marca")
    search_fields = ("nombre",)


admin.site.register(Marca)
admin.site.register(Categoria)
admin.site.register(ImagenProducto)
admin.site.register(TallaProducto)
