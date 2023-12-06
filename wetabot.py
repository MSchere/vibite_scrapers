import time
import sys
import bot_utils
from dish_utils import Dish, Nutrient, NutrientInfo, Platform
from firebase_utils import save_menu

bot_title = '''

 __          __  _        ____        _   
 \ \        / / | |      |  _ \      | |  
  \ \  /\  / /__| |_ __ _| |_) | ___ | |_ 
   \ \/  \/ / _ \ __/ _` |  _ < / _ \| __|
    \  /\  /  __/ || (_| | |_) | (_) | |_ 
     \/  \/ \___|\__\__,_|____/ \___/ \__|
                                          
                                          
'''

# This script scrapes the menu from Wetaca's website and saves it to Firestore
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
wetaca_url = "https://wetaca.com"
wetaca_menu_url = "https://wetaca.com/carta"

nutrient_lookup = {
    "Energía": Nutrient.energy,
    "Grasas totales": Nutrient.fat,
    "Grasas saturadas": Nutrient.satFat,
    "Proteínas": Nutrient.protein,
    "Carbohidratos": Nutrient.carbs,
    "Azúcares": Nutrient.sugar,
    "Fibra Dietética": Nutrient.fiber,
    "Sal": Nutrient.salt,
}


def get_dishes(div_id) -> list:
    cnt = 1
    drv = utils.drv
    section_dish_list = []
    while True:
        try:
            nutrients_dict = {}
            next_dish = utils.is_element_present(f"//*[@id=\"{div_id}\"]/div/div[{str(cnt)}]")
            if not next_dish:
                break
            utils.open_link_in_new_tab(f"//*[@id=\"{div_id}\"]/div/div[{str(cnt)}]/div/a")
            food_url = drv.current_url
            food_name = food_url.split("/")[-1].replace("-", " ")
            food_price = float(utils.get_text(
                "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[1]/div[2]/div[2]/div[1]")[:-1].replace(",", "."))
            food_description = utils.get_text(
                "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[1]/div[2]/div[1]/div[2]/div[2]/h2").lower()
            food_ingredients = utils.get_text(
                "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[2]/div[1]/p").lower()
            food_allergens = utils.get_text(
                "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[2]/div[1]/p/span").lower()
            food_ingredients = food_ingredients.replace(food_allergens, "")
            food_image = utils.get_image(
                "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[1]/div[1]/img")
            is_vegan = utils.is_class_present("icon-Vegan")
            is_lactose_free = utils.is_class_present("icon-Lactose")
            food_weight = float(utils.get_text(
                "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[2]/div[2]/table/tbody/tr[1]/td[3]").replace(",", ".").split(" ")[1])
            for i in range(2, 10):  # Get nutritional info from the nutrients table
                nutrient_name = nutrient_lookup.get(utils.get_text(
                    f"//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[2]/div[2]/table/tbody/tr[{str(i)}]/td[1]"), "")
                nutrient_str_100 = utils.get_text(
                    f"//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[2]/div[2]/table/tbody/tr[{str(i)}]/td[2]").replace(",", ".")

                nutrient_value_100 = float(nutrient_str_100.split(" ")[0])
                nutrient_value_total = nutrient_value_100 * food_weight / 100
                nutrient_unit = nutrient_str_100.split(" ")[1]
                nutrients_dict[nutrient_name] = NutrientInfo(
                    nutrient_value_100, nutrient_value_total, nutrient_unit)
            drv.close()  # Return to previous page
            drv.switch_to.window(drv.window_handles[0])

            time_now = int(time.time())

            current_food = Dish(Platform.WETACA.value, food_name, food_description, food_price, food_url, food_image, food_weight,
                                nutrients_dict, food_ingredients, food_allergens, is_vegan, False, is_lactose_free, time_now)
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
drv.get(wetaca_url)  # navigate to the application home page to load cookies
# Click accept cookies
utils.click("//*[@id='__next']/div/div/div/div[2]/div[3]/div[2]/button")
drv.get(wetaca_menu_url)
# Wait for first dish to load
utils.get_text("//*[@id='comidas']/div/div[1]/div/a/div[2]/div[1]")

# Get dishes
dish_list = []
dish_list.extend(get_dishes("comidas"))
dish_list.extend(get_dishes("comidas-ligeras-cenas"))
dish_list.extend(get_dishes("entrantes"))
dish_list.extend(get_dishes("postres"))

drv.quit()  # Close webdriver
save_menu(dish_list)  # Save menu to Firestore
print("------------------------WETABOT END---------------------------")
