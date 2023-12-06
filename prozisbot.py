import re
import time
import sys
import bot_utils
from dish_utils import Dish, Nutrient, NutrientInfo, Platform
from firebase_utils import save_menu

bot_title = '''

  _____              _     ____        _   
 |  __ \            (_)   |  _ \      | |  
 | |__) | __ ___ _____ ___| |_) | ___ | |_ 
 |  ___/ '__/ _ \_  / / __|  _ < / _ \| __|
 | |   | | | (_) / /| \__ \ |_) | (_) | |_ 
 |_|   |_|  \___/___|_|___/____/ \___/ \__|
                                           
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
HEADLESS = False
DEBUG = False

utils = bot_utils.Utils(browser=BROWSER,server=SERVER,  headless=HEADLESS, debug=DEBUG)
prozis_url = "https://www.prozis.com/es/es"

nutrient_lookup = {
    "Valor energético": Nutrient.energy,
    "Grasas": Nutrient.fat,
    "Saturadas": Nutrient.satFat,
    "Hidratos de Carbono": Nutrient.carbs,
    "Azúcares": Nutrient.sugar,
    "Fibra Alimentaria": Nutrient.fiber,
    "Proteínas": Nutrient.protein,
    "Sal": Nutrient.salt,
}

nutrient_regex = r"([A-Za-z áéíóú]+): ?(\d+\.?,?\d?) ?([a-zA-Z]+)?"

def get_dishes() -> list:
    cnt = 1
    drv = utils.drv
    section_dish_list = []
    while True:
        try:
            nutrients_dict = {}
            next_dish = utils.is_element_present(f"//*[@id='listSectionWrapper']/div[1]/div[{str(cnt)}]")
            if not next_dish:
                break
            utils.open_link_in_new_tab(f"//*[@id='listSectionWrapper']/div[1]/div[{str(cnt)}]/a")
            food_url = drv.current_url
            food_name = food_url.split("/")[-1].replace("-", " ")

            if (food_name.find("cubiertos") != -1) or  food_name.find("meal kit") != -1:
                drv.close()  # Return to previous page
                drv.switch_to.window(drv.window_handles[0])
                cnt += 1
                continue

            food_price = float(utils.get_text(
                "//*[@id='ob-product-price']")[1:])
            food_image = utils.get_image("//*[@id='pdp-gallery']/div/div[2]/div/div[2]/div/div/div/picture/img")
            food_description = utils.get_text_from_xpaths([
                "/html/body/div[6]/prz-pdpdesktop/div/article/div[3]/div/section[2]/div/div[2]/div/div/div/div/table/tr/td/div/div[2]/p",
                "/html/body/div[6]/prz-pdpdesktop/div/article/div[3]/div/section[2]/div/div[2]/div/div/div/div/table/tr/td/div/div[3]/p"])
            # Go to nutritional info tab
            utils.click("//*[@id='tab_NUTRITION_TABLE']")
            food_weight_str = utils.get_text("//*[@id='pdpTabsList']/div/div/div/div[1]/div[1]/div/p")
            match = re.search(nutrient_regex, food_weight_str)
            food_weight = float(match[2])
            food_ingredients = utils.get_text_from_xpaths([
                "//*[@id='pdpTabsList']/div/div/div/div[2]/div/div[1]/div[2]",
                "//*[@id='pdpTabsList']/div/div/div/div[2]/div/div[2]/div[2]"]).lower()
            food_allergens = utils.get_text_from_xpaths([
                "//*[@id='pdpTabsList']/div/div/div/div[2]/div/div[2]/div",
                "//*[@id='pdpTabsList']/div/div/div/div[2]/div/div[3]/div"]).lower()
            
            is_vegan = food_name.find("vegano") != -1
            is_vegan = food_name.find("veganos") != -1
            is_gluten_free = False
            is_lactose_free = False

            table_type = utils.get_text("//*[@id='pdpTabsList']/div/div/div/div[1]/div[2]/div[1]/button")
            for i in range(1, 9):
                nutrient_name = nutrient_lookup.get(utils.get_text(f"//*[@id='pdpTabsList']/div/div/div/div[1]/div[2]/div[3]/div[{i}]/strong"))
                nutrient_value_str = utils.get_text(f"//*[@id='pdpTabsList']/div/div/div/div[1]/div[2]/div[3]/div[{i}]/div[2]")                    
                nutrient_unit = nutrient_value_str.split(" ")[1]
                if (table_type == "Por Dosis"):
                    nutrient_value = float(nutrient_value_str.split(" ")[0])
                    nutrient_value_100 = nutrient_value / food_weight * 100
                else:
                    nutrient_value_100 = float(nutrient_value_str.split(" ")[0])
                    nutrient_value = nutrient_value_100 * food_weight / 100
                nutrients_dict[nutrient_name] = NutrientInfo(
                    nutrient_value_100, nutrient_value, nutrient_unit)

            drv.close()  # Return to previous page
            drv.switch_to.window(drv.window_handles[0])

            time_now = int(time.time())

            current_food = Dish(Platform.PROZIS.value, food_name, food_description, food_price, food_url, food_image, food_weight,
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

# Start
drv.get(prozis_url)
# Click accept cookies
utils.click("//*[@id='CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll']")

# Get dishes
dish_list = []
for i in range(1, 4):
    drv.get(f"https://www.prozis.com/es/es/alimentacion-saludable/congelados/platos/q/page/{i}")
    # Wait for page to load
    utils.get_text("//*[@id='listSectionWrapper']/div[1]")
    dish_list.extend(get_dishes())

drv.quit()  # Close webdriver
save_menu(dish_list)  # Save menu to Firestore
print("------------------------PROZISBOT END---------------------------")
