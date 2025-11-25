import base64
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from carrito.models import Carrito, ItemCarrito
from clientes.models import Cliente
from productos.models import (
    Categoria,
    Departamento,
    ImagenProducto,
    Marca,
    Producto,
    Seccion,
    TallaProducto,
)


PLACEHOLDER_IMAGE = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4//8/AwAI/AL+9nHh"
    "AAAAAElFTkSuQmCC"
)

CATALOG_STRUCTURE = [
    {
        "departamento": {
            "nombre": "Colección Performance",
            "descripcion": "Modelos técnicos para entrenar y competir.",
            "orden": 1,
        },
        "secciones": [
            {
                "nombre": "Running & Training",
                "descripcion": "Sneakers de alto rendimiento y preparación física.",
                "orden": 1,
                "categorias": [
                    {
                        "nombre": "Running Profesional",
                        "descripcion": "Zapatillas listas para sumar kilómetros y competir.",
                    },
                    {
                        "nombre": "Trail Técnico",
                        "descripcion": "Diseños con agarre reforzado para montaña y clima adverso.",
                    },
                    {
                        "nombre": "Training Studio",
                        "descripcion": "Modelos estables para rutinas de gimnasio y clases dirigidas.",
                    },
                ],
            }
        ],
    },
    {
        "departamento": {
            "nombre": "Colección Urbana",
            "descripcion": "Estilos pensados para la ciudad.",
            "orden": 2,
        },
        "secciones": [
            {
                "nombre": "Lifestyle & Street",
                "descripcion": "Silhuetas casual premium y streetwear.",
                "orden": 1,
                "categorias": [
                    {
                        "nombre": "Casual Premium",
                        "descripcion": "Clásicos reinterpretados para el día a día.",
                    },
                    {
                        "nombre": "Street Icon",
                        "descripcion": "Modelos urbanos con carácter y materiales mixtos.",
                    },
                ],
            }
        ],
    },
    {
        "departamento": {
            "nombre": "Colección Estacional",
            "descripcion": "Selección ligera para climas cálidos.",
            "orden": 3,
        },
        "secciones": [
            {
                "nombre": "Sandalias & Slides",
                "descripcion": "Diseños estivales y de relax.",
                "orden": 1,
                "categorias": [
                    {
                        "nombre": "Slides & Verano",
                        "descripcion": "Opciones livianas para descansar después del entrenamiento.",
                    }
                ],
            }
        ],
    },
]

LEGACY_CATEGORY_NAMES = ("Running", "Casual", "Trail", "Training")

IMAGE_OVERRIDES = {
    "Nike Air Zoom Pegasus 39": "productos/Nike_Air_Zoom_Pegasus_39.jpg",
    "Adidas Ultraboost 22": "productos/Adids_Ultraboost_22.jpg",
    "Puma Cali Dream": "productos/Puma_Cali_Dream.jpg",
    "New Balance 574 Classic": "productos/New_Balance_574.jpg",
    "Nike Air Force 1 Low": "productos/Air_Force_1_Low.jpg",
    "Adidas Stan Smith": "productos/Stan_Smith.jpg",
    "Puma Future Rider": "productos/Puma_Future_Rider.jpg",
    "New Balance 327": "productos/New_Balance_327.jpg",
    "Adidas Terrex Free Hiker": "productos/Adidas_Terrex_Free_Hiker.jpg",
    "Nike Air Max 90": "productos/Air_Max_90_Slawn.jpg",
    "Puma Leadcat 2.0": "productos/Puma_Leadcat_2.0.jpg",
    "Adidas Adilette Comfort": "productos/Adilette.jpg",
}

DEFAULT_TALLAS = ["38", "39", "40", "41", "42", "43"]
TALLA_SETS = {
    "Running Profesional": ["38", "39", "40", "41", "42", "43", "44"],
    "Trail Técnico": ["39", "40", "41", "42", "43", "44", "45"],
    "Training Studio": ["36", "37", "38", "39", "40", "41"],
    "Casual Premium": ["35", "36", "37", "38", "39", "40", "41", "42"],
    "Street Icon": ["37", "38", "39", "40", "41", "42", "43"],
    "Slides & Verano": ["35", "36", "37", "38", "39", "40", "41", "42", "43", "44"],
}

