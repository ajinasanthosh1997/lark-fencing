from django.db import transaction
from django.db.models import F
from django.utils import timezone

from payments.models import Payment

from .models import Order, OrderStatusHistory


class OrderWorkflowError(ValueError):
    pass


ALLOWED_TRANSITIONS = {
    Order.Status.PENDING_PAYMENT: (Order.Status.CONFIRMED, Order.Status.CANCELLED),
    Order.Status.CONFIRMED: (Order.Status.PROCESSING, Order.Status.CANCELLED),
    Order.Status.PROCESSING: (Order.Status.READY, Order.Status.CANCELLED),
    Order.Status.READY: (Order.Status.DISPATCHED, Order.Status.DELIVERED, Order.Status.CANCELLED),
    Order.Status.DISPATCHED: (Order.Status.DELIVERED,),
    Order.Status.DELIVERED: (),
    Order.Status.CANCELLED: (),
    Order.Status.PARTIALLY_REFUNDED: (),
    Order.Status.REFUNDED: (),
}


def available_transitions(order):
    labels = dict(Order.Status.choices)
    return [(value, labels[value]) for value in ALLOWED_TRANSITIONS.get(order.status, ())]


ORDER_PROGRESS = (
    (Order.Status.CONFIRMED, "Confirmed"),
    (Order.Status.PROCESSING, "Processing"),
    (Order.Status.READY, "Ready"),
    (Order.Status.DISPATCHED, "Dispatched"),
    (Order.Status.DELIVERED, "Delivered"),
)


def workflow_progress(order):
    """Return the complete customer-order path for the dashboard progress tracker."""
    statuses = [status for status, _ in ORDER_PROGRESS]
    current_index = statuses.index(order.status) if order.status in statuses else -1
    if order.status == Order.Status.CANCELLED:
        reached = set(order.status_history.values_list("new_status", flat=True))
        reached.add(Order.Status.CONFIRMED)
        current_index = max((statuses.index(value) for value in reached if value in statuses), default=-1)
    steps = []
    for index, (status, label) in enumerate(ORDER_PROGRESS):
        if order.status == Order.Status.CANCELLED:
            state = "completed" if index <= current_index else "upcoming"
        elif index < current_index:
            state = "completed"
        elif index == current_index:
            state = "current"
        else:
            state = "upcoming"
        steps.append({"status": status, "label": label, "state": state})
    return steps


def _restore_inventory(order, now):
    if order.inventory_restocked_at:
        return
    for item in order.items.select_related("product", "variant"):
        if not item.product or not item.product.track_inventory:
            continue
        if item.variant_id:
            type(item.variant).objects.filter(pk=item.variant_id).update(
                stock_quantity=F("stock_quantity") + item.quantity
            )
        else:
            type(item.product).objects.filter(pk=item.product_id).update(
                stock_quantity=F("stock_quantity") + item.quantity
            )
    order.inventory_restocked_at = now


@transaction.atomic
def transition_order(order, new_status, *, changed_by=None, note=""):
    locked = Order.objects.select_for_update().get(pk=order.pk)
    allowed = ALLOWED_TRANSITIONS.get(locked.status, ())
    if new_status not in allowed:
        raise OrderWorkflowError(
            f"{locked.get_status_display()} orders cannot be changed to "
            f"{dict(Order.Status.choices).get(new_status, new_status)}."
        )

    previous_status = locked.status
    now = timezone.now()
    update_fields = ["status", "updated_at"]
    locked.status = new_status

    if new_status == Order.Status.CONFIRMED and not locked.confirmed_at:
        locked.confirmed_at = now
        update_fields.append("confirmed_at")
    elif new_status == Order.Status.DISPATCHED:
        locked.dispatched_at = now
        update_fields.append("dispatched_at")
    elif new_status == Order.Status.DELIVERED:
        locked.delivered_at = now
        update_fields.append("delivered_at")
    elif new_status == Order.Status.CANCELLED:
        if locked.payments.filter(status=Payment.Status.PAID).exists():
            raise OrderWorkflowError("A paid order cannot be cancelled until its payment is resolved.")
        _restore_inventory(locked, now)
        update_fields.append("inventory_restocked_at")
        locked.payments.filter(
            status__in=(
                Payment.Status.INITIATED,
                Payment.Status.PENDING,
                Payment.Status.AUTHORIZED,
            )
        ).update(status=Payment.Status.CANCELLED)

    locked.save(update_fields=update_fields)
    OrderStatusHistory.objects.create(
        order=locked,
        previous_status=previous_status,
        new_status=new_status,
        changed_by=changed_by,
        note=note.strip(),
    )
    return locked


@transaction.atomic
def record_cash_payment(order, *, changed_by=None):
    locked = Order.objects.select_for_update().get(pk=order.pk)
    if locked.status == Order.Status.CANCELLED:
        raise OrderWorkflowError("Cash cannot be recorded for a cancelled order.")
    payment = locked.payments.select_for_update().filter(
        method=Order.PaymentMethod.CASH_ON_DELIVERY
    ).first()
    if not payment:
        raise OrderWorkflowError("This order has no cash-on-delivery payment record.")
    if payment.status == Payment.Status.PAID:
        return payment
    if payment.status == Payment.Status.CANCELLED:
        raise OrderWorkflowError("A cancelled payment cannot be marked as paid.")
    payment.status = Payment.Status.PAID
    payment.paid_at = timezone.now()
    payment.save(update_fields=["status", "paid_at", "updated_at"])
    return payment
