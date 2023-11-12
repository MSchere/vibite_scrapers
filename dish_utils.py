from enum import Enum


class Nutrient(Enum):
    energy = "energy"
    fat = "fat"
    satFat = "satFat"
    protein = "protein"
    carbs = "carbs"
    sugar = "sugar"
    fiber = "fiber"
    salt = "salt"


class NutrientInfo:
    def __init__(self, value_100, value_total, unit):
        self.value_100 = value_100
        self.value_total = value_total
        self.unit = unit

class Platform(Enum):
    WETACA = "Wetaca"
    TAPPERS = "Tappers"
    PROZIS = "Prozis"
    NOCOCINOMAS = "Nococinomas"
    MENUDIET = "Menudiet"
    GUISOS = "Guisos"
    KNOWEATS = "Knoweats"
    MIPLATO = "MiPlato"

class Dish:
    platform = ""
    name = ""
    description = ""
    price = 0
    dish_url = ""
    image_url = ""
    weight = 0
    nutrients = {}
    ingredients = ""
    allergens = ""
    is_vegan = False
    is_gluten_free = False
    is_lactose_free = False
    nutri_score = ""
    score = 0
    is_available = True
    updated_at = 0

    # points, energy (kj), sugar (g), satFat(g), sodium (g)
    bad_nutrients_table = [
        ["points", Nutrient.energy, Nutrient.sugar,
            Nutrient.satFat, Nutrient.salt],
        [1, 335, 4.5, 1, 0.09],
        [2, 670, 9, 2, 0.18],
        [3, 1005, 13.5, 3, 0.27],
        [4, 1340, 18, 4, 0.36],
        [5, 1675, 22.5, 5, 0.45],
        [6, 2010, 27, 6, 0.54],
        [7, 2345, 31.5, 7, 0.63],
        [8, 2680, 36, 8, 0.72],
        [9, 3015, 40.5, 9, 0.81],
        [10, 3350, 45, 10, 0.90]
    ]
    # points, fiber (g), protein (g)
    good_nutrients_table = [
        ["points", Nutrient.fiber, Nutrient.protein],
        [1, 0.7, 1.6],
        [2, 1.4, 3.2],
        [3, 2.1, 4.8],
        [4, 2.8, 6.4],
        [5, 3.5, 8]
    ]

    points_table = [
        ["min", "max", "score"],
        [-15, -1, "A"],
        [0, 2, "B"],
        [3, 10, "C"],
        [11, 18, "D"],
        [19, 40, "E"]
    ]

    def __init__(self, platform, name, description, price, dish_url, image_url, weight, nutrients,
                 ingredients, allergens, is_vegan, is_gluten_free, is_lactose_free, updated_at):
        self.platform = platform
        self.name = name
        self.description = description
        self.price = price
        self.dish_url = dish_url
        self.image_url = image_url
        self.weight = weight
        self.nutrients = nutrients
        self.ingredients = ingredients
        self.allergens = allergens
        self.is_vegan = is_vegan
        self.is_gluten_free = is_gluten_free
        self.is_lactose_free = is_lactose_free
        self.updated_at = updated_at

    def calculate_nutriscore(self) -> int:
        points = 0
        for nutrient_name in self.nutrients:
            if nutrient_name == Nutrient.energy:
                for i in range(1, len(self.bad_nutrients_table)):
                    energy = self.nutrients[nutrient_name].value_100
                    if self.nutrients[nutrient_name].unit == "kcl":
                        energy = energy * 4.184
                    if energy < self.bad_nutrients_table[i][1]:
                        points += self.bad_nutrients_table[i][0]
                        break
            if nutrient_name == Nutrient.sugar or nutrient_name == Nutrient.satFat or nutrient_name == Nutrient.salt:
                for i in range(1, len(self.bad_nutrients_table)):

                    if self.nutrients[nutrient_name].value_100 > self.bad_nutrients_table[i][self.bad_nutrients_table[0].index(nutrient_name)]:
                        points += self.bad_nutrients_table[i][0]
                        break
            elif nutrient_name == Nutrient.fiber or nutrient_name == Nutrient.protein:
                for i in range(1, len(self.good_nutrients_table)):
                    if self.nutrients[nutrient_name].value_100 > self.good_nutrients_table[i][self.good_nutrients_table[0].index(nutrient_name)]:
                        points -= self.good_nutrients_table[i][0]
                        break

        for i in range(1, len(self.points_table)):
            if points >= self.points_table[i][0] and points <= self.points_table[i][1]:
                self.nutri_score = self.points_table[i][2]

                self.score = round((points - 40) / -55 * 10, 1)
                print("Calculated nutri-score: " + str(points) +
                      " - " + self.nutri_score + " - " + str(self.score) + " pts.")
                break

    def __str__(self):
        return f"{self.platform} - {self.name} - {self.price} € - {self.weight} - {self.ingredients} - {self.allergens} - {self.is_vegan} - {self.is_gluten_free} - {self.is_lactose_free} - {self.updated_at} - {self.nutri_score} - {self.score} pts."

    def print(self):
        print(self.__str__())
