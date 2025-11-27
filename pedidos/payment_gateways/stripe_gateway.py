from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

try:
    import stripe  # type: ignore
except ImportError:  # pragma: no cover - entorno sin stripe instalado
    stripe = None
from django.conf import settings

from pedidos.models import Pedido
from pedidos.services import disparar_confirmacion_pedido

logger = logging.getLogger(__name__)


class StripeGatewayError(Exception):
    """Errores controlados relacionados con Stripe."""


def is_enabled() -> bool:
    return bool(stripe and settings.STRIPE_SECRET_KEY and settings.STRIPE_PUBLISHABLE_KEY)


def _configure_stripe() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise StripeGatewayError("Falta configurar STRIPE_SECRET_KEY.")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    if getattr(settings, "STRIPE_API_VERSION", ""):
        stripe.api_version = settings.STRIPE_API_VERSION


def _amount_to_cents(amount: Decimal) -> int:
    return int(Decimal(amount).quantize(Decimal("0.01")) * 100)


def ensure_payment_intent(pedido: Pedido) -> stripe.PaymentIntent:
    if stripe is None:
        raise StripeGatewayError("Stripe no está instalado en este entorno.")
    if not is_enabled():
        raise StripeGatewayError("Stripe no está habilitado en este entorno.")

    _configure_stripe()
    amount = _amount_to_cents(pedido.total)
    intent: Optional[stripe.PaymentIntent] = None

    try:
        if pedido.stripe_payment_intent_id:
            intent = stripe.PaymentIntent.retrieve(pedido.stripe_payment_intent_id)
            if intent.amount != amount:
                intent = stripe.PaymentIntent.modify(intent.id, amount=amount)
        else:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=getattr(settings, "STRIPE_DEFAULT_CURRENCY", "eur"),
                description=f"Pedido {pedido.numero_pedido}",
                metadata={
                    "pedido_id": str(pedido.pk),
                    "numero_pedido": pedido.numero_pedido,
                },
                automatic_payment_methods={"enabled": True},
            )
            pedido.stripe_payment_intent_id = intent.id
            pedido.save(update_fields=["stripe_payment_intent_id"])
    except stripe.error.StripeError as exc:
        logger.exception("Error creando PaymentIntent de Stripe: %s", exc.user_message or str(exc))
        raise StripeGatewayError(exc.user_message or "No se pudo crear el pago en Stripe.") from exc

    _sync_payment_state(pedido, intent)
    if (intent.status or "").lower() == "succeeded":
        _finalize_payment_success(pedido, intent, sync_state=False)
    return intent


def _sync_payment_state(pedido: Pedido, intent: stripe.PaymentIntent) -> None:
    updates: list[str] = []
    status = intent.status or ""
    if status != pedido.stripe_payment_status:
        pedido.stripe_payment_status = status
        updates.append("stripe_payment_status")

    latest_charge_id = intent.latest_charge or ""
    receipt_url = ""
    charges = getattr(intent, "charges", None)
    if charges and getattr(charges, "data", None):
        last_charge = charges.data[-1]
        latest_charge_id = last_charge.get("id", latest_charge_id)
        receipt_url = last_charge.get("receipt_url", "")

    if latest_charge_id and latest_charge_id != pedido.stripe_charge_id:
        pedido.stripe_charge_id = latest_charge_id
        updates.append("stripe_charge_id")

    if receipt_url and receipt_url != pedido.stripe_receipt_url:
        pedido.stripe_receipt_url = receipt_url
        updates.append("stripe_receipt_url")

    if updates:
        pedido.save(update_fields=updates)


def _finalize_payment_success(
    pedido: Pedido, intent: stripe.PaymentIntent, *, sync_state: bool = True
) -> None:
    if sync_state:
        _sync_payment_state(pedido, intent)

    updates: list[str] = []
    was_pending = pedido.estado == Pedido.Estados.PENDIENTE
    if was_pending:
        pedido.estado = Pedido.Estados.PROCESANDO
        updates.append("estado")

    if updates:
        pedido.save(update_fields=updates)

    if was_pending:
        disparar_confirmacion_pedido(pedido)