PRODUCTS_DATA = [
    {
        "nombre": "AeroRun Swift 1",
        "categoria": "Running Profesional",
        "marca": "AeroRun",
        "precio": "120.00",
        "precio_oferta": "110.00",
        "descripcion": "Plancha de carbono flexible y espuma reactiva para tus fondos.",
        "stock": 80,
        "es_destacado": True,
        "imagen": "productos/aerorun-swift-1.png",
        "color": "Azul acero",
        "material": "Malla técnica",
    },
    {
        "nombre": "AeroRun Swift 2",
        "categoria": "Running Profesional",
        "marca": "AeroRun",
        "precio": "125.00",
        "precio_oferta": None,
        "descripcion": "Upper reforzado y suela con mayor retorno de energía.",
        "stock": 60,
        "es_destacado": False,
        "imagen": "productos/aerorun-swift-2.png",
        "color": "Gris tormenta",
        "material": "Mesh reciclado",
    },
    {
        "nombre": "UrbanStep Classic",
        "categoria": "Casual Premium",
        "marca": "UrbanStep",
        "precio": "89.90",
        "precio_oferta": "79.90",
        "descripcion": "Perfil bajo con cupsole y cuero premium para looks diarios.",
        "stock": 75,
        "es_destacado": True,
        "imagen": "productos/urbanstep-classic.png",
        "color": "Blanco tiza",
        "material": "Cuero vacuno",
    },
    {
        "nombre": "UrbanStep Canvas",
        "categoria": "Casual Premium",
        "marca": "UrbanStep",
        "precio": "79.90",
        "precio_oferta": None,
        "descripcion": "Lona encerada y plantilla foam para jornadas extensas.",
        "stock": 90,
        "es_destacado": False,
        "imagen": "productos/urbanstep-canvas.png",
        "color": "Arena",
        "material": "Canvas encerado",
    },
    {
        "nombre": "TrailMaster Pro",
        "categoria": "Trail Técnico",
        "marca": "TrailMaster",
        "precio": "140.00",
        "precio_oferta": "129.00",
        "descripcion": "Suela Vibram y membrana impermeable para montaña.",
        "stock": 55,
        "es_destacado": True,
        "imagen": "productos/trailmaster-pro.png",
        "color": "Negro / Lima",
        "material": "Ripstop",
    },
    {
        "nombre": "TrailMaster Terrain",
        "categoria": "Trail Técnico",
        "marca": "TrailMaster",
        "precio": "149.00",
        "precio_oferta": None,
        "descripcion": "Protector de puntera y agarre agresivo para terrenos técnicos.",
        "stock": 45,
        "es_destacado": False,
        "imagen": "productos/trailmaster-terrain.png",
        "color": "Oliva",
        "material": "Textil reforzado",
    },
    {
        "nombre": "ZenWalk Studio",
        "categoria": "Training Studio",
        "marca": "ZenWalk",
        "precio": "99.00",
        "precio_oferta": "89.00",
        "descripcion": "Suela plana y talón estabilizado para rutinas HIIT.",
        "stock": 70,
        "es_destacado": True,
        "imagen": "productos/zenwalk-studio.png",
        "color": "Lavanda",
        "material": "Neopreno",
    },
    {
        "nombre": "ZenWalk Flex",
        "categoria": "Training Studio",
        "marca": "ZenWalk",
        "precio": "109.00",
        "precio_oferta": None,
        "descripcion": "Upper tipo calcetín con soporte en el mediopié.",
        "stock": 65,
        "es_destacado": False,
        "imagen": "productos/zenwalk-flex.png",
        "color": "Negro",
        "material": "Tejido elástico",
    },
    {
        "nombre": "AeroRun Pulse",
        "categoria": "Running Profesional",
        "marca": "AeroRun",
        "precio": "132.00",
        "precio_oferta": "118.00",
        "descripcion": "Perfil rocker para mantener el ritmo en rodajes tempo.",
        "stock": 60,
        "es_destacado": False,
        "imagen": "productos/aerorun-pulse.png",
        "color": "Coral",
        "material": "Engineered mesh",
    },
    {
        "nombre": "UrbanStep Metro",
        "categoria": "Street Icon",
        "marca": "UrbanStep",
        "precio": "95.00",
        "precio_oferta": None,
        "descripcion": "Chunky sole y paneles reflectantes para la noche urbana.",
        "stock": 50,
        "es_destacado": True,
        "imagen": "productos/urbanstep-metro.png",
        "color": "Negro / Gris",
        "material": "Sintético y TPU",
    },
    {
        "nombre": "TrailMaster Ridge",
        "categoria": "Trail Técnico",
        "marca": "TrailMaster",
        "precio": "155.00",
        "precio_oferta": None,
        "descripcion": "Placa protectora y drop reducido para rutas técnicas.",
        "stock": 40,
        "es_destacado": False,
        "imagen": "productos/trailmaster-ridge.png",
        "color": "Rojo",
        "material": "Microfibra",
    },
]


