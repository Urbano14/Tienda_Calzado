import logging
from decimal import Decimal

from django import forms
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from carrito.utils import obtener_o_crear_carrito
from clientes.models import Cliente
from pedidos.models import Pedido
from pedidos.services import crear_pedido_desde_carrito
from pedidos.payment_gateways import stripe_gateway

CHECKOUT_ENTREGA_SESSION_KEY = "checkout_entrega"
CHECKOUT_PAGO_SESSION_KEY = "checkout_pago"
CHECKOUT_PEDIDO_ID_SESSION_KEY = "checkout_pedido_id"

logger = logging.getLogger(__name__)


class DetallesEntregaForm(forms.Form):
    nombre = forms.CharField(max_length=150, label="Nombre")
    apellidos = forms.CharField(max_length=150, label="Apellidos")
    email = forms.EmailField(label="Correo electrónico")
    telefono = forms.RegexField(
        regex=r"^\+?\d{9,15}$",
        label="Teléfono de contacto",
        help_text="Incluye prefijo si es un número internacional.",
        error_messages={"invalid": "Introduce un teléfono válido (solo dígitos y prefijo opcional)."},
    )
    direccion = forms.CharField(
        max_length=255,
        label="Calle y vía",
        help_text="Ej.: Avenida Andalucía",
    )
    numero = forms.CharField(
        max_length=20,
        label="Número",
    )
    piso = forms.CharField(
        max_length=50,
        label="Piso / Puerta (opcional)",
        required=False,
    )
    ciudad = forms.CharField(max_length=120, label="Ciudad")
    provincia = forms.CharField(max_length=120, label="Provincia")
    codigo_postal = forms.RegexField(
        regex=r"^\d{5}$",
        label="Código Postal",
        error_messages={"invalid": "El código postal debe tener 5 dígitos."},
    )
    pais = forms.CharField(max_length=80, label="País", initial="España")
    referencias = forms.CharField(
        label="Referencias para el repartidor (opcional)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    METODOS_ENTREGA = [
        ("estandar", "Envío estándar (48-72h)"),
        ("urgente", "Envío urgente (24h)"),
        ("recogida", "Recogida en tienda"),
    ]
    metodo_entrega = forms.ChoiceField(
        choices=METODOS_ENTREGA,
        initial="estandar",
        label="Método de entrega",
        help_text="Elige cómo quieres recibir tu pedido.",
    )


class DetallesPagoForm(forms.Form):
    METODOS = (
        ("tarjeta", "Tarjeta (Stripe)"),
        ("contrareembolso", "Pago contra reembolso"),
    )
    metodo_pago = forms.ChoiceField(
        choices=METODOS,
        label="Método de pago",
        help_text="Selecciona la pasarela con la que deseas completar el cobro.",
    )
    referencia_pago = forms.CharField(
        required=False,
        label="Referencia de pago (opcional)",
        help_text="Últimos dígitos de la tarjeta o indicaciones para el repartidor.",
    )


class CheckoutBaseView(View):
    require_entrega = False
    require_pago = False
    allow_empty_cart = False

    def dispatch(self, request, *args, **kwargs):
        self.carrito = obtener_o_crear_carrito(request)
        carrito_vacio = not self.carrito.items.exists()
        pedido_confirmado = bool(request.session.get(CHECKOUT_PEDIDO_ID_SESSION_KEY))
        if carrito_vacio and not (self.allow_empty_cart or pedido_confirmado):
            messages.error(request, "Tu carrito está vacío. Añade productos antes de continuar.")
            return redirect("carrito")

        if self.require_entrega and not request.session.get(CHECKOUT_ENTREGA_SESSION_KEY):
            messages.warning(request, "Completa primero los detalles de entrega.")
            return redirect("pedidos:checkout_entrega")

        if self.require_pago and not request.session.get(CHECKOUT_PAGO_SESSION_KEY):
            messages.warning(request, "Completa primero los detalles de pago.")
            return redirect("pedidos:checkout_pago")

        return super().dispatch(request, *args, **kwargs)


