
import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

INFAKT_TOKEN = os.getenv("INFAKT_TOKEN")
INFAKT_API_URL = "https://api.infakt.pl/v3/clients.json"
HEADERS = {"X-inFakt-ApiKey": INFAKT_TOKEN}


def find_client_by_email(email):
    response = requests.get(INFAKT_API_URL, headers=HEADERS)
    if response.status_code != 200:
        print("Błąd pobierania klientów:", response.text)
        return None

    for item in response.json():
        client_data = item.get("client") if isinstance(item, dict) else None
        if client_data and client_data.get("email") == email:
            return client_data.get("id")
    return None


def create_client(order):
    client_payload = {
        "client": {
            "name": f"{order['billing_address']['first_name']} {order['billing_address']['last_name']}",
            "email": order["email"],
            "street": order["billing_address"]["address1"],
            "city": order["billing_address"]["city"],
            "post_code": order["billing_address"]["zip"],
            "country": order["billing_address"]["country"],
            "phone": order["billing_address"]["phone"],
        }
    }

    response = requests.post(INFAKT_API_URL, headers=HEADERS, json=client_payload)
    if response.status_code != 201:
        print("Błąd tworzenia klienta:", response.text)
        return None

    return response.json()["client"]["id"]


@app.post("/shopify")
async def shopify_webhook(request: Request):
    data = await request.json()
    email = data.get("email")
    print(">>> ODEBRANE ZAMÓWIENIE:")
    print(data)

    client_id = find_client_by_email(email)
    if not client_id:
        client_id = create_client(data)

    if not client_id:
        return {"error": "Nie udało się znaleźć lub utworzyć klienta."}

    return {"client_id": client_id}