class Command(BaseCommand):
    help = "Carga datos de prueba coherentes con el mapa de navegación y con imágenes reales."

    def handle(self, *args, **options):
        self.stdout.write("Creando datos de prueba...")
        categoria_map = self._ensure_navigation()
        marca_objs = self._ensure_marcas(["AeroRun", "UrbanStep", "TrailMaster", "ZenWalk"])
        self._seed_products(categoria_map, marca_objs)
        self._cleanup_legacy_categories()
        self._ensure_images_for_all_products()
        self._ensure_tallas_for_all_products()
        self._seed_cliente_demo()
        self.stdout.write(self.style.SUCCESS("Datos de ejemplo creados correctamente."))

    def _ensure_navigation(self):
        categoria_map = {}
        for bloque in CATALOG_STRUCTURE:
            dep_cfg = bloque["departamento"]
            departamento, _ = Departamento.objects.update_or_create(
                nombre=dep_cfg["nombre"],
                defaults={
                    "descripcion": dep_cfg["descripcion"],
                    "orden": dep_cfg["orden"],
                },
            )

            for seccion_cfg in bloque["secciones"]:
                seccion, _ = Seccion.objects.update_or_create(
                    departamento=departamento,
                    nombre=seccion_cfg["nombre"],
                    defaults={
                        "descripcion": seccion_cfg["descripcion"],
                        "orden": seccion_cfg["orden"],
                    },
                )

                for categoria_cfg in seccion_cfg["categorias"]:
                    categoria, _ = Categoria.objects.update_or_create(
                        seccion=seccion,
                        nombre=categoria_cfg["nombre"],
                        defaults={"descripcion": categoria_cfg["descripcion"]},
                    )
                    categoria_map[categoria.nombre] = categoria

        return categoria_map

    @staticmethod
    def _ensure_marcas(nombres):
        marca_objs = {}
        for nombre in nombres:
            marca_objs[nombre], _ = Marca.objects.get_or_create(nombre=nombre)
        return marca_objs

    def _seed_products(self, categoria_map, marca_objs):
        for data in PRODUCTS_DATA:
            categoria = categoria_map.get(data["categoria"])
            marca = marca_objs.get(data["marca"])
            if not categoria or not marca:
                self.stderr.write(
                    f"⚠️  No se encontró la categoría o marca para {data['nombre']}. Se omite."
                )
                continue

            producto, _ = Producto.objects.update_or_create(
                nombre=data["nombre"],
                defaults={
                    "descripcion": data["descripcion"],
                    "precio": Decimal(data["precio"]),
                    "precio_oferta": (
                        Decimal(data["precio_oferta"])
                        if data["precio_oferta"]
                        else None
                    ),
                    "stock": data["stock"],
                    "marca": marca,
                    "categoria": categoria,
                    "es_destacado": data["es_destacado"],
                    "color": data.get("color"),
                    "material": data.get("material"),
                },
            )

            self._ensure_imagen_producto(producto, data.get("imagen"))
            self._sync_tallas(producto)

        self.stdout.write("Productos sincronizados.")

    def _ensure_imagen_producto(self, producto, relative_path):
        imagen_obj = ImagenProducto.objects.filter(producto=producto).first()
        if not imagen_obj:
            imagen_obj = ImagenProducto(producto=producto)

        if relative_path and default_storage.exists(relative_path):
            if imagen_obj.imagen.name != relative_path:
                imagen_obj.imagen.name = relative_path
            imagen_obj.es_principal = True
            imagen_obj.save()
            return

        placeholder_name = f"{slugify(producto.nombre)}.png"
        content = ContentFile(base64.b64decode(PLACEHOLDER_IMAGE))
        imagen_obj.imagen.save(placeholder_name, content, save=False)
        imagen_obj.es_principal = True
        imagen_obj.save()

    def _ensure_images_for_all_products(self):
        productos = Producto.objects.all()
        created = 0
        for producto in productos:
            if producto.imagenes.exists():
                continue

            relative_path = self._find_existing_media(producto)
            if relative_path:
                ImagenProducto.objects.create(
                    producto=producto,
                    imagen=relative_path,
                    es_principal=True,
                )
                created += 1
                continue

            placeholder = ContentFile(
                base64.b64decode(PLACEHOLDER_IMAGE),
                name=f"{slugify(producto.nombre)}.png",
            )
            ImagenProducto.objects.create(
                producto=producto,
                imagen=placeholder,
                es_principal=True,
            )
            created += 1

        if created:
            self.stdout.write(f"Se añadieron imágenes faltantes a {created} productos.")

    def _find_existing_media(self, producto):
        candidates = []
        override = IMAGE_OVERRIDES.get(producto.nombre)
        if override:
            candidates.append(override)

        simple = producto.nombre.replace(" ", "_")
        candidates.extend(
            [
                f"productos/{simple}.jpg",
                f"productos/{simple}.png",
                f"productos/{simple}.jpeg",
                f"productos/{slugify(producto.nombre)}.jpg",
                f"productos/{slugify(producto.nombre)}.png",
            ]
        )

        for candidate in candidates:
            if default_storage.exists(candidate):
                return candidate
        return None

    def _ensure_tallas_for_all_products(self):
        updated = 0
        for producto in Producto.objects.select_related("categoria"):
            if self._sync_tallas(producto):
                updated += 1
        if updated:
            self.stdout.write(f"Tallas sincronizadas para {updated} productos.")

    def _sync_tallas(self, producto):
        categoria = producto.categoria.nombre if producto.categoria else None
        tallas = TALLA_SETS.get(categoria) or DEFAULT_TALLAS
        if not tallas:
            return False

        existing = set(producto.tallas.values_list("talla", flat=True))
        target = set(tallas)
        changed = False

        stock = self._stock_por_categoria(categoria)
        for talla in tallas:
            _, created = TallaProducto.objects.update_or_create(
                producto=producto,
                talla=talla,
                defaults={"stock": stock},
            )
            if created:
                changed = True

        sobrantes = existing - target
        if sobrantes:
            producto.tallas.filter(talla__in=sobrantes).delete()
            changed = True

        return changed

    @staticmethod
    def _stock_por_categoria(categoria_nombre):
        if categoria_nombre in {"Running Profesional", "Trail Técnico"}:
            return 24
        if categoria_nombre in {"Casual Premium", "Street Icon"}:
            return 30
        if categoria_nombre == "Slides & Verano":
            return 40
        return 18

    def _cleanup_legacy_categories(self):
        qs = Categoria.objects.filter(nombre__in=LEGACY_CATEGORY_NAMES, seccion__isnull=True)
        removed = qs.count()
        if removed:
            qs.delete()
            self.stdout.write(f"Se eliminaron {removed} categorías heredadas sin sección.")

    def _seed_cliente_demo(self):
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
