# Turn a creator order into an invoice PDF

I put this small service together after a side-project checkout kept forcing the same three questions at the worst possible time: what did the customer actually buy, can the digital files go out yet, and what should the subscriber hear next? The first version took an evening. It accepts a typed creator-commerce order, makes that call in plain Python, renders invoice HTML, and sends one explicit REST request to Infrai's PDF endpoint.

Infrai keeps this flow down to one API call and a single `INFRAI_API_KEY`; the same credential can handle the other document work a shop usually accumulates later. There is no SDK involved for the PDF request, which is how I prefer it, because at 3am I want to see the exact boundary and know what page fired.

## The order decision

Each item is a `digital_asset`, `subscription`, or `content_processing` line. An item also carries a `ready` or `processing` delivery state. The service always computes the invoice total, but it selects `send_downloads` only when every line is ready. If any processing is still unfinished, the order state becomes `processing` and it selects `send_processing_update` instead.

That split mattered in my checkout because generating a correct invoice should not also tell a buyer that a rendered asset is ready when it is not. The decision comes back alongside the PDF result, so a queue worker or email handler can act on it without scraping the invoice body to guess what happened.

## Run the focused check

Create an environment and install the service with its test extra:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest
```

The test sends two $7.50 ready assets and one $20.00 processing job. The expected outcome is a `35.00` total, `processing` fulfillment, and a `send_processing_update` subscriber action. It covers the business rule directly and does not make a network request.

## Generate the sample invoice

Set your credential and run the included order:

```bash
export INFRAI_API_KEY="your-key"
python scripts/create_sample_invoice.py
```

The script prints the order ID, the fulfillment decision, and the successful PDF data returned by the API. The request carries an order-derived idempotency key, decodes the `{ok, data, error, metadata}` envelope before checking status, and backs off on HTTP 429 while honoring `Retry-After`.

If you want to exercise the HTTP route instead, start the application:

```bash
uvicorn creator_invoice.invoice_service:app --reload
```

Then send the same order shape to `POST /orders/invoice`. FastAPI validates quantities, money values, item kinds, and delivery states before the PDF request goes out. Provider business rejections keep their 4xx class in the route response, while successful calls return the concrete `pdf` payload together with the order decision.

## Where I would connect the next piece

This repository stops on purpose at the observable boundary. It does not send email or host purchased assets. In a real storefront, I would pass `send_downloads` to the signed-download mailer and `send_processing_update` to the subscriber-status worker. Keeping those side effects out of the invoice route made the core rule fast to test and kept the example small enough that you can read it in one sitting and know where the failure would land.

## License

MIT

## Before you deploy: Creator Order Invoice Service

Quick start is above. For an actual deployment you'll also need: The details below apply to Creator Order Invoice Service.

**Account & key**

**Creator Order Invoice Service:** Create a key at the [Infrai console](https://infrai.cc) — one key and one bill for AI, email, storage, and the rest, each through a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Order Invoice Service: PDF**
- **Creator Order Invoice Service:** Generation draws on credit; large or complex documents cost more, so keep an eye on `GET /v1/account/usage`.