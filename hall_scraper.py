'''Scraper for Columbia Dining Website that extracts daily menu information.

Interacts with dynamic web pages and formats menu as dataframe.
Prepares for insertion into database table.

There is a main function for testing purposes.
External facing function for module interfacing is get_locs().

Typical usage example:

python3 main.py

from hall_scraper import get_locs
'''

# Imports
import time
import pandas as pd

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
skip_meals = ["All"]

def main():
    get_locs()

def get_locs():
    '''Gets URLs for dining hall landing pages.
    '''
    try:
        options = Options()

        # Don't load images
        options.add_argument('--blink-settings=imagesEnabled=false')
        #options.add_argument("--disable-gpu")
        options.add_argument("--log-level=1")

        driver = webdriver.Chrome(options=options)
        driver.get("https://dining.columbia.edu/")
    except Exception as e:
        print(f"ERROR: Unable to get webpage with chrome driver: {e}")

    try: # Wait for page to load
        wait = WebDriverWait(driver, 10)
        hall_menu = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="sitenav-1-second"]/div/ul/li[1]/ul')))
    except Exception as e:
        print(f"ERROR: Unable to load page: {e}")
        driver.quit()
        return -1

    try: # Open dining hall urls
        halls = hall_menu.find_elements(By.CSS_SELECTOR, 'li > a')
        urls = [h.get_attribute('href') for h in halls]
        for u in urls:
            _get_meals(driver, u)
    except Exception as e:
        print(f"ERROR: Unable to open dining hall URLS: {e}")
        driver.quit()
        return -1
    
    driver.quit()
    return 0

def _del_privacy(driver):
    '''Addresses privacy notice.

    If don't close privacy notice, can't click buttons for meal menu.

    Args:
        driver: Selenium Chrome webdriver
    '''
    try: #this removes any notices if there is any at the top of the page
        button = driver.find_elements(By.XPATH, '//*[@id="alert-8927"]/div/div[2]/i')
        if button:
            button.click()
            print("Clicked x button")
        else:
            print("X button not found")
    except Exception as e:
        print(f"Error handling x button: {e}")

    try: #accepts the privacy statement/cookies
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "cu-privacy-notice-close"))
        )
        button.click()
    except Exception as e:
        print(f"Error clicking privacy notice close.")
    time.sleep(2)

def _get_meals(driver, url):
    '''Gets food information for dining hall.

    Args:
        driver: Selenium Chrome webdriver
        url: Link to dining hall landing page.
    '''
    # driver = webdriver.Chrome()
    # driver.get("https://dining.columbia.edu/content/ferris-booth-commons-0")

    wait = WebDriverWait(driver, 10)

    print(f"New Tab: {url}")
    driver.execute_script(f"window.open('{url}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    try:
        dining_hall = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'node-title.ng-binding'))).text
        print(dining_hall)
    except:
        print(f"ERROR: Unable to get dining hall name.")
        return -1

    if dining_hall in ["Grace Dodge Dining Hall", "Robert F. Smith Dining Hall"]:
        # Grace Dodge doesn't have any menus to scrape.
        return -1
    _del_privacy(driver)

    meal_elems = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.cu-dining-menu-tabs button')))
    
    for m in meal_elems:
        meal = m.text
        if meal in skip_meals:
            continue

        print(f"meal: {meal}")

        m.click()
        station_elems = wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'station-title.ng-binding')))
        stations = [s.text for s in station_elems]
        food_container = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'meal-items')))

        for i in range(len(food_container)):
            print(f"\tstation:{stations[i]}")
            food_elems = food_container[i].find_elements(By.CLASS_NAME, 'meal-item.angular-animate.ng-trans-fade-down.ng-scope')
            
            for f in food_elems:
                food_name = f.find_element(By.TAG_NAME, 'h5').text
                print(f"\t\tfood: {food_name}")
                dietary_restriction = []
                allergen = []
                try:
                    dietary_restriction = f.find_element(By.TAG_NAME, 'strong').text.split(',')
                except NoSuchElementException as e:
                    #print("No dietary restrictions.")
                    pass
                
                try:
                    allergen = f.find_element(By.TAG_NAME, 'em').text.strip("Contains: ").split(',')
                except NoSuchElementException as e:
                    #print("No allergens.")
                    pass

                print(f"\t\t\tdietary restrictions:{', '.join(dietary_restriction)}")
                print(f"\t\t\tallergens: {', '.join(allergen)}")



    
 
if __name__ == "__main__":
    main()