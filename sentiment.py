from pymongo import MongoClient
from textblob import TextBlob

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["almayadeen"]
collection = db["articles"]

# Fetch and analyze articles
for article in collection.find():
    article_id = article['_id']  # MongoDB document ID
    text = article.get('full_text', '')

    # Perform sentiment analysis using TextBlob
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity  # Returns a value between -1 and 1

    # Update the sentiment back in MongoDB
    collection.update_one(
        {'_id': article_id},
        {'$set': {'sentiment': sentiment_score}}
    )

    print(f"Processed Article {article_id} with sentiment: {sentiment_score}")

print("Sentiment analysis completed.")
