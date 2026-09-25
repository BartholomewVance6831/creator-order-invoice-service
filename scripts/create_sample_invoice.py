import json

from creator_invoice.infrai_pdf import InfraiPdfClient
from creator_invoice.order_invoice import CreatorOrder, decide_invoice, render_invoice_html


def main() -> None:
    order = CreatorOrder.model_validate(
        {
            "order_id": "order_1042",
            "creator_name": "Mina Makes",
            "customer_name": "Alex Chen",
            "customer_email": "alex@example.com",
            "currency": "USD",
            "items": [
                {
                    "title": "Studio lighting presets",
                    "kind": "digital_asset",
                    "quantity": 1,
                    "unit_price": "18.00",
                    "delivery_state": "ready",
                },
                {
                    "title": "Member feed refresh",
                    "kind": "content_processing",
                    "quantity": 1,
                    "unit_price": "12.00",
                    "delivery_state": "ready",
                },
            ],
        }
    )
    decision = decide_invoice(order)
    client = InfraiPdfClient()
    try:
        pdf = client.generate(render_invoice_html(order, decision), order.order_id)
    finally:
        client.close()
    print(json.dumps({"order_id": order.order_id, "decision": decision.model_dump(mode="json"), "pdf": pdf}, indent=2))


if __name__ == "__main__":
    main()
