import time

import bot_utils
from dish_utils import Dish, NutrientInfo, Nutrients
from firebase_utils import save_menu

''' 
 __          __  _        _           _   
 \ \        / / | |      | |         | |  
  \ \  /\  / /__| |_ __ _| |__   ___ | |_ 
   \ \/  \/ / _ \ __/ _` | '_ \ / _ \| __|
    \  /\  /  __/ || (_| | |_) | (_) | |_ 
     \/  \/ \___|\__\__,_|_.__/ \___/ \__|
                                          
    This script scrapes the menu from Wetaca's website and saves it to Firestore
    Maintenance is required when the website changes or new popups are added.
'''

HEADLESS = True
DEBUG = False

utils = bot_utils.Utils(debug=DEBUG)
# CONFIGURATION
wetaca_url = "https://wetaca.com"
wetaca_menu_url = "https://wetaca.com/carta"

nutrient_lookup = {
    "Energía": Nutrients.ENERGY,
    "Grasas totales": Nutrients.FAT,
    "Grasas saturadas": Nutrients.SATFAT,
    "Proteínas": Nutrients.PROTEIN,
    "Carbohidratos": Nutrients.CARBS,
    "Azúcares": Nutrients.SUGAR,
    "Fibra Dietética": Nutrients.FIBER,
    "Sal": Nutrients.SALT,
}


def get_dishes(div_id) -> list:
    cnt = 1
    drv = utils.drv
    section_dish_list = []
    while True:
        try:
            nutrients_dict = {}
            food_name = utils.find(
                "//*[@id=\""+div_id+"\"]/div/div["+str(cnt)+"]/div/a/div[2]/div[1]")
            utils.open_link_in_new_tab(
                "//*[@id=\""+div_id+"\"]/div/div["+str(cnt)+"]/div/a")
            food_price = float(utils.get_text(
                "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[1]/div[2]/div[2]/div[1]")[:-1].replace(",", "."))
            food_description = utils.get_text(
                "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[1]/div[2]/div[1]/div[2]/div[2]/h2")
            food_ingredients = utils.get_text(
                "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[2]/div[1]/p")
            food_allergens = utils.get_text(
                "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[2]/div[1]/p/span")
            food_ingredients = food_ingredients.replace(food_allergens, "")
            food_image = utils.get_image(
                "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[1]/div[1]/img")
            for i in range(2, 10):  # Get nutritional info from the nutrients table
                nutrient_name = nutrient_lookup.get(utils.get_text(
                    "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[2]/div[2]/table/tbody/tr["+str(i)+"]/td[1]"), "")
                nutrient_str_100 = utils.get_text(
                    "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[2]/div[2]/table/tbody/tr["+str(i)+"]/td[2]").replace(",", ".")
                nutrient_str_total = utils.get_text(
                    "//*[@id='__next']/div/div/div/div[2]/div[3]/div/div[2]/div[2]/table/tbody/tr["+str(i)+"]/td[3]").replace(",", ".")

                nutrient_value_100 = float(nutrient_str_100.split(" ")[0])
                nutrient_value_total = float(nutrient_str_total.split(" ")[0])
                nutrient_unit = nutrient_str_100.split(" ")[1]
                nutrients_dict[nutrient_name] = NutrientInfo(
                    nutrient_value_100, nutrient_value_total, nutrient_unit)
            drv.close()  # Return to previous page
            drv.switch_to.window(drv.window_handles[0])

            time_now = int(time.time())

            current_food = Dish(food_name, food_description, food_price, food_image,
                                nutrients_dict, food_ingredients, food_allergens, False, False, False, time_now)
            current_food.calculate_nutriscore()
            current_food.print()
            section_dish_list.append(current_food)
            cnt += 1
        except (Exception, ValueError) as error:
            if (str(error).startswith("Unable to locate element")):
                print("No more dishes in this section")
            else:
                print("Error:", error)
                break
            return section_dish_list  # Return the list of dishes in the section


# BEGIN SCRIPT
print("---------------------------WETABOT---------------------------")
# Initialize webdriver
drv = utils.setup_driver("firefox", headless=HEADLESS)
drv.get(wetaca_url)  # navigate to the application home page to load cookies
# Click accept cookies
utils.click("//*[@id='__next']/div/div/div/div[2]/div[3]/div[2]/button")
drv.get(wetaca_menu_url)
# Get menu date
utils.get_text("//*[@id='__next']/div/div/div/div[2]/div/div/div[2]/p")

# Get dishes
dish_list = []
dish_list.extend(get_dishes("comidas"))
dish_list.extend(get_dishes("comidas-ligeras-cenas"))
dish_list.extend(get_dishes("entrantes"))
dish_list.extend(get_dishes("postres"))

drv.quit()  # Close webdriver
save_menu(dish_list)  # Save menu to Firestore
print("--------------------------------------------------------------")
