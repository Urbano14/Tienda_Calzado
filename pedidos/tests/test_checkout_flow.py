from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from carrito.models import Carrito, ItemCarrito
from pedidos.models import Pedido
from productos.models import Categoria, Marca, Producto


class PedidoCreateAPITests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.marca = Marca.objects.create(nombre="Marca API")
        self.categoria = Categoria.objects.create(nombre="Zapatillas API")
        self.producto = Producto.objects.create(
            nombre="Modelo API",
            precio=Decimal("45.00"),
            categoria=self.categoria,
            marca=self.marca,
            stock=10,
        )

    def _preparar_carrito(self):
        carrito = Carrito.objects.create()
        ItemCarrito.objects.create(carrito=carrito, producto=self.producto, cantidad=2)
        session = self.api_client.session
        session["guest_carrito_id"] = carrito.id
        session.save()
        return carrito

    def test_invitado_puede_generar_pedido_via_api(self):
        self._preparar_carrito()
        payload = {
            "metodo_pago": Pedido.MetodosPago.CONTRAREEMBOLSO,
            "direccion_envio": "Calle API 123",
            "telefono": "+34111222333",
            "datos_cliente": {
                "nombre": "Ana",
                "apellidos": "Invitada",
                "email": "ana@example.com",
                "telefono": "+34111222333",
                "direccion": "Calle API 123",
                "ciudad": "Madrid",
                "codigo_postal": "28080",
                "password": "",
            },
        }
        url = reverse("pedidos:api-pedidos-create")
        response = self.api_client.post(url, payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Pedido.objects.count(), 1)
        pedido = Pedido.objects.first()
        self.assertEqual(pedido.metodo_pago, Pedido.MetodosPago.CONTRAREEMBOLSO)
        self.assertIsNone(pedido.cliente)
        self.assertEqual(pedido.items.count(), 1)
        self.assertEqual(pedido.items.first().cantidad, 2)

    def test_api_rechaza_invitado_sin_datos_cliente(self):
        self._preparar_carrito()
        payload = {
            "metodo_pago": Pedido.MetodosPago.CONTRAREEMBOLSO,
            "direccion_envio": "Sin datos",
            "telefono": "+34111222333",
        }
        url = reverse("pedidos:api-pedidos-create")
        response = self.api_client.post(url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("datos_cliente", response.json())
        self.assertEqual(Pedido.objects.count(), 0)


class GuestCheckoutFlowTests(TestCase):
    def setUp(self):
        marca = Marca.objects.create(nombre="Marca UX")
        categoria = Categoria.objects.create(nombre="Zapatillas UX")
        self.producto = Producto.objects.create(
            nombre="Modelo UX",
            precio=Decimal("80.00"),
            categoria=categoria,
            marca=marca,
            stock=5,
        )

    def _seed_carrito(self):
        carrito = Carrito.objects.create()
        ItemCarrito.objects.create(carrito=carrito, producto=self.producto, cantidad=1)
        session = self.client.session
        session["guest_carrito_id"] = carrito.id
        session.save()

    def test_checkout_rapido_invitado_contrareembolso(self):
        self._seed_carrito()
        entrega_data = {
            "nombre": "Luis",
            "apellidos": "Rapido",
            "email": "luis@example.com",
            "telefono": "+34999000111",
            "direccion": "Calle Prisa",
            "numero": "10",
            "piso": "",
            "ciudad": "Sevilla",
            "provincia": "Sevilla",
            "codigo_postal": "41012",
            "pais": "España",
            "referencias": "",
        }

        resp_entrega = self.client.post(reverse("pedidos:checkout_entrega"), entrega_data)
        self.assertEqual(resp_entrega.status_code, 302)
        self.assertEqual(resp_entrega.url, reverse("pedidos:checkout_pago"))

        pago_data = {
            "metodo_pago": Pedido.MetodosPago.CONTRAREEMBOLSO,
            "referencia_pago": "",
        }
        resp_pago = self.client.post(reverse("pedidos:checkout_pago"), pago_data)
        self.assertEqual(resp_pago.status_code, 302)
        self.assertEqual(resp_pago.url, reverse("pedidos:checkout_confirmacion"))

        resp_confirm = self.client.get(reverse("pedidos:checkout_confirmacion"))
        self.assertEqual(resp_confirm.status_code, 200)
        pedido = resp_confirm.context["pedido"]
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido.metodo_pago, Pedido.MetodosPago.CONTRAREEMBOLSO)
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertIsNone(pedido.cliente)
        self.assertIn(pedido.numero_pedido, resp_confirm.content.decode())
