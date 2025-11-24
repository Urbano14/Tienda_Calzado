from decimal import Decimal

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from pedidos.models import ItemPedido, Pedido


class DatosClienteSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150)
    apellidos = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    telefono = serializers.CharField(max_length=30)
    direccion = serializers.CharField(max_length=255)
    ciudad = serializers.CharField(max_length=120)
    codigo_postal = serializers.CharField(max_length=20)
    password = serializers.CharField(max_length=128, required=False, allow_blank=True)


class ItemPedidoSerializer(serializers.ModelSerializer):
    producto_id = serializers.IntegerField(source="producto.id", read_only=True)
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)

    class Meta:
        model = ItemPedido
        fields = (
            "id",
            "producto_id",
            "producto_nombre",
            "talla",
            "cantidad",
            "precio_unitario",
            "total",
        )


class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, read_only=True)
    cliente = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = (
            "id",
            "numero_pedido",
            "fecha_creacion",
            "estado",
            "subtotal",
            "impuestos",
            "coste_entrega",
            "descuento",
            "total",
            "metodo_pago",
            "direccion_envio",
            "telefono",
            "cliente",
            "items",
        )

    def get_cliente(self, obj):
        if not obj.cliente:
            return None
        cliente = obj.cliente
        return {
            "id": cliente.pk,
            "nombre": getattr(cliente, "nombre", None) or getattr(cliente, "first_name", ""),
            "apellidos": getattr(cliente, "apellidos", None) or getattr(cliente, "last_name", ""),
            "email": getattr(cliente, "email", ""),
            "telefono": getattr(cliente, "telefono", ""),
            "direccion": getattr(cliente, "direccion", ""),
            "ciudad": getattr(cliente, "ciudad", ""),
            "codigo_postal": getattr(cliente, "codigo_postal", ""),
        }


class PedidoCreateSerializer(serializers.Serializer):
    carrito_id = serializers.IntegerField(required=False, help_text=_("Identificador del carrito a procesar."))
    metodo_pago = serializers.ChoiceField(choices=Pedido.MetodosPago.choices)
    direccion_envio = serializers.CharField()
    telefono = serializers.CharField()
    descuento = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )
    datos_cliente = DatosClienteSerializer(required=False, allow_null=True)

    def validate(self, attrs):
        request = self.context.get("request")
        if request and not request.user.is_authenticated and not attrs.get("datos_cliente"):
            raise serializers.ValidationError({"datos_cliente": _("Los invitados deben indicar sus datos.")})
        return attrs
