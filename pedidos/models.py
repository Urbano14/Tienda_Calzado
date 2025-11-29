import uuid
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from productos.models import Producto


class Pedido(models.Model):
    class Estados(models.TextChoices):
        PENDIENTE = "pendiente", _("Pendiente")
        PROCESANDO = "procesando", _("Procesando")
        ENVIADO = "enviado", _("Enviado")
        ENTREGADO = "entregado", _("Entregado")
        CANCELADO = "cancelado", _("Cancelado")

    class MetodosPago(models.TextChoices):
        TARJETA = "tarjeta", _("Tarjeta")
        CONTRAREEMBOLSO = "contrareembolso", _("Contrareembolso")

    class MetodosEntrega(models.TextChoices):
        ESTANDAR = "estandar", _("Envío estándar (48-72h)")
        URGENTE = "urgente", _("Envío urgente (24h)")
        RECOGIDA = "recogida", _("Recogida en tienda")

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="pedidos",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    numero_pedido = models.CharField(max_length=30, unique=True)
    estado = models.CharField(
        max_length=20,
        choices=Estados.choices,
        default=Estados.PENDIENTE,
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    impuestos = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    coste_entrega = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    metodo_pago = models.CharField(max_length=30, choices=MetodosPago.choices)
    direccion_envio = models.TextField()
    metodo_entrega = models.CharField(
        max_length=20,
        choices=MetodosEntrega.choices,
        default=MetodosEntrega.ESTANDAR,
    )
    email_contacto = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=30)
    tracking_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_payment_status = models.CharField(max_length=50, blank=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    stripe_receipt_url = models.URLField(blank=True)

    class Meta:
        ordering = ("-fecha_creacion",)

    def __str__(self):
        return f"{self.numero_pedido} ({self.estado})"

    def save(self, *args, **kwargs):
        if self.pk:
            original_token = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("tracking_token", flat=True)
                .first()
            )
            if original_token:
                self.tracking_token = original_token
            update_fields = kwargs.get("update_fields")
            if update_fields:
                kwargs["update_fields"] = tuple(
                    field for field in update_fields if field != "tracking_token"
                )
        elif not self.tracking_token:
            self.tracking_token = uuid.uuid4()
        super().save(*args, **kwargs)


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="items_pedido")
    talla = models.CharField(max_length=20, blank=True)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"
