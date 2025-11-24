from decimal import Decimal

from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from carrito.utils import obtener_o_crear_carrito
from pedidos.models import Pedido
from pedidos.services import crear_pedido_desde_carrito

CHECKOUT_ENTREGA_SESSION_KEY = "checkout_entrega"
CHECKOUT_PAGO_SESSION_KEY = "checkout_pago"
CHECKOUT_PEDIDO_ID_SESSION_KEY = "checkout_pedido_id"


class DetallesEntregaForm(forms.Form):
    nombre = forms.CharField(max_length=150, label="Nombre")
    apellidos = forms.CharField(max_length=150, label="Apellidos")
    email = forms.EmailField(label="Correo electrónico")
    direccion = forms.CharField(max_length=255, label="Dirección")
    ciudad = forms.CharField(max_length=120, label="Ciudad")
    codigo_postal = forms.CharField(max_length=20, label="Código Postal")
    telefono = forms.CharField(max_length=30, label="Teléfono de contacto")


class DetallesPagoForm(forms.Form):
    METODOS = (
        ("tarjeta", "Tarjeta"),
        ("reembolso", "Pago contra reembolso"),
    )
    metodo_pago = forms.ChoiceField(choices=METODOS, label="Método de pago")
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
            return redirect("pedidos:checkout_pago")

        return render(request, self.template_name, {"form": form})

    @staticmethod
    def get_initial_data(request):
        data = request.session.get(CHECKOUT_ENTREGA_SESSION_KEY)
        if data:
            return data
        if request.user.is_authenticated:
            return {
                "nombre": request.user.first_name or request.user.username,
                "apellidos": request.user.last_name,
                "email": request.user.email,
            }
        return {}


class DetallesPagoView(CheckoutBaseView):
    template_name = "checkout/detalles_pago.html"
    form_class = DetallesPagoForm
    require_entrega = True

    def get(self, request, *args, **kwargs):
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

        direccion_envio = entrega_data.get("direccion", "")
        ciudad = entrega_data.get("ciudad", "")
        codigo_postal = entrega_data.get("codigo_postal", "")
        direccion_completa = ", ".join(filter(None, [direccion_envio, ciudad, codigo_postal]))

        payload = {
            "metodo_pago": pago_data.get("metodo_pago"),
            "direccion_envio": direccion_completa,
            "telefono": entrega_data.get("telefono"),
            "descuento": Decimal("0"),
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
            "telefono": telefono,
        }
