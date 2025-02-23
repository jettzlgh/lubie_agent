import requests
import json

def fetch_shopify_products(store_url):
    """
    Fetch all products from a Shopify store using the public products.json endpoint.
    """
    endpoint = f"{store_url}/products.json"
    
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            products = response.json().get("products", [])
            return products
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def save_products_to_json(products,filename):
    """
    Save the retrieved products to a JSON file.
    """
    filename = 'testapi/'+filename
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(products, f,ensure_ascii=False, indent=4)
        print(f"Products saved to {filename}")
    except Exception as e:
        print(f"Error saving products: {e}")


shopify_store_url = "https://mylubie.com"
products = fetch_shopify_products(shopify_store_url)

if products:
    print(f"Total Products Retrieved: {len(products)}")
    save_products_to_json(products,'full_products.json')
    for product in products:  # Display first 5 products
        product.pop('images', None)
        product.pop('options', None)
    print(len(products))
    save_products_to_json(products,'reduced_products.json')
    # save_products_to_json(products)
