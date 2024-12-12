from pymongo import MongoClient, UpdateOne
from transformers import pipeline
import torch
import numpy as np

print(torch.__version__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["almayadeen"]
collection = db["articles"]

# Load the NER pipeline for Arabic entity extraction
ner = pipeline('ner', model='CAMeL-Lab/bert-base-arabic-camelbert-ca-ner')

batch_size = 50
updated_documents = []
batch_operations = []

def truncate_text(text, max_length=512):
    """Truncate text to fit the BERT model's input size."""
    return text[:max_length]

def convert_floats(ner_results):
    for entity in ner_results:
        for key in entity:
            if isinstance(entity[key], np.floating):
                entity[key] = float(entity[key])
    return ner_results

# Process only 10 documents from MongoDB
for doc in collection.find():
    try:
        text = doc.get("full_text", "")
        post_id = doc.get("post_id", "Unknown")
        # print(post_id)

        # Truncate text to ensure it fits the BERT model's input size
        text = truncate_text(text)


        # Extract named entities
        ner_results = ner(text)

        ner_results = convert_floats(ner_results)

        # Organize entities into categories (people, locations, organizations)
        organized_entities = {
            "persons": [],
            "locations": [],
            "organizations": []
        }

        for entity in ner_results:
            entity_type = entity.get("entity")
            word = entity.get("word")
            score = entity.get("score", 0)

            if entity_type.startswith("B-PER"):
                organized_entities["persons"].append({"word": word, "score": score})
            elif entity_type.startswith("B-LOC"):
                organized_entities["locations"].append({"word": word, "score": score})
            elif entity_type.startswith("B-ORG"):
                organized_entities["organizations"].append({"word": word, "score": score})

        batch_operations.append(
            UpdateOne({"_id": doc["_id"]}, {"$set": {"my_entities": organized_entities}})
        )

        if len(batch_operations) >= batch_size:
            collection.bulk_write(batch_operations)
            batch_operations.clear()

    except Exception as e:
        print(f"Error processing document {doc.get('post_id', 'Unknown')}: {str(e)}")

if batch_operations:
    collection.bulk_write(batch_operations)

print("Named entities extraction and updates completed.")
