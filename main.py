import os
from fastapi import FastAPI, Request
import requests

app = FastAPI()

INFAKT_API_URL = "https://api.infakt.pl/v3/clients.json"
INFAKT_TOKEN = os.getenv("INFAKT_TOKEN")

def find_client_by_email(email: str):
    headers = {
        "X-inFakt-ApiKey": INFAKT_TOKEN,
        "Content-Type": "application/json",
    }
    response = requests.get("https://api.infakt.pl/v3/clients.json", headers=headers)
    if response.status_code != 200:
        return None
    clients = response.json()
    for client in clients:
        if isinstance(client, dict) and client.get("client", {}).get("email") == email:
            return client.get("client", {}).get("id")
    return None

def create_client(data: dict):
    headers = {
        "X-inFakt-ApiKey": INFAKT_TOKEN,
        "Content-Type": "application/json",
    }

    payload = {
        "client": {
            "email": data["email"],
            "phone": data.get("phone"),
            "name": f'{data["first_name"]} {data["last_name"]}',
            "street": data.get("street"),
            "city": data.get("city"),
            "postal_code": data.get("zip"),
            "country": data.get("country"),
            "company": False,
            "person": True
        }
    }

    response = requests.post(INFAKT_API_URL, headers=headers, json=payload)
    if response.status_code == 201:
        return response.json().get("client", {}).get("id")
    else:
        print("Błąd tworzenia klienta:", response.text)
        return None

@app.post("/shopify")
async def shopify_webhook(request: Request):
    order = await request.json()
    print(">>> ODEBRANE ZAMÓWIENIE:")
    print(order)

    email = order.get("email")
    first_name = order.get("billing_address", {}).get("first_name")
    last_name = order.get("billing_address", {}).get("last_name")
    street = order.get("billing_address", {}).get("address1")
    city = order.get("billing_address", {}).get("city")
    zip_code = order.get("billing_address", {}).get("zip")
    phone = order.get("billing_address", {}).get("phone")
    country = order.get("billing_address", {}).get("country")

    client_id = find_client_by_email(email)
    if client_id:
        print(f"Klient już istnieje w inFakt (ID: {client_id})")
    else:
        client_id = create_client({
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "street": street,
            "city": city,
            "zip": zip_code,
            "phone": phone,
            "country": country,
        })
        print(f"Utworzono nowego klienta w inFakt (ID: {client_id})" if client_id else "Nie udało się utworzyć klienta.")

    return {"ok": True}