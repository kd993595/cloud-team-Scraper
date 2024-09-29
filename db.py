import mysql.connector
from hall_scraper import get_food

def init_DB(): 
  db = mysql.connector.connect(
    host ="localhost",
    user ="root",
    passwd ="dbuserdbuser",
    database = "db"
  )
 
  print(db)
  return db

def insert_food():
  db = init_DB()
  mycursor = db.cursor()

  dining_hall = "Ferris"
  food_list = get_food() #gets the list of food for the dining hall
  for food in food_list: #iterates through list, adding each food item
    print(food)
    sql = "INSERT INTO dining_food (hall, name) VALUES (%s, %s)" 
    val = (dining_hall, food)
    mycursor.execute(sql, val)
  
  db.commit() 

  mycursor.close()

  db.close()


def get_food_db():
    db = init_DB()
    mycursor = db.cursor()

    dining_hall = "Ferris"
    
    sql = "SELECT name FROM dining_food WHERE hall = %s"
    mycursor.execute(sql, (dining_hall,))

    food_list = mycursor.fetchall()
    food_items = [food[0] for food in food_list] #just cleaning the food items to return stirngs instead of arrays
    mycursor.close()
    db.close()
    return food_items




