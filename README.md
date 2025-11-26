Tienda de Calzado

Proyecto académico en Django para la asignatura de Planificación y Gestión de Proyectos Informáticos.

Guía rápida
1) Clonar el proyecto
- `git clone https://github.com/Urbano14/Tienda_Calzado.git`
- `cd Tienda_Calzado`

2) Entorno y dependencias
- `python -m venv .venv`
- `.\.venv\Scripts\activate`
- `pip install -r requirements.txt`

3) Ejecutar el servidor local
- `python manage.py migrate`
- `python manage.py loaddata productos`
- `python manage.py runserver`

Rutas disponibles
- Listado HTML de productos: http://127.0.0.1:8000/productos/
- Detalle de producto: http://127.0.0.1:8000/productos/<id>/
- Carrito de compra: http://127.0.0.1:8000/carrito/
- API REST - Productos: http://127.0.0.1:8000/api/productos/
- API REST - Categorias: http://127.0.0.1:8000/api/categorias/
- Panel de administración: http://127.0.0.1:8000/admin/
- Imágenes de productos: se sirven desde `media/` (versiónada en el repo). Si añades o cambias imágenes, súbelas a `media/productos/` y haz `git add media/`.
  - En despliegues sin servidor web estático dedicado, Django expone `MEDIA_URL` directamente (ver `tienda_virtual/urls.py`), así que con clonar y correr el server se deberían ver las fotos.

Testing
- Ejecutar toda la suite: `python manage.py test`
- Cubrimos: modelos y vistas/API de productos (stock, imagen destacada, precio vigente) y flujos del carrito (stock general y por talla, uso de precio_oferta, ajustes de cantidad y avisos).
- Antes de probar manualmente, arranca el server con `python manage.py runserver` y usa las rutas de arriba.
- Pruebas mínimas nuevas: `python manage.py test pedidos.tests.test_checkout_flow` (API y checkout de invitado) y `python manage.py test tienda_virtual.tests.test_security` para comprobar las políticas de seguridad.

Correo de confirmaci��n
- El checkout env��a un email real tras crear el pedido usando SMTP. Define estas variables de entorno antes de arrancar el server: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`/`EMAIL_USE_SSL` (1 �� 0) y `DEFAULT_FROM_EMAIL`.
- Si quieres volver al backend de consola para desarrollo, exporta `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`.

Flujo Git sugerido
- Crear rama: `git checkout -b feature/lo-que-sea`
- Guardar cambios: `git add . && git commit -m "feat: descripcion breve"`
- Subir: `git push origin feature/lo-que-sea` y abrir PR hacia main.

Normas rápidas
- No subir `.venv/`, `db.sqlite3` ni archivos temporales (ya están en `.gitignore`).
- Commits pequeños y claros; solo se fusiona a `main` código que funcione.
- Describir y seguir tareas en issues de GitHub.

Pagos con Stripe
- Variables obligatorias en `.env`: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` y opcionalmente `STRIPE_DEFAULT_CURRENCY` (por defecto `eur`). Sin esas claves la pantalla de confirmación mostrará un aviso y deshabilitará el pago con tarjeta.
- El checkout crea un `PaymentIntent` por pedido y solo envía el correo de confirmación cuando Stripe confirma el cobro (webhook `payment_intent.succeeded`).
- En local usa la CLI de Stripe: `stripe login` y luego `stripe listen --forward-to localhost:8000/pedidos/webhooks/stripe/`. Copia el `webhook secret` que te muestre y colócalo en `STRIPE_WEBHOOK_SECRET`.
- En producción debes registrar el endpoint HTTPS `https://TU_DOMINIO/pedidos/webhooks/stripe/` en el dashboard de Stripe (Developers → Webhooks) y usar las claves live en las variables de entorno.
- Si quieres personalizar la moneda o activar modos de captura manual, revisa `tienda_virtual/settings.py` y `pedidos/payment_gateways/stripe_gateway.py` para extender la configuración.

Seguridad en despliegue
- Define `FORCE_HTTPS=1` en los entornos PaaS/producción para forzar redirecciones HTTPS, cookies seguras y HSTS (`SECURE_PROXY_SSL_HEADER` ya está configurado para `X-Forwarded-Proto`).
- Las políticas de contraseñas de Django (longitud mínima, contraseñas comunes, etc.) se validan con las pruebas de `tienda_virtual.tests.test_security`.
- Render (u otro PaaS) debe exponer la aplicación detrás de TLS; las pruebas anteriores garantizan que al activar `FORCE_HTTPS` la aplicación cumpla los requisitos de seguridad.
