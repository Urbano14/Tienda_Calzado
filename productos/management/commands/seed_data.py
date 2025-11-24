import base64
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from carrito.models import Carrito, ItemCarrito
from clientes.models import Cliente
from productos.models import Categoria, ImagenProducto, Marca, Producto


PLACEHOLDER_IMAGE = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4//8/AwAI/AL+9nHh"
    "AAAAAElFTkSuQmCC"
)


class Command(BaseCommand):
    help = "Carga datos de prueba para categorías, marcas, productos y cliente demo."

    def handle(self, *args, **options):
        self.stdout.write("Creando datos de prueba...")
        marcas = ["AeroRun", "UrbanStep", "TrailMaster", "ZenWalk"]
        categorias = [
            ("Running", "Zapatillas para correr"),
            ("Casual", "Uso diario"),
            ("Trail", "Senderismo y trail"),
            ("Training", "Entrenamiento en gimnasio"),
        ]

        marca_objs = {}
        for nombre in marcas:
            marca_objs[nombre], _ = Marca.objects.get_or_create(nombre=nombre)

        categoria_objs = {}
        for nombre, descripcion in categorias:
            categoria_objs[nombre], _ = Categoria.objects.get_or_create(
                nombre=nombre, defaults={"descripcion": descripcion}
            )

        productos_data = [
            ("AeroRun Swift 1", "Running", "AeroRun", "120.00"),
            ("AeroRun Swift 2", "Running", "AeroRun", "125.00"),
            ("UrbanStep Classic", "Casual", "UrbanStep", "89.90"),
            ("UrbanStep Canvas", "Casual", "UrbanStep", "79.90"),
            ("TrailMaster Pro", "Trail", "TrailMaster", "140.00"),
            ("TrailMaster Terrain", "Trail", "TrailMaster", "149.00"),
            ("ZenWalk Studio", "Training", "ZenWalk", "99.00"),
            ("ZenWalk Flex", "Training", "ZenWalk", "109.00"),
            ("AeroRun Pulse", "Running", "AeroRun", "132.00"),
            ("UrbanStep Metro", "Casual", "UrbanStep", "95.00"),
            ("TrailMaster Ridge", "Trail", "TrailMaster", "155.00"),
        ]

        for nombre, categoria, marca, precio in productos_data:
            producto, _ = Producto.objects.update_or_create(
                nombre=nombre,
                defaults={
                    "descripcion": f"{nombre} - modelo de demostración.",
                    "precio": Decimal(precio),
                    "stock": 50,
                    "marca": marca_objs[marca],
                    "categoria": categoria_objs[categoria],
                },
            )
            if not producto.imagenes.exists():
                content = ContentFile(
                    base64.b64decode(PLACEHOLDER_IMAGE),
                    name=f"{slugify(nombre)}.png",
                )
                ImagenProducto.objects.create(
                    producto=producto,
                    imagen=content,
                    es_principal=True,
                )

        user, created = User.objects.get_or_create(
            username="test",
            defaults={"email": "test@test.com", "first_name": "Test", "last_name": "User"},
        )
        if created:
            user.set_password("test1234")
            user.save()

        Cliente.objects.get_or_create(user=user)

        carrito, _ = Carrito.objects.get_or_create(usuario=user)
        carrito.items.all().delete()

        demo_productos = Producto.objects.all()[:3]
        for producto in demo_productos:
            ItemCarrito.objects.update_or_create(
                carrito=carrito,
                producto=producto,
                defaults={"cantidad": 2},
            )

        self.stdout.write(self.style.SUCCESS("Datos de ejemplo creados correctamente."))
