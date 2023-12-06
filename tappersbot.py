import re
import time
import sys
import bot_utils
from dish_utils import Dish, Nutrient, NutrientInfo, Platform
from firebase_utils import save_menu

bot_title = '''

  _______                              ____        _   
 |__   __|                            |  _ \      | |  
    | | __ _ _ __  _ __   ___ _ __ ___| |_) | ___ | |_ 
    | |/ _` | '_ \| '_ \ / _ \ '__/ __|  _ < / _ \| __|
    | | (_| | |_) | |_) |  __/ |  \__ \ |_) | (_) | |_ 
    |_|\__,_| .__/| .__/ \___|_|  |___/____/ \___/ \__|
            | |   | |                                  
            |_|   |_|                                  
       
'''
# This script scrapes the menu from Tappers' website and saves it to Firestore
# Maintenance is required when the website changes or new popups are added.
if len(sys.argv) < 1:
    print("Usage: python prozisbot.py <browser> [server]")
    sys.exit(1)
BROWSER = sys.argv[1]
SERVER = False
if len(sys.argv) > 2:
    SERVER = sys.argv[2] == "server"
HEADLESS = True
DEBUG = False

utils = bot_utils.Utils(browser=BROWSER,server=SERVER,  headless=HEADLESS, debug=DEBUG)
# CONFIGURATION
tappers_url = "https://www.tappers.es/a-domicilio/todos/"

nutrient_regex = r"([A-Za-z áéíóú]+): ?(\d+\.?,?\d?) ?([a-zA-Z]+)?"
name_regex = r"([A-Za-z -ñáéíóúÁÉÍÓÚ]+) \((\d+) ?([a-zA-Z]+)\.\)"

nutrient_lookup = {
    "energía": Nutrient.energy,
    "grasas": Nutrient.fat,
    "de las cuales ags": Nutrient.satFat,
    "de las cuales saturadas": Nutrient.satFat,
    "proteínas": Nutrient.protein,
    "hidratos de carbono": Nutrient.carbs,
    "hidratos de c": Nutrient.carbs,
    "de los cuales azúcar": Nutrient.sugar,
    "de los cuales azúcares": Nutrient.sugar,
    "los cuales azúcar": Nutrient.sugar,
    "fibra dietética": Nutrient.fiber,
    "fibra alimentaria": Nutrient.fiber,
    "sal": Nutrient.salt,
}


def get_dishes(section_id) -> list:
    cnt = 1
    drv = utils.drv
    section_dish_list = []
    while True:
        try:
            nutrients_dict = {}
            next_dish = utils.is_element_present(
                f"//*[@id='content']/div/section[{section_id}]/div/div/div/div[4]/div/div/ul/li[{str(cnt)}]")
            if not next_dish:
                break
            utils.open_link_in_new_tab(
                f"//*[@id='content']/div/section[{section_id}]/div/div/div/div[4]/div/div/ul/li[{str(cnt)}]/a[1]"
            )
            food_url = drv.current_url
            name_str = utils.get_text(
                "//*[@id='content']/div[2]/section[1]/div/div[2]/div/div[1]/div/h1")
            match = re.search(name_regex, name_str)
            food_name = match[1]
            food_weight = float(match[2])

            food_price = float(utils.get_text(
                "//*[@id='content']/div[2]/section[1]/div/div[2]/div/section[1]/div/div[1]/div/div/div/p/span/bdi")[:-1].replace(",", "."))
            food_description = utils.get_text_from_xpaths(
                ["//*[@id='content']/div[2]/section[1]/div/div[2]/div/div[2]/div/div/p",
                 "//*[@id='content']/div[2]/section[1]/div/div[2]/div/div[3]/div/div/p"]
            )
            food_image = utils.get_image_from_xpaths(
                ["//*[@id='content']/div[2]/section[1]/div/div[1]/div/div/div/div/div/div/div[1]/img",
                 "//*[@id='content']/div[2]/section[1]/div/div[1]/div/div/div/div/div/div/img"]
            )

            food_ingredients = utils.get_text(
                "//*[@id='tab-informacion-completa']/table/tbody[2]/tr[1]/td").lower()

            is_gluten_free = False
            gluten_free_div = "//*[@id='content']/div[2]/section[1]/div/div[1]/div/div/div/div/div/div/div/div/div/div"
            if (utils.is_element_present(gluten_free_div)):
                if utils.get_text(gluten_free_div) == "Sin gluten":
                    is_gluten_free = True

            is_vegan = False
            vegan_div = "//*[@id='content']/div[2]/section[1]/div/div[1]/div/div/div/div/div/div/div[1]/div/div/div/div"
            if (utils.is_element_present(vegan_div)):
                if utils.get_text(vegan_div) == "Veganos":
                    is_vegan = True

            is_lactose_free = False
            nutrients_str = utils.get_text(
                "//*[@id='tab-informacion-completa']/table/tbody[2]/tr[6]/td")

            for match in re.findall(nutrient_regex, nutrients_str):
                nutrient = match[0].strip().lower()
                nutrient_value_100 = float(match[1].replace(",", "."))
                nutrient_unit = match[2].lower() if match[2] else "g"
                nutrient_name = nutrient_lookup[nutrient]
                if nutrient_unit == "kj":
                    continue
                if nutrient_unit == "kcal":
                    nutrient_unit = "kcl"
                nutrient_value_total = nutrient_value_100 * food_weight / 100
                nutrients_dict[nutrient_name] = NutrientInfo(
                    nutrient_value_100, nutrient_value_total, nutrient_unit)

            food_allergens = ""  # TODO: Get allergens from the allergens table
            drv.close()  # Return to previous page
            drv.switch_to.window(drv.window_handles[0])

            time_now = int(time.time())

            current_food = Dish(Platform.TAPPERS.value, food_name, food_description, food_price, food_url, food_image, food_weight,
                                nutrients_dict, food_ingredients, food_allergens, is_vegan, is_gluten_free, is_lactose_free, time_now)
            current_food.calculate_nutriscore()
            current_food.print()
            section_dish_list.append(current_food)
            cnt += 1
        except (Exception, ValueError) as error:
            print("Error:", error)
            drv.close()  # Return to previous page
            drv.switch_to.window(drv.window_handles[0])
            continue
    print("No more dishes in this section")
    return section_dish_list  # Return the list of dishes in the section


# BEGIN SCRIPT
print(bot_title)
# Initialize webdriver
drv = utils.setup_driver()
# Go to website
drv.get(tappers_url)
# Wait for section to load
utils.get_text("//*[@id='content']/div/section[4]")

# Get dishes
dish_list = []
dish_list.extend(get_dishes("4"))
dish_list.extend(get_dishes("6"))
dish_list.extend(get_dishes("8"))
dish_list.extend(get_dishes("9"))

drv.quit()  # Close webdriver
save_menu(dish_list)  # Save menu to Firestore
print("------------------------TAPPERSBOT END---------------------------")
