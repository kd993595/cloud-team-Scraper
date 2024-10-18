'''Inserts data from scraping into database.

Works with two tables:
	1. "food": master menu with all food items scraped to date
			without associated to date
	2. "daily": menu of what food items are available for certain date

If there is data in output folder for given date, uses already scraped data.
If not, calls scraper to get data.

There is a main function for testing purposes.
External functions:
	food_to_db: Inserts food items into database tables.
	get_daily: Returns food items and their info for given date.
'''

# Imports
import argparse
import os
import pandas as pd

from datetime import datetime
from sqlalchemy import create_engine, text
from hall_scraper import scrape_daily

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-u', '--username', default='root')
	parser.add_argument('-p', '--password', default='dbuserdbuser')
	parser.add_argument('-s', '--server', default='localhost')
	parser.add_argument('-d', '--database', default='scraper_db')
	parser.add_argument('--date', default=datetime.now().strftime(f'%Y-%m-%d'))
	parser.add_argument('-o', '--output', default='output')
	args = parser.parse_args()

	scrape_to_db(args.username, args.password, args.server, args.database, args.output, args.date)
	get_daily(args.username, args.password, args.server, args.database, args.date)

def scrape_to_db(username, password, host, database, output, date):
	"""Inserts food items into database tables.

	Inserts each food item into both master and daily tables, 
	checking integrity before insertion.

	Args:
		username: MySQL user
		password: password for user
		server: host IP address
		database: name of database (schema)
		output: folder in which to find CSV file with scraped data
		date: date from which to insert data
	"""
	engine = get_engine(username, password, host)

	with engine.connect() as conn:
		# Create food table if not exists
		if not table_exists(engine, database, "food"):
			try:
				query = text(f"""
					CREATE TABLE {database}.food(
						food_id INT NOT NULL AUTO_INCREMENT,
						food_name VARCHAR(255) NOT NULL,
						dietary_restriction VARCHAR(255),
						allergen VARCHAR(255),
						description VARCHAR(255),
						dining_hall VARCHAR(255) NOT NULL,
						meal VARCHAR(255) NOT NULL,
						station VARCHAR(255) NOT NULL,
						PRIMARY KEY (food_id)
					);"""
				)
				conn.execute(query)
				conn.commit()
			except Exception as e:
				print(f"ERROR: Failed creating table: {e}")
			else:
				print(f"Created table: {database}.food")
		else:
			print(f"Table exists: {database}.food")
		
		# Create daily table if not exists
		if not table_exists(engine, database, "daily"):
			try:
				query = text(f"""
					CREATE TABLE {database}.daily(
						daily_id INT NOT NULL AUTO_INCREMENT,
						food_id INT NOT NULL,
						date DATE NOT NULL,
						PRIMARY KEY (daily_id),
						FOREIGN KEY (food_id) REFERENCES {database}.food(food_id) ON DELETE CASCADE ON UPDATE CASCADE
					);""")
				conn.execute(query)
				conn.commit()
			except Exception as e:
				print(f"ERROR: Failed creating table: {e}")
			else:
				print(f"Created table: {database}.daily")
		else:
			print(f"Table exists: {database}.daily")


		# Get food information dictionary
		date = datetime.now().strftime(f'%Y-%m-%d')
		
		file = os.path.join(output, f"scrape_{date}.csv")
		if os.path.exists(file):
			# Already scraped today, use previous data
			df = pd.read_csv(file)
		else:
			# Scrape data
			df = scrape_daily()

		for _, row in df.iterrows():
			try: # Insert food item into master menu
				cols = row.index
				vals = [f'"{r}"' for r in row.values]
				where = [f'{cols[i]}="{row.values[i]}"' for i in range(len(cols))]

				# Insertion into master menu
				query = text(f"SELECT * FROM {database}.food WHERE {' AND '.join(where)};")
				res = conn.execute(query)
				if not res.fetchall():
					# Food item not already in master menu
					query = text(f"INSERT INTO {database}.food ({', '.join(cols)}) VALUES ({', '.join(vals)});")
					conn.execute(query)
					conn.commit()
					print(f"\tInserted item into {database}.food: {row[0]} ")
			except Exception as e:
				print(f"\tERROR: Failed insertion into {database}.food: {e}")
				
			try: # Insert food item into daily menu
				query = text(f"SELECT food_id FROM {database}.food WHERE {' AND '.join(where)};")
				food_id = conn.execute(query).scalar()

				query = text(f"SELECT * FROM {database}.daily WHERE food_id={food_id} and date='{date}'")
				res = conn.execute(query)
				if not res.fetchall():
					query = text(f"INSERT INTO {database}.daily (date, food_id) VALUES('{date}', '{food_id}')")
					conn.execute(query)
					conn.commit()
					print(f"\tInserted item into {database}.daily: {row[0]}")
			except Exception as e:
				print(f"\tERROR: Failed insertion into {database}.daily: {e}")

def get_daily(username, password, host, database, date):
	"""Gets food items and their info for specified date.

	Args:
		username: MySQL user
		password: password for user
		server: host IP address
		database: name of database (schema)
		date: YYYY-MM-DD to match date attribute in daily table

	Returns:
		DataFrame with food item information for given date.
	"""
	engine = get_engine(username, password, host)
	query = text(f"""
		SELECT * 
			FROM (
				SELECT * FROM {database}.daily
				WHERE date='{date}') AS today
		LEFT JOIN {database}.food
			ON today.food_id = food.food_id;""")
	df = pd.DataFrame(execute_query(engine, query).fetchall())
	return df

def execute_query(engine, query):
	"""Executes a SQL query.

	Args:
		engine: engine object for server connection (not database)
		query: string with SQL query
	
	Returns:
		Information returned from query.
	"""
	try:
		with engine.connect() as conn:
			res = conn.execute(query)
	except Exception as e:
		print(f"Unable to execute query: {query[:20]}...")
		return
	
	return res

def table_exists(engine, database, table_name):
	"""Check if table exists.

	Args:
		engine: engine object for server connection (not database)
		database: Database (schema) name
		table_name: Name of table within schema
	
	Returns:
		Table name if it exists. Else returns None.
	"""
	try:
		with engine.connect() as conn:
			query = text(f"""SELECT TABLE_NAME
				FROM INFORMATION_SCHEMA.TABLES 
				WHERE TABLE_SCHEMA = '{database}' 
				AND TABLE_NAME = '{table_name}';""")
			res = conn.execute(query)
			return res.fetchall()
	except Exception as e:
		print("ERROR: Table exists query failed.")
	return

def get_engine(username, password, host):
	"""Construct engine object.

	Args:
		username: MySQL user
		password: password for user
		host: host IP address
	"""
	engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}")
	return engine

if __name__ == "__main__":
	main()