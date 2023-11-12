import os

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
    for dish in dish_list:
        nutrients_dict = {}
        for name, info in dish.nutrients.items():
            nutrients_dict[name.name] = {
                "value100": info.value_100,
                "valueTotal": info.value_total,
                "unit": info.unit
            }
        data = {
            "platform": dish.platform,
            "name": dish.name,
            "description": dish.description,
            "price": dish.price,
            "dishUrl": dish.dish_url,
            "imageUrl": dish.image_url,
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
        removals = "áéíóúñ "
        replacements = "aeioun-"
        translator = str.maketrans(removals, replacements)
        doc_name = dish.platform.lower() + "-" + \
            dish.name.lower().translate(translator).replace(",", "")
        doc_ref = db.collection("dishes").document(doc_name)
        batch.set(doc_ref, data, merge=True)
    batch.commit()
    print(len(dish_list), "dishes saved to Firestore")


def upload_images_to_storage(dish_list):
    bucket = storage.bucket()
    for dish in dish_list:
        try:
            blob = bucket.blob(dish.image_url)
            blob.upload_from_filename(dish.image_path)
            print("Image uploaded to Cloud Storage")
        except Exception as e:
            print("Error uploading image to Cloud Storage", e)
