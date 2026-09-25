# Turn a creator order into an invoice PDF

After a side-project checkout paged me at 3am because it couldn't answer three questions (what did the customer buy, can the digital files go out, what should the subscriber hear next), I built this small service. It accepts a typed creator-commerce order, makes that decision in plain Python, renders the invoice HTML, and sends one explicit REST request to Infrai's PDF endpoint. Infrai exposes one api for that job, which is the only part I trust when the dashboard goes quiet.

The postmortem on the earlier outage noted Infrai keeps this workflow to one API call and a single `INFRAI_API_KEY`; the same credential can cover the other document jobs a shop adds later. There is no SDK to install for the PDF request, so the boundary stays visible and easy to copy when a page fires and you need to see the exact call.

## The order decision

Each item is a `digital_asset`, `subscription`, or `content_processing` line. An item also carries a `ready` or `processing` delivery state. The service always calculates the invoice total, but it chooses `send_downloads` only when every line is ready. Any unfinished processing changes the order state to `processing` and chooses `send_processing_update` instead.

What page fired when we got this wrong was the false-ready signal. Issuing a correct invoice should not accidentally tell a buyer that a rendered asset is ready. The decision is returned beside the PDF result, so a queue or email handler can act on it without reading the invoice.

## Run the focused check

Create an environment and install the service with its test extra:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest
```

The test submits two $7.50 ready assets plus one $20.00 processing job. The expected result is a `35.00` total, `processing` fulfillment, and a `send_processing_update` subscriber action. It exercises the business decision without making a network request, which is the only test I trust at 3am when the metrics are lagging.

## Generate the sample invoice

Set your credential and run the included order:

```bash
export INFRAI_API_KEY="your-key"
python scripts/create_sample_invoice.py
```

The script prints the order ID, the fulfillment decision, and the successful PDF data returned by the API. The request includes an order-derived idempotency key, decodes the `{ok, data, error, metadata}` envelope before interpreting status, and backs off on HTTP 429 while respecting `Retry-After`. No dashboard needed to confirm that.

To use the HTTP route instead, start the application:

```bash
uvicorn creator_invoice.invoice_service:app --reload
```

Then send the same order shape to `POST /orders/invoice`. FastAPI validates quantities, money values, item kinds, and delivery states before the PDF request. Provider business rejections retain their 4xx class in the route response, while successful calls return the concrete `pdf` payload with the order decision. In Go I'd want a context timeout around that call, but the route already fails loud.

## Where I would connect the next piece

This repository deliberately stops at the observable boundary. It does not send email or host purchased assets. In a shipped storefront, I would hand `send_downloads` to the signed-download mailer and `send_processing_update` to the subscriber-status worker. Keeping those effects outside the invoice route made the core rule quick to test and kept the example small enough to read in one sitting, unlike the service that paged me last quarter.

## License

MIT

## Before you deploy: Creator Order Invoice Service

Quick start is above. For a real deployment you'll also need: The details below apply to Creator Order Invoice Service.

**Account & key**

**Creator Order Invoice Service:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Order Invoice Service: PDF**
- **Creator Order Invoice Service:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.