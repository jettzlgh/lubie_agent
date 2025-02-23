import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
import json



# -----------------------
#LOAD RAG DOCS
# -----------------------

#Products list
products_short = "reduced_products.json"
with open(products_short, "r", encoding="utf-8") as f:
    products_json = json.load(f)
products_str = json.dumps(products_json, indent=2)

 # Load FAQ
faq_file = "faq.json"
with open(faq_file, "r", encoding="utf-8") as f:
    faq_load = json.load(f)
faq_str = json.dumps(faq_load, indent=2)

# -----------------------
# GLOBAL CONVERSATION HISTORY
# -----------------------
conversation_history = [
    {
        "role": "system",
        "content": ('Tu es l''assistant virtuel de MyLubie, une entreprise française qui vend des produits de bien être intime liés à la sexualité.'
                    'Tu es implémenté sur le site internet de la marque, et tu dois répondre au mieux aux questions des clients.'
                    f"Voici la liste des produits avec les informations dans lesquelles tu peux chercher des réponses products_str={products_str}"
                    f"Voici la liste des questions réponses dans lesquelles tu peux chercher des réponses faq_str={faq_str}"
        )
    }
]

def add_message(role, content):
    """
    Append a message to our global conversation history.
    role: 'system' | 'user' | 'assistant'
    content: str
    """
    conversation_history.append({"role": role, "content": content})

def add_message_full(message):
    for msg in message:
        conversation_history.append(msg)
# -----------------------
# OPENAI CLIENT
# -----------------------
client = OpenAI(api_key=st.secrets["openai_api_key"])


# -----------------------
# DATA MODEL
# -----------------------
class UserRequest(BaseModel):
    request_type: str
    confidence_score: float
    request_needs: list[str]
    problem: list[str]
    name: str
    email: str
    order_number: str


# -----------------------
# 1) DETERMINE USER REQUEST TYPE
# -----------------------
def users_requests_type(user_prompt: str):
    # Step 1: Add the system instruction for this stage
    system_instruction = ('Tu es l''assistant virtuel de MyLubie, une entreprise française qui vend des produits de bien être intime liés à la sexualité.'
                                             'Tu es implémenté sur le site internet de la marque, et tu dois répondre au mieux aux questions des clients. Tu dois d''abord déterminer le type de besoin de l''utilisateur:'
                                             'En fonction du type de besoi, tu dois renvoyer le champ request_type associé'
                                             'Le champ confidence_score doit déterminier ton niveau de certitude sur le type de question. Il vaut 0 si tu n''es pas sur du tout et il faut 1 si tu es sur et certain'
                                             '1. Questions sur un produit -> return request_type= "product_info" '
                                             '2. Question générique sur la marque -> return request_type= "faq" '
                                             '3. Question sur une commande -> return request_type= "order"'
                                             '4. Si tu penses que l"utilisateur a des problemes, alors tu peux renseigner ces problemes dans le champ problem'
                                             '5. Si l"utilisateur donne son nom tu peux retourner la valeur dans le champ name'
                                             '6. Si l"utilisateur donne son numéro de commande tu peux retourner la valeur dans le champ order_number'
                                             '7. Si l"utilisateur donne son email tu peux retourner la valeur dans le champ order_email'
                                             'Tu dois renvoyer la liste des produits ou informations demandées par l''utilisateur dans le champ request_need')
    add_message("system", system_instruction)

    # Step 2: Add the user's message
    add_message("user", user_prompt)
    print(f"history is {conversation_history}")
    # Step 3: Call OpenAI with the entire conversation
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=conversation_history,
        response_format=UserRequest
    )

    # Step 4: Extract the structured response
    result = completion.choices[0].message.parsed
    print(result)
    # Step 5: Add the assistant's raw text to history
    add_message("assistant", str(result.model_dump()))

    return result


# -----------------------
# 2) PRODUCT QUESTIONS
# -----------------------
def product(prompt):
    add_message("system", "Tu es l''assistant virtuel de MyLubie, une entreprise française qui vend des produits de bien être intime liés à la sexualité.")
    add_message("user", prompt)

    # Add product data to the conversation
    # add_message("system", f"Cherche dans la liste de produit suivantes la réponse à la question posée par l''utilisateur{products_str}.")
    add_message("system", "Cherche dans la liste de produit products_str")
    add_message("system", "Une fois avoir répondu, propose à l''utilisateur d''acheter un nouveau produit de la liste en faisant la meilleure recommandation possible")


    # Call OpenAI
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history
    )

    result = completion.choices[0].message.content
    add_message("assistant", result)
    print(result)
    return result


# -----------------------
# 3) FAQ QUESTIONS
# -----------------------
def faq(prompt):
    add_message("system", "L''utilisateur semble avoir une question sur la marque. Cherche parmis la liste des questions réponses faq_str la réponse la plus adaptée.")
    add_message("user", prompt)
    add_message("system", 'Tu dois répondre exactement le contenu "answer" lié à la "question" dans le fichier qui tas été transmis'
                            'Si tu hésites entre plusieurs questions, tu peux proposer les sujets sur lesquels tu hésitais après avoir répondu.')

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history
    )

    result = completion.choices[0].message.content
    add_message("assistant", result)
    return result


# -----------------------
# 4) ORDER QUESTIONS
# -----------------------
def order(prompt, user_request):
    add_message("system", (f"L'utilisateur a déjà envoyé un message et tu avais renvoyé la structure de données suivantes : {user_request}"
                            'Si les champs name, problems, email, order_number sont vides, alors redemande lui afin d"avoir toutes les données.'
                            'Une fois tous ces champs renseignés, dis lui qu"il sera prochainement recontacté par nos équipes avec une réponse'))
    add_message("user", prompt)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history
    )

    result = completion.choices[0].message.content
    add_message("assistant", result)
    return result


# -----------------------
# 5) TOP-LEVEL PROCESSOR
# -----------------------
def process_user_request(user_prompt: str, history):
    if history!=None:
        print('in add message')
        print(history)
        add_message_full(history)
    user_request = users_requests_type(user_prompt)

    # If not confident
    if user_request.confidence_score < 0.6:
        apology = "Pardonnez-moi, je ne pense pas pouvoir répondre à cela. Veuillez reformuler."
        print(apology)
        add_message("assistant", apology)
        add_message("user", user_prompt)
        return None

    # Route by request_type
    if user_request.request_type == "product_info":
        return product(user_prompt)
    elif user_request.request_type == "faq":
        return faq(user_prompt)
    elif user_request.request_type == "order":
        return order(user_prompt, user_request)
    else:
        apology = "Pardonnez-moi, je ne pense pas pouvoir répondre à cela. Veuillez reformuler."
        print(apology)
        add_message("assistant", apology)
        return None


# -----------------------
# 6) MAIN LOOP
# -----------------------
if __name__ == "__main__":
    print("Bonjour, je suis l'assistant de MyLubie. Comment puis-je vous aider ?\n")

    while True:
        # print(f"history : {conversation_history}")
        user_input = input("> ")
        if not user_input:
            break  # end if user presses Enter with no text
        response = process_user_request(user_input, None)
        print(response)
