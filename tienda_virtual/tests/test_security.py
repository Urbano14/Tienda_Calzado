from django.conf import settings
from django.test import SimpleTestCase


class SecuritySettingsTests(SimpleTestCase):
    def test_password_validators_include_minimum_and_common_checks(self):
        names = {validator["NAME"] for validator in settings.AUTH_PASSWORD_VALIDATORS}
        self.assertIn(
            "django.contrib.auth.password_validation.MinimumLengthValidator",
            names,
            "Se requiere el validador de longitud mínima para contraseñas.",
        )
        self.assertIn(
            "django.contrib.auth.password_validation.CommonPasswordValidator",
            names,
            "Se requiere el validador de contraseñas comunes para reducir ataques de diccionario.",
        )

    def test_https_flags_follow_force_https_toggle(self):
        self.assertEqual(settings.SECURE_SSL_REDIRECT, settings.FORCE_HTTPS)
        self.assertEqual(settings.SESSION_COOKIE_SECURE, settings.FORCE_HTTPS)
        self.assertEqual(settings.CSRF_COOKIE_SECURE, settings.FORCE_HTTPS)
        self.assertEqual(settings.SECURE_HSTS_INCLUDE_SUBDOMAINS, settings.FORCE_HTTPS)
        self.assertEqual(settings.SECURE_HSTS_PRELOAD, settings.FORCE_HTTPS)
        self.assertEqual(settings.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))
