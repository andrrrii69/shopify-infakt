import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

INFAKT_API_TOKEN = os.environ["INFAKT_API_TOKEN"]

app = FastAPI()

@app.post("/shopify")
async def handle_shopify_order(request: Request):
    data = await request.json()
    print(">>> ODEBRANE ZAMÓWIENIE:")
    print(data)

    # Przygotowanie danych klienta
    customer = data.get("customer", {})
    email = customer.get("email")

    if not email:
        return JSONResponse(content={"error": "Brak adresu email klienta"}, status_code=400)

    headers = {
        "Authorization": f"Bearer {INFAKT_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. Szukanie klienta
    client_search = requests.get(f"https://api.infakt.pl/v3/clients.json?email={email}", headers=headers)
    print(">>> ODPOWIEDŹ Z INFAKT (szukanie klienta):", client_search.status_code, client_search.text)

    client_id = None
    if client_search.status_code == 200 and client_search.json():
        client_id = client_search.json()[0]["id"]
    else:
        # 2. Próba stworzenia klienta
        client_data = {
            "email": email,
            "first_name": customer.get("first_name", ""),
            "last_name": customer.get("last_name", ""),
            "street": data.get("billing_address", {}).get("address1", ""),
            "city": data.get("billing_address", {}).get("city", ""),
            "postal_code": data.get("billing_address", {}).get("zip", ""),
            "country": data.get("billing_address", {}).get("country", ""),
        }

        res = requests.post("https://api.infakt.pl/v3/clients.json", headers=headers, json=client_data)
        print(">>> ODPOWIEDŹ Z INFAKT (tworzenie klienta):", res.status_code, res.text)

        if res.status_code == 201:
            client_id = res.json()["id"]
        else:
            return JSONResponse(content={"error": "Nie udało się utworzyć klienta", "infakt_response": res.text}, status_code=422)

    # 3. Tworzenie faktury
    invoice_data = {
        "client_id": client_id,
        "kind": "vat",
        "payment_method": "cash",
        "invoice_contents": [
            {
                "name": item["title"],
                "price": item["price"],
                "quantity": item["quantity"]
            } for item in data.get("line_items", [])
        ]
    }

    invoice_res = requests.post("https://api.infakt.pl/v3/invoices.json", headers=headers, json=invoice_data)
    print(">>> ODPOWIEDŹ INFAKT (tworzenie faktury):", invoice_res.status_code, invoice_res.text)

    if invoice_res.status_code != 201:
        return JSONResponse(content={"error": "Nie udało się utworzyć faktury", "infakt_response": invoice_res.text}, status_code=422)

    return JSONResponse(content={"status": "OK", "invoice_id": invoice_res.json()["id"]})

