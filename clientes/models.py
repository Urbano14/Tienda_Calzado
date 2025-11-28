from django.contrib.auth.models import User
from django.db import models


class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cliente")
    nombre_completo = models.CharField(max_length=150, blank=True)
    apellidos = models.CharField(max_length=150, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    codigo_postal = models.CharField(max_length=10, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)

    METODO_PAGO_CHOICES = [
        ("stripe", "Tarjeta (Stripe)"),
        ("contrareembolso", "Contrareembolso"),
    ]
    metodo_pago_preferido = models.CharField(
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        blank=True,
    )

    def __str__(self):
        return f"Cliente {self.user.email or self.user.username}"
