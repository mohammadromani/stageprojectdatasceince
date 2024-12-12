from datetime import datetime

from pymongo import MongoClient
import pandas as pd


def calculate_entity_trends(entity_type="locations"):

    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["almayadeen"]
    collection = db["articles"]

    # Fetch data
    data = list(collection.find({}, {"published_time": 1, f"my_entities.{entity_type}": 1}))

    # Extract entities and dates
    rows = []
    for doc in data:
        # Extract the timestamp, whether it's a native datetime or nested field
        timestamp = doc.get("published_time")
        if isinstance(timestamp, dict):  # Handle nested fields
            timestamp = timestamp.get("$date")
        if isinstance(timestamp, str):  # Handle string timestamps
            timestamp = float(timestamp)
        if isinstance(timestamp, (float, int)):  # Convert timestamp to datetime
            date = pd.to_datetime(timestamp, unit="ms")
        elif isinstance(timestamp, pd.Timestamp):  # If already a datetime, use directly
            date = timestamp
        elif isinstance(timestamp, datetime):  # Python datetime
            date = timestamp
        else:
            continue  # Skip invalid or missing timestamps

        # Extract entities of the given type
        entities = doc.get("my_entities", {}).get(entity_type, [])
        for entity in entities:
            rows.append({"date": date, "entity": entity["word"]})

    # Create a DataFrame
    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame(columns=["date", "entity", "count"])  # Return empty DataFrame if no data

    # Group by entities and time intervals, and count occurrences
    trend = df.groupby([df["date"].dt.to_period("M"), "entity"]).size().reset_index(name="count")
    trend["date"] = trend["date"].dt.to_timestamp()

    return trend

def calculate_entity_keyword_trends(keyword=""):

    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["almayadeen"]
    collection = db["articles"]

    # Fetch data
    data = list(collection.find({
            "$or": [
                {"my_entities.persons.word": keyword},
                {"my_entities.locations.word": keyword},
                {"my_entities.organizations.word": keyword}
            ]
        }, {
            "title": 1,
            "post_id": 1,
            "published_time": 1,
            "_id": 1
        }))

    # Extract entities and dates
    rows = []
    for doc in data:
        # Extract the timestamp, whether it's a native datetime or nested field
        timestamp = doc.get("published_time")
        if isinstance(timestamp, dict):  # Handle nested fields
            timestamp = timestamp.get("$date")
        if isinstance(timestamp, str):  # Handle string timestamps
            timestamp = float(timestamp)
        if isinstance(timestamp, (float, int)):  # Convert timestamp to datetime
            date = pd.to_datetime(timestamp, unit="ms")
        elif isinstance(timestamp, pd.Timestamp):  # If already a datetime, use directly
            date = timestamp
        elif isinstance(timestamp, datetime):  # Python datetime
            date = timestamp
        else:
            continue  # Skip invalid or missing timestamps

        # Extract entities of the given type
        entities = doc.get("my_entities", {}).get(entity_type, [])
        for entity in entities:
            rows.append({"date": date, "entity": entity["word"]})

    # Create a DataFrame
    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame(columns=["date", "entity", "count"])  # Return empty DataFrame if no data

    # Group by entities and time intervals, and count occurrences
    trend = df.groupby([df["date"].dt.to_period("M"), "entity"]).size().reset_index(name="count")
    trend["date"] = trend["date"].dt.to_timestamp()

    return trend


# Example Usage
if __name__ == "__main__":
    entity_type = "locations"  # Change to 'persons', 'organizations', etc. as needed
    entity_trends = calculate_entity_trends(entity_type=entity_type)
    print(entity_trends)
