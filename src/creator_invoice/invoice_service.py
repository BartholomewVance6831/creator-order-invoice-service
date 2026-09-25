from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .infrai_pdf import InfraiError, InfraiPdfClient
from .order_invoice import CreatorOrder, InvoiceDecision, decide_invoice, render_invoice_html


class InvoiceResult(BaseModel):
    order_id: str
    decision: InvoiceDecision
    pdf: dict[str, Any]


app = FastAPI(title="Creator Order Invoice Service")


@app.post("/orders/invoice", response_model=InvoiceResult)
def create_order_invoice(order: CreatorOrder) -> InvoiceResult:
    decision = decide_invoice(order)
    html = render_invoice_html(order, decision)
    client = InfraiPdfClient()
    try:
        pdf = client.generate(html=html, order_id=order.order_id)
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": str(exc.detail.get("message", exc.code))},
        ) from exc
    finally:
        client.close()
    return InvoiceResult(order_id=order.order_id, decision=decision, pdf=pdf)
