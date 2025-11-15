from django.db import models
from django.contrib.auth.models import User
from productos.models import Producto 
import uuid

# Create your models here.


# -------------------------------------------------------------------
# --- 1. El Contenedor: Carrito 🛍️ ---
# -------------------------------------------------------------------

class Carrito(models.Model):
    """
    Representa el carrito de compras. Se asocia opcionalmente con un usuario
    registrado o con un UUID para invitados (usado en cookies).
    """
    
    # Si el usuario está logueado, se asocia aquí (ForeignKey opcional).
    usuario = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, # Si el usuario se elimina, el carrito se mantiene (como invitado).
        null=True, 
        blank=True
    )
    
    #Identificador único para el carrito de invitado (se usa para almacenar en una cookie).
    guest_uuid = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    # Indica si el carrito ya fue finalizado y convertido en pedido.
    completado = models.BooleanField(default=False) 

    @property
    def obtener_total_carrito(self):
        """Calcula el costo total sumando todos los subtotales de los ítems."""
        items = self.itemcarrito_set.all()
        total = sum([item.obtener_subtotal for item in items])
        return total

    @property
    def obtener_total_articulos(self):
        """Calcula el número total de unidades (cantidad) de productos en el carrito."""
        items = self.itemcarrito_set.all()
        total = sum([item.cantidad for item in items])
        return total

    def __str__(self):
        if self.usuario:
            return f'Carrito de {self.usuario.username}'
        return f'Carrito de Invitado ({self.guest_uuid})'

# -------------------------------------------------------------------
# --- 2. Los Contenidos: ItemCarrito 👟 ---
# -------------------------------------------------------------------

class ItemCarrito(models.Model):
    """
    Representa una línea específica dentro de un carrito, conteniendo un producto 
    y una cantidad.
    """
    
    # Relación Muchos-a-Uno con el Carrito (contenedor).
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE)
    
    # Relación Muchos-a-Uno con el Producto (el artículo).
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    
    # Cantidad de este producto en particular.
    cantidad = models.IntegerField(default=1, null=False, blank=False)
    
    fecha_anadido = models.DateTimeField(auto_now_add=True)

    @property
    def obtener_subtotal(self):
        """Calcula el costo para esta línea de artículo: Precio * Cantidad."""
        return self.producto.precio * self.cantidad
    
    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'

    class Meta:
        # Restricción: Asegura que un producto solo puede tener una entrada por carrito.
        # Si se añade el mismo, se debe incrementar 'cantidad'.
        unique_together = ('carrito', 'producto')
