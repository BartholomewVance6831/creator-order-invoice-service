from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import Literal

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    title: str
    kind: Literal["digital_asset", "subscription", "content_processing"]
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0, decimal_places=2)
    delivery_state: Literal["ready", "processing"]


class CreatorOrder(BaseModel):
    order_id: str
    creator_name: str
    customer_name: str
    customer_email: str
    currency: str = Field(min_length=3, max_length=3)
    items: list[OrderItem] = Field(min_length=1)


class InvoiceDecision(BaseModel):
    total: Decimal
    fulfillment_state: Literal["ready", "processing"]
    subscriber_update: Literal["send_downloads", "send_processing_update"]


def decide_invoice(order: CreatorOrder) -> InvoiceDecision:
    total = sum(
        (item.unit_price * item.quantity for item in order.items),
        start=Decimal("0.00"),
    ).quantize(Decimal("0.01"))
    is_ready = all(item.delivery_state == "ready" for item in order.items)
    return InvoiceDecision(
        total=total,
        fulfillment_state="ready" if is_ready else "processing",
        subscriber_update="send_downloads" if is_ready else "send_processing_update",
    )


def render_invoice_html(order: CreatorOrder, decision: InvoiceDecision) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(item.title)}</td>"
        f"<td>{escape(item.kind.replace('_', ' '))}</td>"
        f"<td>{item.quantity}</td>"
        f"<td>{item.unit_price:.2f}</td>"
        f"<td>{item.unit_price * item.quantity:.2f}</td>"
        "</tr>"
        for item in order.items
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: Arial, sans-serif; color: #17202a; margin: 42px; }}
h1 {{ margin-bottom: 4px; }} table {{ width: 100%; border-collapse: collapse; margin-top: 28px; }}
th, td {{ border-bottom: 1px solid #d5d8dc; padding: 10px 6px; text-align: left; }}
.total {{ text-align: right; font-size: 20px; margin-top: 24px; }}
</style></head><body>
<h1>Invoice {escape(order.order_id)}</h1>
<p>Creator: {escape(order.creator_name)}<br>Customer: {escape(order.customer_name)}</p>
<table><thead><tr><th>Item</th><th>Delivery</th><th>Qty</th><th>Unit</th><th>Amount</th></tr></thead>
<tbody>{rows}</tbody></table>
<p class="total">Total {escape(order.currency.upper())} {decision.total:.2f}</p>
<p>Fulfillment: {escape(decision.fulfillment_state)}</p>
</body></html>"""
