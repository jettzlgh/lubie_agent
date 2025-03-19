import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
import json

# client = OpenAI()
client = OpenAI(api_key=st.secrets["openai_api_key"])


# -----------------------
#LOAD RAG DOCS
# -----------------------

#Products list
# products_short = "reduced_products.json"
# with open(products_short, "r", encoding="utf-8") as f:
#     products_json = json.load(f)
# products_str = json.dumps(products_json, indent=2)

#  # Load FAQ
# faq_file = "faq.json"
# with open(faq_file, "r", encoding="utf-8") as f:
#     faq_load = json.load(f)
# faq_str = json.dumps(faq_load, indent=2)

# -----------------------
# GLOBAL Instruction
# -----------------------
system_instruction = '''
                    ###MISSION###
                    Tu as pour mission de répondre au mieux à la question qui t'a été posée, en fonction de tes instructions et des documents à ta disposition

                    ###ROLE###
                    Tu es l'assitant de My Lubie depuis 10 ans. Tu es expert de cette marque et de la relation client. On attend de toi de répondre aux questions clients de la meilleure des manières tout en faisant des recommandations de produits.

                    ###CONTEXTE###
                    My Lubie est une marque de bien être intime inclusive. Elle vend des produits comme des préservatifs, lubrifiants, huile et jouets intimes.
                    Tu es implémenté via un chatbot sur le site internet de My Lubie. Les clients peuvent t'interroger sur des questions liées aux produits, à la marque en générale, à la sexualité ou aux commandes qu'ils ont passés.

                    ###DIRECTIVE DE REPONSE###
                    Dans ta manière de répondre, tu dois utiliser les mêmes éléments de language présent dans les documents dont tu as accès afin d'être au plus proche du ton de voix de My Lubie.
                    Ne fait pas des réponses trop longues.
                    Répond à la question en ajoutant les bons arguments sans trop en faire.
                    Ne cite surtout pas d'autres marques concurrentes de My Lubie.
                    Ne surtout pas répondre à des questions qui ne sont pas liées à My Lubie.
                    Si la question ne porte pas un sujet de My Lubie ou lié à la sexualité, alors répond une phrase générique et indique que tu ne peux que répondre dans un contexte de la marque.
                    Répond en écriture inclusive c'est à dire sans supposer le sexe de la personne a qui tu parles

                    ###TYPE DE RÉPONSE###
                    'En fonction du type de besoin, tu dois renvoyer le champ request_type associé '
                    'Le champ confidence_score doit déterminier ton niveau de certitude sur le type de question. Il vaut 0 si tu n''es pas sur du tout et il faut 1 si tu es sur et certain '
                    'Si on te dit des banalités (hello, ca va, bojour etc), répond dans le sens de la question et précise que tu peux répondre aux questions liées à la marque '
                    'Questions sur un produit -> return request_type= "product_info" '
                    'Question sur la marque -> return request_type= "faq" '
                    'Question sur une commande -> return request_type= "order" '
                    'Question ou phrase générique sans but précis ou hors contexte de MyLubie -> return request_type= "out_of_scope".
                    'Dans ce cas ou la question n'a pas de rapport avec la marque, répond une phrase agréable et explique tu ne peux que répondre dans un contexte de la marque'
                    'Si tu penses que l"utilisateur a des problemes, alors tu peux renseigner ces problemes dans le champ problem '
                    'Si l"utilisateur donne son nom tu peux retourner la valeur dans le champ name '
                    'Si l"utilisateur donne son numéro de commande tu peux retourner la valeur dans le champ order_number '
                    'Si l"utilisateur donne son email tu peux retourner la valeur dans le champ order_email '
                    'Tu dois renvoyer la liste des produits ou informations demandées par l''utilisateur dans le champ request_need
                    'Si un client indique avoir un probleme de commande, demande lui les informations : nom, email, numéro de commande afin de pouvoir comprendre le probleme rapidement
                    'La réponse textuelle qui sera envoyée au client doit etre dans le champ text_answer
                    '''


# -----------------------
# GLOBAL CONVERSATION HISTORY
# -----------------------
conversation_history = []


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
    text_answer : str


# -----------------------
# 1) DETERMINE USER REQUEST TYPE
# -----------------------
def users_requests_type(user_prompt: str,model='gpt-4o-mini'):

    add_message("user", user_prompt)
    response = client.responses.create(
        instructions=system_instruction,
        model = model,
        temperature= 1,
        input =conversation_history,
        tools=[{
            "type" : "file_search",
            "vector_store_ids" : ["vs_67dab4a9a6948191a48432a87b1e405c"]
        }],
        text={
        "format": {
            "type": "json_schema",
            "name": "lubie_reasonning",
            "schema": {
                "type": "object",
                "properties": {
                    "text_answer": {
                        "type": "string"
                    },
                    "request_type": {
                        "type": "string"
                    },
                    "confidence_score": {
                        "type": "number"
                    },
                    "client_problem" : {
                        "type" : "object",
                        "properties" : {
                            "request_needs": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "problems": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "name": {
                                "type": "string"
                            },
                            "email": {
                                "type": "string"
                            },
                            "order_number": {
                                "type": "string"
                            },
                        },
                        "required": ["request_needs", "problems", "name", "email", "order_number"],
                        "additionalProperties": False
                    }
                },
                "required": ["text_answer", "request_type", "confidence_score", "client_problem"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
    )
    add_message("assistant", (response.output_text))
    return json.loads(response.output_text)

# -----------------------
# 2) PRODUCT QUESTIONS
# -----------------------
def product(prompt):
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
# 5) Out of scope
# -----------------------
def oos(prompt):
    add_message("system", ("L'utilisateur pose une question ou dit quelque chose qui n'a pas de rapport direct avec MyLubie"
                            'Répond lui gentillement et indique tu peux répondre à toutes les questions concernant la marque MyLubie'))
    add_message("user", prompt)
    print(conversation_history)
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
    # if history!=None:
    #     add_message_full(history)
    print('in process')
    print(f"history length >>>>>>>>>> : {len(conversation_history)}")
    user_request = users_requests_type(user_prompt)
    print(user_request)
    return user_request['text_answer']

    if user_request.request_type == "product_info":
        return product(user_prompt)
    elif user_request.request_type == "faq":
        return faq(user_prompt)
    elif user_request.request_type == "order":
        return order(user_prompt, user_request)
    elif user_request.request_type == "out_of_scope":
        print("in oos")
        return oos(user_prompt)
    else:
        apology = "Pardonnez-moi, je ne pense pas pouvoir répondre à cela. Veuillez reformuler."
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
