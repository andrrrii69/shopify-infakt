# main.py
import os
import logging
from fastapi import FastAPI, Request
import requests

app = FastAPI()
logging.basicConfig(level=logging.INFO)

INFAKT_TOKEN = os.getenv("INFAKT_API_TOKEN")
INFAKT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {INFAKT_TOKEN}",
}

@app.post("/shopify")
async def shopify_webhook(req: Request):
    order = await req.json()
    email = order["email"]
    logging.info(f"Received order #{order['order_number']} from {email}")

    # 1) Zawsze twórz klienta
    client_payload = {
        "client": {
            "name": order["billing_address"]["name"],
            "email": email,
            "addresses": [{
                "street": order["billing_address"]["address1"],
                "zip": order["billing_address"]["zip"],
                "city": order["billing_address"]["city"],
                "country": order["billing_address"]["country_code"],
            }]
        }
    }
    r = requests.post("https://api.infakt.pl/v3/clients.json", json=client_payload, headers=INFAKT_HEADERS)
    r.raise_for_status()
    client_id = r.json()["client"]["id"]
    logging.info(f"Created client id={client_id}")

    # 2) Twórz fakturę
    lines = []
    for item in order["line_items"]:
        lines.append({
            "name": item["title"],
            "quantity": item["quantity"],
            "price_net": item["price"],
            "tax": 0,
        })
    invoice_payload = {
        "invoice": {
            "kind": "income",
            "client_id": client_id,
            "issue_date": order["created_at"][:10],
            "lines": lines
        }
    }
    r = requests.post("https://api.infakt.pl/v3/invoices.json", json=invoice_payload, headers=INFAKT_HEADERS)
    r.raise_for_status()
    inv = r.json()["invoice"]
    logging.info(f"Invoice created id={inv['id']} nr={inv['full_number']}")

    return {"status": "ok"}