class DetallesEntregaView(CheckoutBaseView):
    template_name = "checkout/detalles_entrega.html"
    form_class = DetallesEntregaForm

    def get(self, request, *args, **kwargs):
        request.session.pop(CHECKOUT_PEDIDO_ID_SESSION_KEY, None)
        form = self.form_class(initial=self.get_initial_data(request))
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        request.session.pop(CHECKOUT_PEDIDO_ID_SESSION_KEY, None)
        form = self.form_class(request.POST)
        if form.is_valid():
            request.session[CHECKOUT_ENTREGA_SESSION_KEY] = form.cleaned_data
            request.session.modified = True
            if request.user.is_authenticated:
                cliente, _ = Cliente.objects.get_or_create(user=request.user)
                cliente.nombre_completo = form.cleaned_data.get("nombre", "")
                cliente.apellidos = form.cleaned_data.get("apellidos", "")
                cliente.direccion = form.cleaned_data.get("direccion", "")
                cliente.ciudad = form.cleaned_data.get("ciudad", "")
                cliente.codigo_postal = form.cleaned_data.get("codigo_postal", "")
                cliente.provincia = form.cleaned_data.get("provincia", "")
                cliente.telefono = form.cleaned_data.get("telefono", "")
                cliente.save()
            return redirect("pedidos:checkout_pago")

        return render(request, self.template_name, {"form": form})

    @staticmethod
    def get_initial_data(request):
        data = request.session.get(CHECKOUT_ENTREGA_SESSION_KEY)
        if data:
            return data
        initial = {"pais": "España"}
        if request.user.is_authenticated:
            initial.update(
                {
                    "nombre": request.user.first_name or request.user.username,
                    "apellidos": request.user.last_name,
                    "email": request.user.email,
                }
            )
            try:
                cliente = request.user.cliente
                initial.update(
                    {
                        "nombre": cliente.nombre_completo or initial.get("nombre"),
                        "apellidos": cliente.apellidos or initial.get("apellidos"),
                        "direccion": cliente.direccion,
                        "ciudad": cliente.ciudad,
                        "codigo_postal": cliente.codigo_postal,
                        "provincia": cliente.provincia,
                        "telefono": cliente.telefono,
                    }
                )
            except Cliente.DoesNotExist:
                pass
        return initial


class DetallesPagoView(CheckoutBaseView):
    template_name = "checkout/detalles_pago.html"
    form_class = DetallesPagoForm
    require_entrega = True

    def get(self, request, *args, **kwargs):
        # Si se añaden más métodos de pago, aquí se puede precargar el preferido del cliente autenticado.
        form = self.form_class(initial=request.session.get(CHECKOUT_PAGO_SESSION_KEY))
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            request.session[CHECKOUT_PAGO_SESSION_KEY] = form.cleaned_data
            request.session.modified = True
            return redirect("pedidos:checkout_confirmacion")

        return render(request, self.template_name, {"form": form})


