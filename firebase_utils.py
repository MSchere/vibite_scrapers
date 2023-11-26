import os

import requests
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app, storage

load_dotenv()


class Firebase:
    cred = credentials.ApplicationDefault()
    initialize_app(cred, {
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "apiKey":  os.getenv("FIREBASE_API_KEY")
    })


def save_menu(dish_list):
    db = firestore.client()
    batch = db.batch()
    removals = "áéíóúñ "
    replacements = "aeioun-"
    translator = str.maketrans(removals, replacements)
    for dish in dish_list:
        doc_name = dish.platform.lower() + "-" + \
            dish.name.lower().translate(translator).replace(",", "")
        nutrients_dict = {}
        for name, info in dish.nutrients.items():
            nutrients_dict[name.name] = {
                "value100": info.value_100,
                "valueTotal": info.value_total,
                "unit": info.unit
            }
        firestore_image_url = upload_image_to_storage(dish, doc_name)
        data = {
            "platform": dish.platform,
            "name": dish.name,
            "description": dish.description,
            "price": dish.price,
            "dishUrl": dish.dish_url,
            "imageUrl": firestore_image_url,
            "weight": dish.weight,
            "nutrients": nutrients_dict,
            "ingredients": dish.ingredients,
            "allergens": dish.allergens,
            "isVegan": dish.is_vegan,
            "isGlutenFree": dish.is_gluten_free,
            "isLactoseFree": dish.is_lactose_free,
            "nutriScore": dish.nutri_score,
            "score": dish.score,
            "updatedAt": dish.updated_at,
            "isAvailable": True,
        }
        doc_ref = db.collection("dishes").document(doc_name)
        batch.set(doc_ref, data, merge=True)
    batch.commit()
    print(len(dish_list), "dishes saved to Firestore")


def upload_image_to_storage(dish, doc_name):
    bucket = storage.bucket("vibite-3ab78.appspot.com")
    try:
        folder_name = "dish_images"
        file_name = doc_name + ".jpg"
        blob = bucket.blob(f"{folder_name}/{file_name}")
        blob.upload_from_string(requests.get(
            dish.image_url).content, content_type="image/jpeg")
        blob.make_public()
        upload_url = blob.public_url
        print(f"{file_name} uploaded to Cloud Storage")
        return upload_url
    except Exception as e:
        print(f"Error uploading {file_name} to Cloud Storage: {e}")
