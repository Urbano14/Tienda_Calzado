from django.db import models


class Marca(models.Model):
    nombre = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to="marcas/", blank=True, null=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to="categorias/", blank=True, null=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_oferta = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name="productos")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, related_name="productos"
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

    @property
    def imagen_destacada(self):
        return self.imagenes.filter(es_principal=True).first() or self.imagenes.first()


class ImagenProducto(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name="imagenes"
    )
    imagen = models.ImageField(upload_to="productos/")
    es_principal = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Imagen de producto"
        verbose_name_plural = "Imágenes de productos"

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
