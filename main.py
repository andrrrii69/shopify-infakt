
import os
import requests
from fastapi import FastAPI, Request

INFAKT_API_URL = "https://api.infakt.pl/v3/clients.json"
INFAKT_TOKEN = os.getenv("INFAKT_TOKEN")

app = FastAPI()

def find_client_by_email(email: str):
    headers = {"X-inFakt-ApiKey": INFAKT_TOKEN}
    response = requests.get(INFAKT_API_URL, headers=headers)
    response.raise_for_status()
    clients = response.json()
    for client in clients:
        if isinstance(client, dict) and client.get("client", {}).get("email") == email:
            return client["client"]["id"]
    return None

def create_client_in_infakt(email: str, customer: dict, address: dict):
    headers = {
        "X-inFakt-ApiKey": INFAKT_TOKEN,
        "Content-Type": "application/json",
    }
    client_data = {
        "client": {
            "email": email,
            "first_name": customer.get("first_name", ""),
            "last_name": customer.get("last_name", ""),
            "phone": customer.get("phone", ""),
            "street": address.get("address1", ""),
            "city": address.get("city", ""),
            "postal_code": address.get("zip", ""),
            "country": address.get("country", ""),
            "client_type": "private_person"
        }
    }
    response = requests.post(INFAKT_API_URL, headers=headers, json=client_data)
    if response.status_code == 201:
        return response.json()["id"]
    print("Błąd tworzenia klienta:", response.text)
    return None

@app.post("/shopify")
async def shopify_webhook(request: Request):
    data = await request.json()
    print(">>> ODEBRANE ZAMÓWIENIE:")
    print(data)
    email = data.get("email")
    customer = data.get("customer", {})
    address = data.get("shipping_address", {})

    client_id = find_client_by_email(email)
    if not client_id:
        client_id = create_client_in_infakt(email, customer, address)
    return {"client_id": client_id}
