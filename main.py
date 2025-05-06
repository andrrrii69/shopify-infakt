from fastapi import FastAPI, Request
import httpx
import uvicorn
import os

app = FastAPI()

INFAKT_API_TOKEN = os.environ["INFAKT_API_TOKEN"]
INFAKT_API_URL = "https://api.infakt.pl/v3/invoices.json"

@app.post("/shopify")
async def handle_shopify_order(request: Request):
    order = await request.json()

    client_name = order["customer"]["first_name"] + " " + order["customer"]["last_name"]
    client_email = order["email"]
    client_address = order["billing_address"]
    client_street = client_address["address1"]
    client_postcode = client_address["zip"]
    client_city = client_address["city"]
    client_country = client_address["country"]

    invoice_positions = []
    for item in order["line_items"]:
        invoice_positions.append({
            "name": item["name"],
            "quantity": item["quantity"],
            "unit_price_gross": float(item["price"]),
            "tax": "23"
        })

    payload = {
        "invoice": {
            "client_name": client_name,
            "client_email": client_email,
            "client_street": client_street,
            "client_post_code": client_postcode,
            "client_city": client_city,
            "client_country": client_country,
            "invoice_date": order["created_at"][:10],
            "payment_to": order["created_at"][:10],
            "invoice_tax": "23",
            "kind": "vat",
            "positions": invoice_positions
        }
    }

    headers = {
        "X-inFakt-ApiKey": INFAKT_API_TOKEN,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(INFAKT_API_URL, headers=headers, json=payload)

    if response.status_code == 201:
        return {"status": "success"}
    else:
        return {"status": "error", "details": response.text}
