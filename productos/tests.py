import shutil
import tempfile
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Categoria,
    Departamento,
    ImagenProducto,
    Marca,
    Producto,
    Seccion,
    TallaProducto,
)


class MediaRootMixin:
    """Isolate MEDIA_ROOT so file-based fields do not leak to the real filesystem."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._temp_media_dir = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._temp_media_dir)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._temp_media_dir, ignore_errors=True)
        super().tearDownClass()


class ProductoAPITestCase(MediaRootMixin, APITestCase):
    def setUp(self):
        self.marca = Marca.objects.create(nombre="Test Brand")
        self.otro_marca = Marca.objects.create(nombre="City Brand")
        self.departamento = Departamento.objects.create(nombre="Colección Test")
        self.otra_departamento = Departamento.objects.create(
            nombre="Colección Alterna"
        )
        self.seccion = Seccion.objects.create(
            nombre="Rendimiento", departamento=self.departamento
        )
        self.otra_seccion = Seccion.objects.create(
            nombre="Urbano", departamento=self.otra_departamento
        )
        self.categoria = Categoria.objects.create(nombre="Running", seccion=self.seccion)
        self.otra_categoria = Categoria.objects.create(
            nombre="Basket", seccion=self.otra_seccion
        )

        self.producto = Producto.objects.create(
            nombre="Zapatilla Pro",
            descripcion="Pensada para larga distancia",
            precio="120.00",
            precio_oferta="99.00",
            marca=self.marca,
            categoria=self.categoria,
            color="Azul",
            material="Malla",
            stock=10,
        )
        self.otro_producto = Producto.objects.create(
            nombre="Zapatilla Urbana",
            descripcion="Para uso diario",
            precio="80.00",
            marca=self.otro_marca,
            categoria=self.otra_categoria,
            stock=3,
        )

        ImagenProducto.objects.create(
            producto=self.producto,
            imagen=self._image_file("principal.jpg"),
            es_principal=True,
        )
        TallaProducto.objects.create(producto=self.producto, talla="42", stock=5)

    def _image_file(self, name):
        return SimpleUploadedFile(name, b"fake image content", content_type="image/jpeg")

    def test_product_list_endpoint_returns_nested_resources(self):
        url = reverse("api-productos")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        producto_data = next(
            item for item in response.data if item["id"] == self.producto.id
        )
        self.assertEqual(producto_data["categoria"]["nombre"], self.categoria.nombre)
        self.assertEqual(producto_data["marca"]["nombre"], self.marca.nombre)
        self.assertEqual(producto_data["tallas"][0]["talla"], "42")
        self.assertGreaterEqual(len(producto_data["imagenes"]), 1)

    def test_product_detail_endpoint_returns_single_product(self):
        url = reverse("api-producto-detalle", args=[self.producto.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.producto.id)
        self.assertEqual(response.data["categoria"]["nombre"], self.categoria.nombre)

    def test_category_list_endpoint_returns_all_categories(self):
        url = reverse("api-categorias")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nombres = {categoria["nombre"] for categoria in response.data}
        self.assertSetEqual(nombres, {"Running", "Basket"})

    def test_product_list_endpoint_filters_by_nombre(self):
        url = reverse("api-productos")
        response = self.client.get(url, {"nombre": "Pro"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.producto.id)

    def test_product_list_endpoint_filters_by_departamento(self):
        url = reverse("api-productos")
        response = self.client.get(
            url, {"departamento": self.departamento.slug}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data}
        self.assertIn(self.producto.id, ids)
        self.assertNotIn(self.otro_producto.id, ids)

    def test_product_list_endpoint_filters_by_seccion(self):
        url = reverse("api-productos")
        response = self.client.get(url, {"seccion": self.seccion.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data}
        self.assertEqual(ids, {self.producto.id})

    def test_product_list_endpoint_filters_by_fabricante(self):
        url = reverse("api-productos")
        response = self.client.get(url, {"fabricante": self.marca.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data}
        self.assertEqual(ids, {self.producto.id})

    def test_product_list_endpoint_allows_advanced_search(self):
        url = reverse("api-productos")

        response = self.client.get(url, {"q": self.seccion.nombre})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data}
        self.assertEqual(ids, {self.producto.id})

        response = self.client.get(url, {"q": self.otro_marca.nombre})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data}
        self.assertEqual(ids, {self.otro_producto.id})


class ProductoViewsTestCase(MediaRootMixin, TestCase):
    def setUp(self):
        self.marca = Marca.objects.create(nombre="Marca Vista")
        self.departamento = Departamento.objects.create(nombre="Colección Vista Test")
        self.otra_departamento = Departamento.objects.create(nombre="Colección Urbana Test")
        self.seccion = Seccion.objects.create(nombre="Trail", departamento=self.departamento)
        self.otra_seccion = Seccion.objects.create(
            nombre="Lifestyle", departamento=self.otra_departamento
        )
        self.categoria = Categoria.objects.create(nombre="Trail", seccion=self.seccion)
        self.otra_categoria = Categoria.objects.create(
            nombre="Lifestyle", seccion=self.otra_seccion
        )

        self.producto = Producto.objects.create(
            nombre="Trail Runner",
            descripcion="Grip superior",
            precio="150.00",
            marca=self.marca,
            categoria=self.categoria,
            stock=8,
        )
        self.otro = Producto.objects.create(
            nombre="City Walk",
            descripcion="Urbano y cómodo",
            precio="90.00",
            marca=self.marca,
            categoria=self.otra_categoria,
            stock=2,
        )

        ImagenProducto.objects.create(
            producto=self.producto,
            imagen=self._image_file("vista.jpg"),
            es_principal=True,
        )

    def _image_file(self, name):
        return SimpleUploadedFile(name, b"fake image content", content_type="image/jpeg")

    def test_lista_productos_view_renders_and_filters(self):
        url = reverse("lista-productos")

        response = self.client.get(url)
        self.assertContains(response, "Trail Runner")
        self.assertContains(response, "City Walk")

        response_filtrado = self.client.get(url, {"categoria": self.categoria.slug})
        self.assertContains(response_filtrado, "Trail Runner")
        self.assertNotContains(response_filtrado, "City Walk")

    def test_lista_productos_view_accepts_departamento_and_marca_filters(self):
        url = reverse("lista-productos")

        response_departamento = self.client.get(url, {"departamento": self.departamento.slug})
        self.assertContains(response_departamento, "Trail Runner")
        self.assertNotContains(response_departamento, "City Walk")

        response_marca = self.client.get(url, {"fabricante": self.marca.slug})
        self.assertContains(response_marca, "Trail Runner")
        self.assertContains(response_marca, "City Walk")

    def test_detalle_producto_view_renders_information(self):
        url = reverse("detalle-producto", args=[self.producto.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trail Runner")
        self.assertContains(response, "Grip superior")
        self.assertContains(response, self.categoria.nombre)


class ProductoModelTestCase(MediaRootMixin, TestCase):
    def setUp(self):
        marca = Marca.objects.create(nombre="Marca Modelo")
        departamento = Departamento.objects.create(nombre="Colección Modelo")
        seccion = Seccion.objects.create(nombre="Performance", departamento=departamento)
        categoria = Categoria.objects.create(nombre="Performance", seccion=seccion)
        self.producto = Producto.objects.create(
            nombre="Speedster",
            descripcion="Modelo ligero",
            precio="110.00",
            marca=marca,
            categoria=categoria,
            stock=4,
        )

    def _image_file(self, name):
        return SimpleUploadedFile(name, b"fake image content", content_type="image/jpeg")

    def test_imagen_destacada_returns_unique_image(self):
        imagen = ImagenProducto.objects.create(
            producto=self.producto,
            imagen=self._image_file("unica.jpg"),
            es_principal=True,
        )

        self.assertEqual(self.producto.imagen_destacada, imagen)

    def test_segunda_imagen_levanta_error(self):
        ImagenProducto.objects.create(
            producto=self.producto,
            imagen=self._image_file("principal.jpg"),
            es_principal=True,
        )

        with self.assertRaises(ValidationError):
            ImagenProducto.objects.create(
                producto=self.producto,
                imagen=self._image_file("extra.jpg"),
                es_principal=False,
            )

    def test_disponibilidad_sigue_el_stock(self):
        self.producto.stock = 0
        self.producto.save()
        self.assertFalse(self.producto.esta_disponible)

        self.producto.stock = 3
        self.producto.save()
        self.assertTrue(self.producto.esta_disponible)

    def test_precio_vigente_prefiere_oferta(self):
        self.producto.precio_oferta = Decimal("90.00")
        self.producto.save()
        self.assertEqual(self.producto.precio_vigente, Decimal("90.00"))

        self.producto.precio_oferta = None
        self.producto.save()
        self.assertEqual(self.producto.precio_vigente, Decimal("110.00"))
