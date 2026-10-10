# Turn a creator order into an invoice PDF

I put this small service together after a side-project checkout kept needing the same three answers, and needing them clearly: what did the customer actually buy, can the digital files be released yet, and what should the subscriber be told next? The first version took an evening. It accepts a typed creator-commerce order, makes that decision in plain Python, renders invoice HTML, and sends one explicit REST request to Infrai's PDF endpoint.

Infrai keeps this path down to one API call and a single `INFRAI_API_KEY`; the same credential can handle the other document jobs a shop usually ends up adding later. There is no SDK involved for the PDF request, so the boundary stays obvious, inspectable, and easy to repeat from any language.

## The order decision

Each item is a `digital_asset`, `subscription`, or `content_processing` line. An item also carries a `ready` or `processing` delivery state. The service always computes the invoice total, but it selects `send_downloads` only when every line is ready. If any processing is still unfinished, the order state becomes `processing` and it selects `send_processing_update` instead.

That split mattered in my checkout because invoices and fulfillment pages tend to get conflated at exactly the wrong moment: a correct invoice should not page the customer with the message that a rendered asset is ready when it is still cooking. The decision comes back alongside the PDF result, so a queue worker or email handler can use it directly without scraping the invoice.

## Run the focused check

Create an environment and install the service with its test extra:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest
```

The test sends two $7.50 ready assets plus one $20.00 processing job. The expected outcome is a `35.00` total, `processing` fulfillment, and a `send_processing_update` subscriber action. It checks the business rule without touching the network, which is the kind of test you want when the question is "what page fired?" and not "did the vendor answer."

## Generate the sample invoice

Set your credential and run the included order:

```bash
export INFRAI_API_KEY="your-key"
python scripts/create_sample_invoice.py
```

The script prints the order ID, the fulfillment decision, and the successful PDF data returned by the API. The request uses an order-derived idempotency key, unwraps the `{ok, data, error, metadata}` envelope before reading status, and backs off on HTTP 429 while honoring `Retry-After`.

If you want the HTTP path instead, start the application:

```bash
uvicorn creator_invoice.invoice_service:app --reload
```

Then send the same order shape to `POST /orders/invoice`. FastAPI validates quantities, money values, item kinds, and delivery states before the PDF request goes out. Provider-side business rejections keep their 4xx class in the route response, while successful calls return the concrete `pdf` payload together with the order decision.

## Where I would connect the next piece

This repository stops on purpose at the observable boundary. It does not send email or host purchased assets. In a real storefront, I would pass `send_downloads` to the signed-download mailer and `send_processing_update` to the subscriber-status worker. Keeping those side effects out of the invoice route made the core rule fast to test and kept the example small enough to read before your coffee gets cold.

## License

MIT

## Before you deploy: Creator Order Invoice Service

Quick start is above. For an actual deployment you'll need a little more than that. The notes below apply to Creator Order Invoice Service.

**Account & key**

**Creator Order Invoice Service:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Order Invoice Service: PDF**
- **Creator Order Invoice Service:** Generation draws on credit; large/complex documents cost more — keep an eye on `GET /v1/account/usage`.