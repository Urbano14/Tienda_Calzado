from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from clientes.models import Cliente


class AutenticacionTests(APITestCase):
    def setUp(self):
        self.registro_url = "/api/registro/"
        self.login_url = "/api/login/"

    def test_registro_ok_devuelve_token(self):
        data = {"email": "cliente@correo.com", "password": "12345678"}
        response = self.client.post(self.registro_url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)
        self.assertEqual(response.data.get("email"), data["email"])
        self.assertTrue(Cliente.objects.filter(user__email=data["email"]).exists())

    def test_registro_email_duplicado(self):
        User.objects.create_user(
            username="cliente@correo.com",
            email="cliente@correo.com",
            password="12345678",
        )
        data = {"email": "CLIENTE@correo.com", "password": "12345678"}
        response = self.client.post(self.registro_url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)

    def test_login_ok_devuelve_token(self):
        user = User.objects.create_user(
            username="cliente@correo.com",
            email="cliente@correo.com",
            password="12345678",
        )
        Cliente.objects.create(user=user)

        response = self.client.post(
            self.login_url,
            {"email": "cliente@correo.com", "password": "12345678"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data.get("email"), "cliente@correo.com")
        self.assertTrue(Token.objects.filter(user=user).exists())

    def test_login_incorrecto(self):
        user = User.objects.create_user(
            username="cliente@correo.com",
            email="cliente@correo.com",
            password="12345678",
        )
        Cliente.objects.create(user=user)

        response = self.client.post(
            self.login_url,
            {"email": "cliente@correo.com", "password": "incorrecta"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data)
