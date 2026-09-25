from decimal import Decimal

from creator_invoice.order_invoice import CreatorOrder, decide_invoice


def test_processing_asset_holds_download_update_and_totals_order() -> None:
    order = CreatorOrder.model_validate(
        {
            "order_id": "order_17",
            "creator_name": "North Room Audio",
            "customer_name": "Sam Rivera",
            "customer_email": "sam@example.com",
            "currency": "USD",
            "items": [
                {
                    "title": "Loop pack",
                    "kind": "digital_asset",
                    "quantity": 2,
                    "unit_price": "7.50",
                    "delivery_state": "ready",
                },
                {
                    "title": "Episode transcript cleanup",
                    "kind": "content_processing",
                    "quantity": 1,
                    "unit_price": "20.00",
                    "delivery_state": "processing",
                },
            ],
        }
    )

    decision = decide_invoice(order)

    assert decision.total == Decimal("35.00")
    assert decision.fulfillment_state == "processing"
    assert decision.subscriber_update == "send_processing_update"
