import requests
from fastapi import FastAPI, Request

app = FastAPI()

INFAKT_HEADERS = {
    "X-inFakt-ApiKey": "TWÓJ_KLUCZ_API",
    "Content-Type": "application/json"
}

def find_client_by_email(email):
    response = requests.get(
        f"https://api.infakt.pl/v3/clients.json?email={email}",
        headers=INFAKT_HEADERS
    )
    clients = response.json()
    if clients:
        return clients[0]["id"]
    return None

def create_client(email, name):
    data = {
        "client": {
            "email": email,
            "name": name,
            "company_name": "",  # wcześniej było: None
            "country": "PL",
        }
    }
    response = requests.post(
        "https://api.infakt.pl/v3/clients.json",
        json=data,
        headers=INFAKT_HEADERS
    )
    response.raise_for_status()
    return response.json()["id"]

@app.post("/shopify")
async def shopify_webhook(request: Request):
    payload = await request.json()
    email = payload["email"]
    name = payload["shipping_address"]["first_name"] + " " + payload["shipping_address"]["last_name"]

    client_id = find_client_by_email(email)
    if not client_id:
        client_id = create_client(email, name)

    print(f"Utworzony / znaleziony klient ID: {client_id}")
    return {"status": "ok"}

