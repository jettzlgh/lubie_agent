import json
import os
from typing import Optional, List
from fastapi import FastAPI, Request
from pydantic import BaseModel
from openai import OpenAI
from contextlib import asynccontextmanager

# (Optionnel) Si vous utilisez la lib google-cloud-storage pour lire depuis un bucket GCP
# pip install google-cloud-storage
from google.cloud import storage

# ---------------------------
# Données & Configuration
# ---------------------------
# Votre clé OpenAI (ou vous pouvez la stocker dans une variable d'env)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-...")

# Nom du bucket GCP
GCP_BUCKET_NAME = "mon-bucket"
FAQ_FILE_PATH = "path/to/faq.json"
PRODUCTS_FILE_PATH = "path/to/reduced_products.json"

# ---------------------------
# LOGIQUE : Charger et stocker
# ---------------------------
faq_str = ""
products_str = ""

def load_files_from_gcp():
    """
    Récupère faq.json et reduced_products.json depuis le bucket GCP,
    puis stocke le JSON en string global (faq_str, products_str).
    """
    global faq_str, products_str

    # Initialiser le client
    storage_client = storage.Client()  # se base sur GOOGLE_APPLICATION_CREDENTIALS ou autre
    bucket = storage_client.bucket(GCP_BUCKET_NAME)

    # Charger FAQ
    faq_blob = bucket.blob(FAQ_FILE_PATH)
    faq_content = faq_blob.download_as_string()
    faq_str = faq_content.decode("utf-8")

    # Charger la liste de produits
    products_blob = bucket.blob(PRODUCTS_FILE_PATH)
    products_content = products_blob.download_as_string()
    products_str = products_content.decode("utf-8")


# ---------------------------
# VOTRE AGENT : code repris/ adapté
# ---------------------------
class UserRequest(BaseModel):
    request_type: str
    confidence_score: float
    request_needs: List[str]
    problem: List[str]
    name: str
    email: str
    order_number: str

conversation_history = []
client = None

def add_message(role, content):
    conversation_history.append({"role": role, "content": content})

def add_message_full(history):
    """
    Injecte dans conversation_history des messages déjà existants
    (utile si vous recevez un historique).
    """
    for msg in history:
        conversation_history.append(msg)

def users_requests_type(user_prompt: str) -> UserRequest:
    add_message("user", user_prompt)
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=conversation_history,
        response_format=UserRequest
    )
    result = completion.choices[0].message.parsed
    add_message("assistant", str(result.model_dump()))
    return result

def product(prompt: str):
    # On ajoute une consigne system
    add_message("system", "Cherche dans products_str la réponse à la question")
    add_message("system", "Ensuite propose à l'utilisateur un autre produit")
    add_message("user", prompt)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history
    )
    result = completion.choices[0].message.content
    add_message("assistant", result)
    return result

def faq(prompt: str):
    add_message("system", "Question sur la marque. Cherche dans faq_str la meilleure réponse.")
    add_message("user", prompt)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history
    )
    result = completion.choices[0].message.content
    add_message("assistant", result)
    return result

def order(prompt: str, user_request: UserRequest):
    add_message("system", (f"L'utilisateur a envoyé : {user_request.dict()}. "
                            "Si name/email/commande manquant, demander. Sinon confirmer."))
    add_message("user", prompt)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history
    )
    result = completion.choices[0].message.content
    add_message("assistant", result)
    return result

def oos(prompt: str):
    add_message("system", ("L'utilisateur est hors scope MyLubie. "
                           "Réponds gentiment et indique ce que tu peux faire."))
    add_message("user", prompt)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history
    )
    result = completion.choices[0].message.content
    add_message("assistant", result)
    return result

def process_user_request(user_prompt: str, history=None):
    # Si on reçoit un historique, on l'ajoute à la conv
    if history:
        add_message_full(history)

    # Étape 1 : classification
    user_request = users_requests_type(user_prompt)

    # Étape 2 : route en fonction du type
    if user_request.request_type == "product_info":
        return product(user_prompt)
    elif user_request.request_type == "faq":
        return faq(user_prompt)
    elif user_request.request_type == "order":
        return order(user_prompt, user_request)
    elif user_request.request_type == "out_of_scope":
        return oos(user_prompt)
    else:
        apology = "Pardonnez-moi, je ne pense pas pouvoir répondre à cela."
        add_message("assistant", apology)
        return apology


# ---------------------------
# Créer l'appli FastAPI
# ---------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialisation au démarrage de l'app (ex: charger fichiers GCP, init OpenAI, etc.).
    """
    # 1. Charger les fichiers depuis GCP
    # load_files_from_gcp()

    # 2. Initialiser le client openai
    global client

    # 3. Injecter faq_str et products_str dans la conversation initiale
    base_system_message = (
        "Tu es l'assistant virtuel de MyLubie. "
        f"Voici la FAQ : {faq_str}\n"
        f"Voici la liste de produits : {products_str}\n"
        "Réponds selon ces sources. Sinon, dis 'Je ne sais pas'."
    )
    conversation_history.clear()
    conversation_history.append({"role": "system", "content": base_system_message})

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    user_prompt: str
    history: Optional[list] = None  # Optionnel : l'historique existant côté front


@app.post("/ask")
def ask_agent(req: ChatRequest):
    """
    Endpoint pour envoyer un message utilisateur et (optionnellement) un historique.
    Retourne la réponse de l'IA.
    """
    response = process_user_request(req.user_prompt, req.history)
    return {"response": response}


@app.get("/")
def root():
    return {"message": "API MyLubie opérationnelle"}
