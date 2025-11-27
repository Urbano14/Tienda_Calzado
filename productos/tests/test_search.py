from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from productos.models import Categoria, Departamento, Marca, Producto, Seccion


class BusquedaCatalogoTests(TestCase):
    def setUp(self):
        self.departamento = Departamento.objects.create(nombre="Deporte")
        self.otra_departamento = Departamento.objects.create(nombre="Lifestyle")

        self.seccion = Seccion.objects.create(
            departamento=self.departamento,
            nombre="Running",
        )
        self.otra_seccion = Seccion.objects.create(
            departamento=self.otra_departamento,
            nombre="Street",
        )

        self.categoria = Categoria.objects.create(
            seccion=self.seccion,
            nombre="Competición",
        )
        self.otra_categoria = Categoria.objects.create(
            seccion=self.otra_seccion,
            nombre="Casual",
        )

        self.marca_nike = Marca.objects.create(nombre="Nike")
        self.marca_adidas = Marca.objects.create(nombre="Adidas")

        self.prod_nike = Producto.objects.create(
            nombre="Nike Runner Pro",
            descripcion="Zapatilla ligera",
            precio=Decimal("120.00"),
            marca=self.marca_nike,
            categoria=self.categoria,
            stock=10,
        )
        self.prod_adidas = Producto.objects.create(
            nombre="Adidas Street Classic",
            descripcion="Modelo urbano",
            precio=Decimal("90.00"),
            marca=self.marca_adidas,
            categoria=self.otra_categoria,
            stock=5,
        )

        self.url = reverse("buscar-productos")

    def test_busqueda_por_nombre(self):
        response = self.client.get(self.url, {"q": "runner"})
        self.assertContains(response, self.prod_nike.nombre)
        self.assertNotContains(response, self.prod_adidas.nombre)

    def test_busqueda_por_texto_coincidiendo_departamento(self):
        response = self.client.get(self.url, {"q": "Deporte"})
        self.assertContains(response, self.prod_nike.nombre)
        self.assertNotContains(response, self.prod_adidas.nombre)

    def test_busqueda_por_texto_coincidiendo_fabricante(self):
        response = self.client.get(self.url, {"q": "Adidas"})
        self.assertContains(response, self.prod_adidas.nombre)
        self.assertNotContains(response, self.prod_nike.nombre)

    def test_busqueda_respecta_departamento_implicito(self):
        self.prod_adidas.descripcion = "Zapatilla casual para running urbano"
        self.prod_adidas.save()

        response = self.client.get(self.url, {"q": "running"})
        self.assertContains(response, self.prod_nike.nombre)
        self.assertNotContains(response, self.prod_adidas.nombre)

    def test_busqueda_por_departamento(self):
        response = self.client.get(self.url, {"departamento": self.departamento.slug})
        self.assertContains(response, self.prod_nike.nombre)
        self.assertNotContains(response, self.prod_adidas.nombre)

    def test_busqueda_por_seccion(self):
        response = self.client.get(self.url, {"seccion": self.seccion.slug})
        self.assertContains(response, self.prod_nike.nombre)
        self.assertNotContains(response, self.prod_adidas.nombre)

    def test_busqueda_por_fabricante(self):
        response = self.client.get(self.url, {"fabricante": self.marca_adidas.slug})
        self.assertContains(response, self.prod_adidas.nombre)
        self.assertNotContains(response, self.prod_nike.nombre)

    def test_busqueda_combinada(self):
        response = self.client.get(
            self.url,
            {"q": "runner", "departamento": self.departamento.slug, "fabricante": self.marca_nike.slug},
        )
        self.assertContains(response, self.prod_nike.nombre)
        self.assertNotContains(response, self.prod_adidas.nombre)
