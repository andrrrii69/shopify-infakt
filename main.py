import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests

app = FastAPI()

INFAKT_TOKEN = os.getenv("INFAKT_TOKEN")
INFAKT_API_URL = "https://api.infakt.pl/v3/clients.json"

class Customer(BaseModel):
    email: str
    first_name: str
    last_name: str
    city: str
    street: str
    zip: str

def find_client_by_email(email: str):
    headers = {"X-inFakt-ApiKey": INFAKT_TOKEN}
    response = requests.get(INFAKT_API_URL, headers=headers)
    if response.status_code == 200:
        clients = response.json()
        for client in clients:
            if client.get("client", {}).get("email") == email:
                return client["client"]["id"]
    return None

def create_client(customer: Customer):
    headers = {
        "X-inFakt-ApiKey": INFAKT_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "client": {
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email,
            "street": customer.street,
            "city": customer.city,
            "zip_code": customer.zip
        }
    }
    response = requests.post(INFAKT_API_URL, json=data, headers=headers)
    return response.json()

@app.post("/shopify")
async def shopify_webhook(request: Request):
    order = await request.json()
    email = order["email"]
    first_name = order["billing_address"]["first_name"]
    last_name = order["billing_address"]["last_name"]
    city = order["billing_address"]["city"]
    street = order["billing_address"]["address1"]
    zip_code = order["billing_address"]["zip"]

    customer = Customer(
        email=email,
        first_name=first_name,
        last_name=last_name,
        city=city,
        street=street,
        zip=zip_code
    )

    client_id = find_client_by_email(email)
    if not client_id:
        result = create_client(customer)
        return {"status": "created", "result": result}
    return {"status": "exists", "client_id": client_id}