from django.conf import settings
from django.db import models

from productos.models import Producto


class Carrito(models.Model):
    """Contenedor del carrito, asociado a un usuario o a la sesion anonima."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carritos",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    @property
    def obtener_total_carrito(self):
        return sum(item.obtener_subtotal for item in self.items.all())

    @property
    def obtener_total_articulos(self):
        return sum(item.cantidad for item in self.items.all())

    def __str__(self):
        if self.usuario:
            return f"Carrito de {self.usuario.username}"
        return "Carrito de invitado"


class ItemCarrito(models.Model):
    """Linea de detalle dentro del carrito."""

    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name="items",
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    talla = models.CharField(max_length=30, null=True, blank=True)
    fecha_anadido = models.DateTimeField(auto_now_add=True)

    @property
    def obtener_subtotal(self):
        return self.producto.precio_vigente * self.cantidad

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

    class Meta:
        unique_together = ("carrito", "producto", "talla")
