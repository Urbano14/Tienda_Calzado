from decimal import Decimal
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from productos.models import Producto, Marca, Categoria
from pedidos.models import Pedido, ItemPedido
from pedidos.checkout_views import DetallesEntregaForm, ConfirmacionCompraView

User = get_user_model()


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
            estado=Pedido.Estados.PROCESANDO,
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
        self.assertEqual(data["estado"], Pedido.Estados.PROCESANDO)

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

    def test_pedido_asignado_requiere_propietario(self):
        user = User.objects.create_user(username="propietario", password="test123")
        pedido_propietario = Pedido.objects.create(
            numero_pedido="OWNER1",
            estado=Pedido.Estados.PROCESANDO,
            subtotal=Decimal("10"),
            impuestos=Decimal("2"),
            coste_entrega=Decimal("1"),
            descuento=Decimal("0"),
            total=Decimal("13"),
            metodo_pago=Pedido.MetodosPago.TARJETA,
            direccion_envio="Calle",
            telefono="600000000",
            cliente=user,
        )

        resp_anon = self.client.get(f"/api/pedidos/{pedido_propietario.numero_pedido}/")
        self.assertEqual(resp_anon.status_code, 403)

        otro = User.objects.create_user(username="intruso", password="test123")
        self.client.force_login(otro)
        resp_otro = self.client.get(f"/api/pedidos/{pedido_propietario.numero_pedido}/")
        self.assertEqual(resp_otro.status_code, 403)
        self.client.logout()

        self.client.force_login(user)
        resp_owner = self.client.get(f"/api/pedidos/{pedido_propietario.numero_pedido}/")
        self.assertEqual(resp_owner.status_code, 200)


class DetallesEntregaFormTests(TestCase):
    def setUp(self):
        self.base_data = {
            "nombre": "Juan",
            "apellidos": "Pérez",
            "email": "juan@example.com",
            "telefono": "+34666000111",
            "direccion": "Calle Luna",
            "numero": "12",
            "piso": "3B",
            "ciudad": "Sevilla",
            "provincia": "Sevilla",
            "codigo_postal": "41012",
            "pais": "España",
            "referencias": "Llamar al llegar",
        }

    def test_form_valido_con_direccion_completa(self):
        form = DetallesEntregaForm(data=self.base_data)
        self.assertTrue(form.is_valid())

    def test_cp_invalido_generates_error(self):
        data = self.base_data.copy()
        data["codigo_postal"] = "ABC12"
        form = DetallesEntregaForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("codigo_postal", form.errors)

    def test_telefono_invalido_generates_error(self):
        data = self.base_data.copy()
        data["telefono"] = "123"
        form = DetallesEntregaForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("telefono", form.errors)


class DireccionFormateadaTests(TestCase):
    def test_formatea_todos_los_componentes(self):
        data = {
            "direccion": "Avenida Andalucía",
            "numero": "45",
            "piso": "5º D",
            "codigo_postal": "41011",
            "ciudad": "Sevilla",
            "provincia": "Sevilla",
            "pais": "España",
            "referencias": "Dejar en portería",
        }

        direccion = ConfirmacionCompraView._direccion_formateada(data)

        self.assertIn("Avenida Andalucía 45", direccion)
        self.assertIn("41011", direccion)
        self.assertIn("Sevilla", direccion)
        self.assertIn("Referencias", direccion)


class SeguimientoPedidoViewTests(TestCase):
    def setUp(self):
        marca = Marca.objects.create(nombre="Tracking Brand")
        categoria = Categoria.objects.create(nombre="Tracking Shoes")
        producto = Producto.objects.create(
            nombre="Trace Runner",
            precio=Decimal("90.00"),
            categoria=categoria,
            marca=marca,
        )
        self.pedido = Pedido.objects.create(
            numero_pedido="TRACK001",
            estado=Pedido.Estados.PENDIENTE,
            subtotal=Decimal("90.00"),
            impuestos=Decimal("18.90"),
            coste_entrega=Decimal("4.99"),
            descuento=Decimal("0.00"),
            total=Decimal("113.89"),
            metodo_pago=Pedido.MetodosPago.CONTRAREEMBOLSO,
            direccion_envio="Calle Seguimiento 123",
            telefono="600000111",
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            producto=producto,
            talla="41",
            cantidad=1,
            precio_unitario=Decimal("90.00"),
            total=Decimal("90.00"),
        )

    def test_seguimiento_publico_muestra_pedido(self):
        url = reverse("seguimiento_pedido", args=[self.pedido.tracking_token])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Seguimiento del pedido")
        self.assertContains(resp, self.pedido.numero_pedido)
        self.assertContains(resp, self.pedido.direccion_envio)

    def test_token_invalido_devuelve_404(self):
        url = reverse("seguimiento_pedido", args=[uuid.uuid4()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
