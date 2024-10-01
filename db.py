'''Inserts data from scraping into database.

'''
# Imports
import argparse
import os
import pandas as pd
import pickle as pkl

from datetime import datetime
from sqlalchemy import create_engine, text
from hall_scraper import get_daily

# import mysql.connector
# from hall_scraper import get_food

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-u', '--username', default='root')
	parser.add_argument('-p', '--password', default='dbuserdbuser')
	parser.add_argument('-s', '--server', default='localhost')
	parser.add_argument('-d', '--database', default='scraper_db')
	args = parser.parse_args()

	food_to_db(args.username, args.password, args.server, args.database)

def food_to_db(username, password, host, database):
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
		file = os.path.join("output", f"scrape_{date}.pkl")
		if os.path.exists(file):
			# Already scraped today, use previous data
			with open(file, 'rb') as handle:
				food_info = pkl.load(handle)
		else:
			# Scrape data
			food_info = get_daily()

		for k in food_info:
			print(f"Processing dining hall daily menu: {k}")
			df = food_info[k]
			for _, row in df.iterrows():
				try:
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
					
				try:
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

def execute_query(engine, query):
	try:
		with engine.connect() as conn:
			res = conn.execute(query)
	except Exception as e:
		print(f"Unable to execute query: {query[:20]}...")
		return

	return res

def food_exists(engine, database, table_name, row):
	try:
		with engine.connect() as conn:
			query = text(f"""
				SELECT EXISTS (
					SELECT * FROM {database}.table_name
					WHERE 
				)
			""")
	except Exception as e:
		print("ERROR: Table row exists query failed.")

def table_exists(engine, database, table_name):
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
	engine = create_engine("mysql+pymysql://root:dbuserdbuser@localhost")
	return engine

def df_to_db(df, table, schema, engine):
	try:
		df.to_sql(table, schema=schema, index=False, if_exists="append", con=engine)
	except Exception as e:
		print(f"ERROR: Failed inserting DataFrame into table {table} of schema {schema}.")
		return -1
	return 0

if __name__ == "__main__":
	main()