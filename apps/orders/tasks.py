from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Order


@shared_task
def send_order_confirmation_email(order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return

    subject = f"Order #{order.id} {order.status}"
    message = f"Your order #{order.id} is {order.status}."
    recipient = "test@example.com"  # placeholder

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=True,
    )
