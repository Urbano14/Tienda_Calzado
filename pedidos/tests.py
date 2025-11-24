from django.test import TestCase

# Create your tests here.
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from productos.models import Producto, Marca, Categoria
from pedidos.models import Pedido, ItemPedido


class PedidoPublicAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Datos mínimos de productos
        marca = Marca.objects.create(nombre="Marca Test")
        categoria = Categoria.objects.create(nombre="Zapatillas")
        producto = Producto.objects.create(
            nombre="Zapatilla X",
            precio=Decimal("59.90"),
            categoria=categoria,
            marca=marca,
        )

        # Pedido con items
        self.pedido = Pedido.objects.create(
            numero_pedido="TEST123",
            estado=Pedido.Estados.PREPARANDO,
            subtotal=Decimal("59.90"),
            impuestos=Decimal("12.58"),
            coste_entrega=Decimal("3.99"),
            descuento=Decimal("0.00"),
            total=Decimal("76.47"),
            metodo_pago=Pedido.MetodosPago.TARJETA,
            direccion_envio="Calle Falsa 123",
            telefono="600000000",
        )

        ItemPedido.objects.create(
            pedido=self.pedido,
            producto=producto,
            talla="42",
            cantidad=1,
            precio_unitario=Decimal("59.90"),
            total=Decimal("59.90"),
        )

    def test_pedido_publico_devuelve_200_y_datos_basicos(self):
        url = f"/api/pedidos/{self.pedido.numero_pedido}/"
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Campos principales esperados
        for campo in [
            "numero_pedido",
            "fecha_creacion",
            "estado",
            "subtotal",
            "impuestos",
            "coste_entrega",
            "descuento",
            "total",
            "items",
        ]:
            self.assertIn(campo, data)

        self.assertEqual(data["numero_pedido"], "TEST123")
        self.assertEqual(data["estado"], Pedido.Estados.PREPARANDO)

        # Items
        self.assertIsInstance(data["items"], list)
        self.assertEqual(len(data["items"]), 1)
        item = data["items"][0]
        self.assertEqual(item["cantidad"], 1)
        self.assertEqual(item["talla"], "42")
        self.assertIn("producto_nombre", item)

    def test_pedido_publico_no_incluye_datos_sensibles(self):
        """
        Verifica que el endpoint no expone datos personales del cliente
        ni campos de contacto o pago.
        """
        url = f"/api/pedidos/{self.pedido.numero_pedido}/"
        resp = self.client.get(url)

        data = resp.json()

        campos_no_permitidos = {
            "cliente",
            "direccion_envio",
            "telefono",
            "metodo_pago",
            "email",
        }
        self.assertTrue(campos_no_permitidos.isdisjoint(data.keys()))

    def test_pedido_inexistente_da_404(self):
        url = "/api/pedidos/NO_EXISTE_999/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
