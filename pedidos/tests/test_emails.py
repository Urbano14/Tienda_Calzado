from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from productos.models import Producto, Marca, Categoria
from pedidos.emails import enviar_confirmacion_pedido
from pedidos.models import Pedido, ItemPedido

User = get_user_model()


class EnviarConfirmacionPedidoTests(TestCase):
    def setUp(self):
        marca = Marca.objects.create(nombre="Mailer")
        categoria = Categoria.objects.create(nombre="Running")
        self.producto = Producto.objects.create(
            nombre="Modelo Email",
            precio=Decimal("80.00"),
            categoria=categoria,
            marca=marca,
            stock=5,
        )
        self.pedido = Pedido.objects.create(
            numero_pedido="MAIL123",
            estado=Pedido.Estados.PENDIENTE,
            subtotal=Decimal("80.00"),
            impuestos=Decimal("16.80"),
            coste_entrega=Decimal("5.00"),
            descuento=Decimal("0.00"),
            total=Decimal("101.80"),
            metodo_pago=Pedido.MetodosPago.TARJETA,
            direccion_envio="Calle Email 42, Sevilla",
            telefono="600000000",
            email_contacto="cliente@example.com",
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            talla="42",
            cantidad=1,
            precio_unitario=Decimal("80.00"),
            total=Decimal("80.00"),
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_envia_email_conteniendo_datos_clave(self):
        enviado = enviar_confirmacion_pedido(self.pedido, "cliente@example.com")

        self.assertTrue(enviado)
        self.assertEqual(len(mail.outbox), 1)
        mensaje = mail.outbox[0]
        self.assertEqual(mensaje.to, ["cliente@example.com"])
        self.assertTrue(mensaje.alternatives)
        html = mensaje.alternatives[0][0]
        self.assertIn(self.pedido.numero_pedido, html)
        self.assertIn(str(self.pedido.total), html)
        self.assertIn(self.pedido.direccion_envio, html)
        self.assertIn(self.producto.nombre, html)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    @mock.patch("pedidos.emails.EmailMultiAlternatives.send", side_effect=Exception("SMTP down"))
    def test_captura_excepcion_y_no_rompe_el_flujo(self, mock_send):
        enviado = enviar_confirmacion_pedido(self.pedido, "cliente@example.com")

        self.assertFalse(enviado)
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(mock_send.called)


class CheckoutEmailFlowTests(TestCase):
    def setUp(self):
        marca = Marca.objects.create(nombre="Checkout Brand")
        categoria = Categoria.objects.create(nombre="Street")
        self.producto = Producto.objects.create(
            nombre="Checkout Runner",
            precio=Decimal("120.00"),
            categoria=categoria,
            marca=marca,
            stock=10,
        )

    def _agregar_producto_al_carrito(self):
        url = reverse("agregar-al-carrito", args=[self.producto.id])
        resp = self.client.post(url, {"cantidad": 1})
        self.assertEqual(resp.status_code, 302)

    def _completar_entrega(self):
        data = {
            "nombre": "Lucia",
            "apellidos": "Gomez",
            "email": "lucia@example.com",
            "telefono": "+34666000111",
            "direccion": "Calle Flores",
            "numero": "12",
            "piso": "3B",
            "ciudad": "Sevilla",
            "provincia": "Sevilla",
            "codigo_postal": "41012",
            "pais": "Espana",
            "referencias": "Llamar al llegar",
        }
        resp = self.client.post(reverse("pedidos:checkout_entrega"), data)
        self.assertEqual(resp.status_code, 302)

    def _completar_pago(self):
        data = {
            "metodo_pago": Pedido.MetodosPago.TARJETA,
            "referencia_pago": "4242",
        }
        resp = self.client.post(reverse("pedidos:checkout_pago"), data)
        self.assertEqual(resp.status_code, 302)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_checkout_completo_envia_email(self):
        self._agregar_producto_al_carrito()
        self._completar_entrega()
        self._completar_pago()

        resp = self.client.get(reverse("pedidos:checkout_confirmacion"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    @mock.patch("pedidos.emails.EmailMultiAlternatives.send", side_effect=Exception("SMTP down"))
    def test_checkout_no_falla_si_el_email_da_error(self, mock_send):
        self._agregar_producto_al_carrito()
        self._completar_entrega()
        self._completar_pago()

        resp = self.client.get(reverse("pedidos:checkout_confirmacion"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(mock_send.called)
