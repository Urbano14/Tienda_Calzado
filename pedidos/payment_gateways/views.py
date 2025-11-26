from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from pedidos.payment_gateways import stripe_gateway


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    """Recibe eventos de Stripe para confirmar pagos."""

    def post(self, request, *args, **kwargs):
        signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        if not signature:
            return HttpResponse("Cabecera de firma ausente.", status=400)

        try:
            event = stripe_gateway.construct_event(request.body, signature)
            handled = stripe_gateway.handle_event(event)
        except stripe_gateway.StripeGatewayError as exc:
            return HttpResponse(str(exc), status=400)

        return HttpResponse(status=200 if handled else 202)
