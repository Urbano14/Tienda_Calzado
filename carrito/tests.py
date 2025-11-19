from decimal import Decimal

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from productos.models import Producto, Marca, Categoria, TallaProducto
from .models import ItemCarrito
from .utils import obtener_o_crear_carrito


class CarritoModelTestCase(TestCase):
    def setUp(self):
        marca = Marca.objects.create(nombre="Marca Test")
        categoria = Categoria.objects.create(nombre="Deporte")
        self.producto = Producto.objects.create(
            nombre="Zapatilla Test",
            precio="100.00",
            precio_oferta="80.00",
            marca=marca,
            categoria=categoria,
            stock=10,
        )
        request = self.client.get("/").wsgi_request
        carrito = obtener_o_crear_carrito(request)
        self.item = ItemCarrito.objects.create(
            carrito=carrito,
            producto=self.producto,
            cantidad=2,
        )

    def test_itemcarrito_subtotal_usa_precio_oferta(self):
        self.assertEqual(self.item.obtener_subtotal, Decimal("160.00"))


class CarritoViewsTestCase(TestCase):
    def setUp(self):
        marca = Marca.objects.create(nombre="Marca View")
        categoria = Categoria.objects.create(nombre="Casual")
        self.producto = Producto.objects.create(
            nombre="Slip On",
            precio="70.00",
            precio_oferta="50.00",
            marca=marca,
            categoria=categoria,
            stock=5,
        )
        self.url_agregar = reverse("agregar-al-carrito", args=[self.producto.id])

    def test_agregar_producto_respeta_stock_total(self):
        response = self.client.post(self.url_agregar, {"cantidad": 10}, follow=True)
        self.assertFalse(ItemCarrito.objects.exists())
        self.assertRedirects(response, reverse("detalle-producto", args=[self.producto.id]))
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("No hay más stock" in msg for msg in mensajes))

    def test_agregar_agota_stock_actualiza_disponibilidad(self):
        producto = Producto.objects.create(
            nombre="Runner",
            precio="50.00",
            marca=self.producto.marca,
            categoria=self.producto.categoria,
            stock=2,
        )
        url = reverse("agregar-al-carrito", args=[producto.id])
        self.client.post(url, {"cantidad": 2}, follow=True)
        item = ItemCarrito.objects.get(producto=producto)
        self.assertEqual(item.cantidad, 2)
        producto.refresh_from_db()
        self.assertEqual(producto.stock, 0)
        self.assertFalse(producto.esta_disponible)

    def test_agregar_producto_sin_stock_no_crea_item(self):
        self.producto.stock = 0
        self.producto.save()
        response = self.client.post(self.url_agregar, {"cantidad": 1}, follow=True)
        self.assertFalse(ItemCarrito.objects.exists())
        self.assertRedirects(response, reverse("detalle-producto", args=[self.producto.id]))
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("No hay más stock" in msg for msg in mensajes))

    def test_agregar_producto_con_talla_respeta_stock_de_talla(self):
        TallaProducto.objects.create(producto=self.producto, talla="42", stock=2)
        response = self.client.post(self.url_agregar, {"cantidad": 5, "talla": "42"}, follow=True)
        self.assertFalse(ItemCarrito.objects.exists())
        self.assertRedirects(response, reverse("detalle-producto", args=[self.producto.id]))

    def test_actualizar_cantidad_no_supera_stock(self):
        # Añadir primero 2 unidades
        self.client.post(self.url_agregar, {"cantidad": 2})
        item = ItemCarrito.objects.get()
        url_actualizar = reverse("actualizar-cantidad", args=[item.id])

        response = self.client.post(url_actualizar, {"cantidad": 10}, follow=True)
        item.refresh_from_db()
        self.assertEqual(item.cantidad, 5)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("Cantidad ajustada a 5" in msg for msg in mensajes))
