from django.contrib import admin

from .models import ItemPedido, Pedido


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ("producto", "talla", "cantidad", "precio_unitario", "total")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_pedido",
        "cliente",
        "fecha_creacion",
        "estado",
        "total",
    )
    list_filter = ("estado", "metodo_pago", "fecha_creacion")
    search_fields = (
        "numero_pedido",
        "cliente__email",
        "cliente__nombre",
        "cliente__apellidos",
        "email_contacto",
    )
    inlines = [ItemPedidoInline]
    readonly_fields = ("fecha_creacion",)


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "producto", "talla", "cantidad", "precio_unitario", "total")
    search_fields = ("pedido__numero_pedido", "producto__nombre")
