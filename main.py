from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

INFAKT_API_TOKEN = os.environ["INFAKT_API_TOKEN"]
INFAKT_HEADERS = {
    "X-inFakt-ApiKey": INFAKT_API_TOKEN,
    "Content-Type": "application/json"
}

@app.post("/shopify")
async def handle_shopify_order(request: Request):
    order = await request.json()
    print(">>> ODEBRANE ZAMÓWIENIE:")
    print(order)

    try:
        email = order["email"]
        customer = order["customer"]
        billing = order["billing_address"]
        client_name = f'{customer["first_name"]} {customer["last_name"]}'

        # 🔍 Szukamy klienta po e-mailu
        async with httpx.AsyncClient() as client:
            client_search = await client.get(
                f"https://api.infakt.pl/v3/clients.json?email={email}",
                headers=INFAKT_HEADERS
            )

        clients = client_search.json()
        if clients:
            client_id = clients[0]["id"]
        else:
            # ➕ Tworzymy nowego klienta
            client_payload = {
                "client": {
                    "name": client_name,
                    "email": email,
                    "street": billing["address1"],
                    "post_code": billing["zip"],
                    "city": billing["city"],
                    "country": billing["country"]
                }
            }
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    "https://api.infakt.pl/v3/clients.json",
                    headers=INFAKT_HEADERS,
                    json=client_payload
                )
                new_client = res.json()
                client_id = new_client["id"]

        # 🧾 Przygotowanie pozycji faktury
        positions = []
        for item in order["line_items"]:
            positions.append({
                "name": item["name"],
                "quantity": item["quantity"],
                "unit_price_gross": float(item["price"]),
                "tax": "23"
            })

        invoice_payload = {
            "invoice": {
                "client_id": client_id,
                "invoice_date": order["created_at"][:10],
                "payment_to": order["created_at"][:10],
                "invoice_tax": "23",
                "kind": "vat",
                "positions": positions
            }
        }

        async with httpx.AsyncClient() as client:
            invoice_res = await client.post(
                "https://api.infakt.pl/v3/invoices.json",
                headers=INFAKT_HEADERS,
                json=invoice_payload
            )

        print(">>> ODPOWIEDŹ INFAKT:")
        print(invoice_res.status_code)
        print(invoice_res.text)

        if invoice_res.status_code == 201:
            return {"status": "success"}
        else:
            return {"status": "error", "details": invoice_res.text}

    except Exception as e:
        print(">>> BŁĄD:")
        print(str(e))
        return {"status": "error", "details": str(e)}

