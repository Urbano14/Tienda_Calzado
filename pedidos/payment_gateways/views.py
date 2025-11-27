import json

from django.http import HttpResponse, JsonResponse
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


@method_decorator(csrf_exempt, name="dispatch")
class StripeConfirmIntentView(View):
    """Permite confirmar manualmente un PaymentIntent desde el frontend."""

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido."}, status=400)

        intent_id = payload.get("payment_intent_id") or payload.get("paymentIntentId")
        if not intent_id:
            return JsonResponse({"error": "Falta 'payment_intent_id'."}, status=400)

        try:
            processed = stripe_gateway.confirm_payment_intent(intent_id)
        except stripe_gateway.StripeGatewayError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        return JsonResponse({"processed": processed})
