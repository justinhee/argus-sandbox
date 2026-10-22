"""Order emails: confirmation, shipping and refund notices."""

from __future__ import annotations

import html
import logging
import smtplib
from email.message import EmailMessage

from shop.models import Customer, Order
from shop.money import format_amount

log = logging.getLogger(__name__)

CONFIRMATION_TEMPLATE = """\
<html><body>
<h1>Thanks for your order, {name}!</h1>
<p>Order #{order_id} has been placed.</p>
<table>
{rows}
</table>
<p>Subtotal: {subtotal}<br>Discount: {discount}<br>Shipping: {shipping}<br>Tax: {tax}</p>
<p><b>Total: {total}</b></p>
</body></html>
"""

ROW_TEMPLATE = "<tr><td>{sku}</td><td>{qty}</td><td>{price}</td></tr>"


def render_confirmation(customer: Customer, order: Order) -> str:
    rows = "\n".join(
        ROW_TEMPLATE.format(sku=html.escape(l.sku), qty=l.quantity, price=format_amount(l.total))
        for l in order.lines
    )
    return CONFIRMATION_TEMPLATE.format(
        name=customer.name,
        order_id=order.order_id,
        rows=rows,
        subtotal=format_amount(order.subtotal),
        discount=format_amount(-order.discount),
        shipping=format_amount(order.shipping),
        tax=format_amount(order.tax),
        total=format_amount(order.total),
    )


def render_shipped(customer: Customer, order: Order, tracking_number: str) -> str:
    return (
        f"<html><body><p>Hi {html.escape(customer.name)},</p>"
        f"<p>Order #{order.order_id} is on its way. Tracking: {html.escape(tracking_number)}</p>"
        f"</body></html>"
    )


class Mailer:
    def __init__(self, host: str, port: int, sender: str) -> None:
        self._host = host
        self._port = port
        self._sender = sender

    def send(self, to: str, subject: str, html_body: str) -> bool:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content("This message requires an HTML-capable mail client.")
        message.add_alternative(html_body, subtype="html")
        try:
            with smtplib.SMTP(self._host, self._port, timeout=10) as smtp:
                smtp.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            log.error("failed to send %r to %s: %s", subject, to, exc)
            return False
        return True

    def order_confirmation(self, customer: Customer, order: Order) -> bool:
        return self.send(customer.email, f"Order #{order.order_id} confirmed",
                         render_confirmation(customer, order))

    def order_shipped(self, customer: Customer, order: Order, tracking_number: str) -> bool:
        return self.send(customer.email, f"Order #{order.order_id} shipped",
                         render_shipped(customer, order, tracking_number))
