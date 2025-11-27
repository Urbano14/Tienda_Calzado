from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from .utils import build_unique_slug


class Departamento(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("orden", "nombre")
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Departamento, self.nombre, self.pk)
        super().save(*args, **kwargs)


class Seccion(models.Model):
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.CASCADE,
        related_name="secciones",
    )
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("orden", "nombre")
        verbose_name = "Sección"
        verbose_name_plural = "Secciones"
        unique_together = ("departamento", "nombre")

    def __str__(self):
        return f"{self.departamento.nombre} · {self.nombre}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Seccion, self.nombre, self.pk)
        super().save(*args, **kwargs)


class Marca(models.Model):
    nombre = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to="marcas/", blank=True, null=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Marca, self.nombre, self.pk)
        super().save(*args, **kwargs)


class Categoria(models.Model):
    seccion = models.ForeignKey(
        Seccion,
        on_delete=models.SET_NULL,
        related_name="categorias",
        blank=True,
        null=True,
        help_text="Permite replicar la jerarquía física de la tienda.",
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to="categorias/", blank=True, null=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Categoria, self.nombre, self.pk)
        super().save(*args, **kwargs)


class Producto(models.Model):
    nombre = models.CharField(max_length=200, db_index=True)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_oferta = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    marca = models.ForeignKey(
        Marca, on_delete=models.CASCADE, related_name="productos", db_index=True
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, related_name="productos", db_index=True
    )
    genero = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    material = models.CharField(max_length=100, blank=True, null=True)
    stock = models.IntegerField(default=0)
    esta_disponible = models.BooleanField(default=True)
    es_destacado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # La disponibilidad se deriva del stock: si no hay unidades, se marca como no disponible.
        self.esta_disponible = self.stock > 0
        super().save(*args, **kwargs)

    @property
    def precio_vigente(self):
        """Devuelve el precio a usar (oferta si existe, si no el base)."""
        if self.precio_oferta is not None:
            return Decimal(self.precio_oferta)
        return Decimal(self.precio)

    @property
    def imagen_destacada(self):
        """Provee la única imagen asociada para simplificar el consumo en plantillas."""
        return self.imagenes.first()

    @property
    def sin_stock(self):
        return not self.esta_disponible


class ImagenProducto(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name="imagenes"
    )
    imagen = models.ImageField(upload_to="productos/")
    es_principal = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Imagen de producto"
        verbose_name_plural = "Imágenes de productos"
        constraints = (
            models.UniqueConstraint(
                fields=("producto",), name="unique_imagen_por_producto"
            ),
        )

    def clean(self):
        if not self.producto_id:
            return
        qs = ImagenProducto.objects.filter(producto=self.producto)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError("Cada producto solo admite una imagen principal.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Imagen de {self.producto.nombre}"

    
class TallaProducto(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="tallas",
    )
    talla = models.CharField(max_length=10)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Talla de producto"
        verbose_name_plural = "Tallas de productos"

    def __str__(self):
        return f"{self.producto.nombre} - Talla {self.talla}"
