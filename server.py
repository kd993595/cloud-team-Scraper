from flask import request, Flask, jsonify
from flask_cors import CORS
from db import insert_food, get_food_db
from hall_scraper import get_food
app = Flask(__name__)
cors = CORS(app)

@app.route("/test", methods=["GET"])
def test():
    
    response = "hello"
    response = {"test": response}
    return jsonify(response), 200

@app.route("/getfood", methods=["GET"])
def food():
    
    response = get_food_db()
    response = {"food_items": response}
    return jsonify(response), 200



if __name__ == "__main__":
    app.run(host='localhost', port=8080)