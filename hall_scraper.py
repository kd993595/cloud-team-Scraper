
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

#this is doing ferris breakfast for now, I used the same script on John Jay and it worked -- html might be consistent
def get_food():
    driver = webdriver.Chrome()
    driver.get("https://dining.columbia.edu/content/ferris-booth-commons-0")
    food_list = []


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
        button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "cu-privacy-notice-close"))
        )
        button.click()
    except Exception as e:
        print(f"Error clicking button: {e}")
    time.sleep(2)
    try: #this presses the breakfast button
        button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="cu_dining_locations-184"]/div[2]/div[3]/ul/li[2]/button'))
        )
        button.click()
    except Exception as e:
        print(f"Error clicking button: {e}")

    try: #obtains all the breakfast items
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "meal-title ng-binding"))
        )
    except Exception as e:
        print(f"Error waiting for meals to load: {e}")

    page_to_scrape = driver.page_source #this is beautiful soup scraping the results now
    soup = BeautifulSoup(page_to_scrape, 'html.parser')

    food = soup.findAll("h5", class_="meal-title ng-binding")

    for result in food: #changing the results to stirngs then adding them to an array
        text = result.text.strip()
        food_list.append(text)
        
    print(food_list)
    driver.quit()
    return food_list
 