class ConfirmacionCompraView(CheckoutBaseView):
    template_name = "checkout/confirmacion_compra.html"
    require_entrega = True
    require_pago = True
    allow_empty_cart = True

    def get(self, request, *args, **kwargs):
        entrega_data = request.session.get(CHECKOUT_ENTREGA_SESSION_KEY, {}).copy()
        pago_data = request.session.get(CHECKOUT_PAGO_SESSION_KEY, {}).copy()
        pedido = self._obtener_o_crear_pedido(request, entrega_data, pago_data)

        context = {
            "pedido": pedido,
            "entrega": entrega_data or self._entrega_desde_pedido(pedido),
            "pago": pago_data or {"metodo_pago": pedido.metodo_pago, "referencia_pago": ""},
        }
        context.update(self._stripe_context(request, pedido))
        return render(request, self.template_name, context)

    def _obtener_o_crear_pedido(self, request, entrega_data, pago_data):
        pedido_id = request.session.get(CHECKOUT_PEDIDO_ID_SESSION_KEY)
        pedido = None
        if pedido_id:
            pedido = (
                Pedido.objects.select_related("cliente")
                .prefetch_related("items__producto")
                .filter(pk=pedido_id)
                .first()
            )

        if pedido:
            return pedido

        direccion_completa = self._direccion_formateada(entrega_data)

        payload = {
            "metodo_pago": pago_data.get("metodo_pago"),
            "direccion_envio": direccion_completa,
            "telefono": entrega_data.get("telefono"),
            "email_contacto": entrega_data.get("email"),
            "descuento": Decimal("0"),
            "metodo_entrega": entrega_data.get("metodo_entrega") or Pedido.MetodosEntrega.ESTANDAR,
        }

        payload["carrito"] = self.carrito

        pedido = crear_pedido_desde_carrito(
            request.user if request.user.is_authenticated else None,
            payload,
        )

        request.session[CHECKOUT_PEDIDO_ID_SESSION_KEY] = pedido.pk
        request.session.pop(CHECKOUT_ENTREGA_SESSION_KEY, None)
        request.session.pop(CHECKOUT_PAGO_SESSION_KEY, None)
        request.session.modified = True

        return (
            Pedido.objects.select_related("cliente")
            .prefetch_related("items__producto")
            .get(pk=pedido.pk)
        )

    @staticmethod
    def _entrega_desde_pedido(pedido):
        if not pedido:
            return {}
        nombre = ""
        apellidos = ""
        email = ""
        telefono = pedido.telefono
        if pedido.cliente:
            user = pedido.cliente
            nombre = getattr(user, "first_name", "") or getattr(user, "nombre", "")
            apellidos = getattr(user, "last_name", "") or getattr(user, "apellidos", "")
            email = getattr(user, "email", "")
        return {
            "nombre": nombre,
            "apellidos": apellidos,
            "email": email,
            "direccion": pedido.direccion_envio,
            "numero": "",
            "piso": "",
            "ciudad": "",
            "provincia": "",
            "codigo_postal": "",
            "pais": "",
            "referencias": "",
            "telefono": telefono,
        }

    @staticmethod
    def _direccion_formateada(entrega):
        if not entrega:
            return ""

        linea_principal = " ".join(
            filter(None, [entrega.get("direccion"), entrega.get("numero")])
        )
        linea_piso = entrega.get("piso")
        localidad = ", ".join(
            filter(
                None,
                [
                    entrega.get("codigo_postal"),
                    entrega.get("ciudad"),
                    entrega.get("provincia"),
                ],
            )
        )
        pais = entrega.get("pais")
        referencias = entrega.get("referencias")

        partes = [linea_principal]
        if linea_piso:
            partes.append(linea_piso)
        partes.append(localidad)
        if pais:
            partes.append(pais)
        if referencias:
            partes.append(f"Referencias: {referencias}")

        return " | ".join(filter(None, partes))

    def _stripe_context(self, request, pedido):
        if not pedido or pedido.metodo_pago != Pedido.MetodosPago.TARJETA:
            return {}

        if not stripe_gateway.is_enabled():
            return {
                "stripe_error": "Configura STRIPE_SECRET_KEY y STRIPE_PUBLISHABLE_KEY para habilitar el pago con tarjeta.",
            }

        try:
            intent = stripe_gateway.ensure_payment_intent(pedido)
        except stripe_gateway.StripeGatewayError as exc:
            logger.warning("No se pudo preparar Stripe para el pedido %s: %s", pedido.pk, exc)
            return {"stripe_error": str(exc)}

        return {
            "stripe_public_key": settings.STRIPE_PUBLISHABLE_KEY,
            "stripe_client_secret": intent.client_secret,
            "stripe_return_url": request.build_absolute_uri(request.path),
        }
