import pymongo
import json
import os
from datetime import datetime

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["almayadeen"]  # Create/use a database named "almayadeen"
collection = db["articles"]  # Create/use a collection named "articles"

# Directory containing JSON files
directory = 'scraped_articles'

# Loop through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.json'):
        file_path = os.path.join(directory, filename)
        # Load JSON data from file
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        for article in data:
            if 'published_time' in article and isinstance(article['published_time'], str):
                article['published_time'] = datetime.fromisoformat(article['published_time'])
            if 'last_updated' in article and isinstance(article['last_updated'], str):
                article['last_updated'] = datetime.fromisoformat(article['last_updated'])

        # Insert data into the MongoDB collection
        try:
            if isinstance(data, list):
                collection.insert_many(data)  # Use insert_many if data is a list of dictionaries
                print(f"Successfully inserted {len(data)} articles from {filename} into MongoDB.")
            else:
                collection.insert_one(data)  # Use insert_one if it's a single dictionary
                print(f"Successfully inserted one article from {filename} into MongoDB.")
        except pymongo.errors.BulkWriteError as e:
            print(f"Error inserting data from {filename}: {e.details}")
        except Exception as e:
            print(f"An error occurred while inserting data from {filename}: {e}")