def construct_event(payload: bytes, signature: str) -> stripe.Event:
    if stripe is None:
        raise StripeGatewayError("Stripe no está instalado en este entorno.")
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise StripeGatewayError("Falta configurar STRIPE_WEBHOOK_SECRET para procesar webhooks.")

    _configure_stripe()
    try:
        return stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError as exc:
        logger.warning("Firma de webhook inválida: %s", exc)
        raise StripeGatewayError("Firma de Stripe no válida.") from exc


def handle_event(event: stripe.Event) -> bool:
    if stripe is None:
        raise StripeGatewayError("Stripe no está instalado en este entorno.")
    event_type = event.get("type")
    data_object: Dict[str, Any] = event.get("data", {}).get("object", {})
    if not data_object:
        logger.info("Evento Stripe %s sin payload", event_type)
        return False

    if event_type == "payment_intent.succeeded":
        return _handle_payment_intent_succeeded(data_object)
    if event_type in {"payment_intent.payment_failed", "payment_intent.canceled"}:
        return _handle_payment_intent_failed(data_object)

    logger.debug("Evento Stripe %s ignorado", event_type)
    return False


def _get_pedido_from_intent(intent_data: Dict[str, Any]) -> Optional[Pedido]:
    metadata = intent_data.get("metadata", {}) or {}
    pedido_id = metadata.get("pedido_id")
    numero = metadata.get("numero_pedido")
    pedido = None
    if pedido_id:
        pedido = Pedido.objects.filter(pk=pedido_id).first()
    if not pedido and numero:
        pedido = Pedido.objects.filter(numero_pedido=numero).first()
    if not pedido:
        logger.warning("No se encontró pedido para PaymentIntent %s", intent_data.get("id"))
    return pedido


def _handle_payment_intent_succeeded(intent_data: Dict[str, Any]) -> bool:
    pedido = _get_pedido_from_intent(intent_data)
    if not pedido:
        return False

    intent_obj = stripe.util.convert_to_stripe_object(intent_data)
    _finalize_payment_success(pedido, intent_obj, sync_state=True)

    logger.info(
        "Pago confirmado en Stripe para pedido %s (intent %s)",
        pedido.numero_pedido,
        intent_data.get("id"),
    )
    return True


def _handle_payment_intent_failed(intent_data: Dict[str, Any]) -> bool:
    pedido = _get_pedido_from_intent(intent_data)
    if not pedido:
        return False

    status = intent_data.get("status", "")
    if status and status != pedido.stripe_payment_status:
        pedido.stripe_payment_status = status
        pedido.save(update_fields=["stripe_payment_status"])

    logger.warning(
        "Pago fallido o cancelado en Stripe para pedido %s", pedido.numero_pedido
    )
    return True


def confirm_payment_intent(intent_id: str) -> bool:
    if stripe is None:
        raise StripeGatewayError("Stripe no está instalado en este entorno.")
    if not intent_id:
        raise StripeGatewayError("Falta el identificador del PaymentIntent.")
    if not is_enabled():
        raise StripeGatewayError("Stripe no está habilitado en este entorno.")

    _configure_stripe()
    try:
        intent = stripe.PaymentIntent.retrieve(intent_id)
    except stripe.error.StripeError as exc:
        logger.exception("Error consultando PaymentIntent %s: %s", intent_id, exc.user_message or str(exc))
        raise StripeGatewayError(exc.user_message or "No se pudo verificar el estado del pago.") from exc

    status = (intent.status or "").lower()
    if status != "succeeded":
        raise StripeGatewayError("El pago todavía no está confirmado por Stripe.")

    intent_data = intent.to_dict_recursive()
    pedido = _get_pedido_from_intent(intent_data)
    if not pedido:
        raise StripeGatewayError("No se encontró el pedido asociado a este pago.")

    _finalize_payment_success(pedido, intent, sync_state=True)
    logger.info(
        "Pago confirmado manualmente para pedido %s (intent %s)",
        pedido.numero_pedido,
        intent.id,
    )
    return True
