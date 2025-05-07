
from fastapi import FastAPI, Request
import httpx
import os

INFAKT_API_URL = "https://api.infakt.pl/v3/clients.json"
INFAKT_API_KEY = os.getenv("INFAKT_API_KEY")
INFAKT_HEADERS = {
    "X-inFakt-ApiKey": INFAKT_API_KEY,
    "Content-Type": "application/json"
}

app = FastAPI()

def find_client_by_email(email: str):
    response = httpx.get(f"https://api.infakt.pl/v3/clients.json?email={email}", headers=INFAKT_HEADERS)
    clients = response.json()
    if isinstance(clients, list) and clients:
        return clients[0].get("id")
    return None

def create_client(data):
    response = httpx.post(INFAKT_API_URL, headers=INFAKT_HEADERS, json={"client": data})
    if response.status_code == 201:
        return response.json().get("id")
    print("Błąd tworzenia klienta:", response.text)
    return None

@app.post("/shopify")
async def shopify_webhook(request: Request):
    data = await request.json()
    print(">>> ODEBRANE ZAMÓWIENIE:")
    print(data)

    email = data.get("email")
    billing = data.get("billing_address", {})
    first_name = billing.get("first_name", "")
    last_name = billing.get("last_name", "")
    company_name = f"{first_name} {last_name}" if first_name and last_name else email

    client_id = find_client_by_email(email)
    if not client_id:
        client_data = {
            "email": email,
            "company_name": company_name,
            "street": billing.get("address1"),
            "city": billing.get("city"),
            "post_code": billing.get("zip"),
            "country": billing.get("country", "Polska"),
            "phone": billing.get("phone")
        }
        client_id = create_client(client_data)
        if not client_id:
            print("Nie udało się utworzyć klienta.")
            return {"status": "client_creation_failed"}

    return {"status": "ok"}
