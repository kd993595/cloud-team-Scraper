'''Scraper for Columbia Dining Website that extracts daily menu information.

Interacts with dynamic web pages and formats menu as dataframe.
Prepares for insertion into database table.

There is a main function for testing purposes.
External functions:
    scrape_daily: Gets today's data from Columbia Dining website.
'''

# Imports
import pandas as pd
import os.path
import time

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Global Variables
skip_meals = ["All"]
columns = ["food_name", "dietary_restriction", "allergen", "description", "dining_hall", "meal", "station"]

def main():
    print(scrape_daily())

def scrape_daily():
    '''Gets today's data from Columbia Dining website.
    
    Gets URLs for dining hall pages and calls _scrape_meals
    to scrape data for dining hall.

    Returns:
        On success, a DataFrame with info from all dining halls
        in the following columns:
            food_name
            dietary_restriction: e.g., Gluten Free, Halal, Vegan
            allergen: e.g., Eggs, Shellfish, Soy, Wheat
            description: notable ingredients
            dining_hall
            meal: meal of the day (e.g., Breakfast)
            station: e.g., Main Line, Action Station, Soup Station
        
        On failure, -1.
    '''
    hall_list = [] # Intialize empty DataFrame

    try: # Open Columbia Dining main page
        options = Options()

        # Don't load images
        options.add_argument('--blink-settings=imagesEnabled=false')
        #options.add_argument("--disable-gpu")
        options.add_argument("--log-level=1")
        # Hide UI window
        #options.add_argument("--headless=new")

        driver = webdriver.Chrome(options=options)
        driver.get("https://dining.columbia.edu/")
        time.sleep(5)
    except Exception as e:
        print(f"ERROR: Unable to get webpage with chrome driver: {e}")
        return -1

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
        for i in range(len(urls)):
            dining_hall, df  = _scrape_meals(driver, urls[i])
            if dining_hall == -1:
                continue
            hall_list.append(df)
    except Exception as e:
        print(f"ERROR: Unable to open dining hall URLS: {e}")
        driver.quit()
        return -1
    
    driver.quit()

    food_df = pd.concat(hall_list).reset_index(drop=True)
    filename = os.path.join("output", f"scrape_{datetime.now().strftime('%Y-%m-%d')}.csv")
    food_df.to_csv(filename, index=False)

    return food_df

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

def _scrape_meals(driver, url):
    '''Gets food information for dining hall.

    Args:
        driver: Selenium Chrome webdriver
        url: Link to dining hall landing page.
        privacy: Whether to close privacy notice (that blocks food information).
            Only necessary for first dining hall.

    Returns:
        DataFrame where each row contains information for one food item
        with the following columns:
            food_name
            dietary_restriction
            allergen
            description
            meal
            station
            dining_hall
    '''
    
    wait = WebDriverWait(driver, 10)

    # Open new tab and go to dining hall web page
    print(f"New Tab: {url}")
    driver.execute_script(f"window.open('{url}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    try: # Wait for dining hall name to load
        dining_hall = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'node-title.ng-binding'))).text
        print(dining_hall)
    except:
        print(f"\tERROR: Unable to get dining hall name.")
        return -1, -1
    
    # Remove privacy notice
    _del_privacy(driver)

    try: # Wait for menu of meals
        meal_elems = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.cu-dining-menu-tabs button')))
    except Exception as e:
        print(f"\tERROR: Unable to retrieve menu or no menu.")
        return -1, -1
    
    food_list = []

    # Iterate through each meal of the day
    for m in meal_elems:
        meal = m.text
        if meal in skip_meals: # Exclude hard-coded meals (e.g., ALl)
            continue

        # Choose meal of day and wait for food items to load
        m.click()
        station_elems = wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'station-title.ng-binding')))
        stations = [s.text for s in station_elems]
        food_container = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'meal-items')))

        # Iterate through stations
        for i in range(len(food_container)):
            food_elems = food_container[i].find_elements(By.CLASS_NAME, 'meal-item.angular-animate.ng-trans-fade-down.ng-scope')
            
            # Iterate through station food items
            for f in food_elems:
                food_name = f.find_element(By.TAG_NAME, 'h5').text
                dietary_restriction = ''
                allergen = ''
                description = ""
                try:
                    dietary_restriction = f.find_element(By.TAG_NAME, 'strong').text
                except NoSuchElementException as e:
                    pass
                
                try:
                    allergen = f.find_element(By.TAG_NAME, 'em').text.replace("Contains: ", "")
                except NoSuchElementException as e:
                    pass

                try:
                    description = f.find_element(By.CLASS_NAME, 'meal-description.ng-binding.ng-scope').text
                except NoSuchElementException as e:
                    pass
                
                food_list.append([food_name, dietary_restriction, allergen, description, dining_hall, meal, stations[i]])

    df = pd.DataFrame(data=food_list, columns=columns)
    return dining_hall, df
    
 
if __name__ == "__main__":
    main()