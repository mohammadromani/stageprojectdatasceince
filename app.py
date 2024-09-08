from flask import Flask, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["almayadeen"]
collection = db["articles"]

# Existing Endpoints (unchanged)
@app.route('/top_keywords', methods=['GET'])
def top_keywords():
    pipeline = [
        {"$unwind": "$keywords"},
        {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/top_authors', methods=['GET'])
def top_authors():
    pipeline = [
        {"$group": {"_id": "$author", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/articles_by_date', methods=['GET'])
def articles_by_date():
    pipeline = [
        {"$group": {"_id": "$published_date", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}  # Sort by date
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/articles_by_word_count', methods=['GET'])
def articles_by_word_count():
    pipeline = [
        {"$project": {"word_count": {"$size": {"$split": ["$content", " "]}}}},
        {"$group": {"_id": "$word_count", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}  # Sort by word count
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)


@app.route('/articles_by_language', methods=['GET'])
def articles_by_language():
    total_articles = collection.count_documents({})  # Total number of articles
    pipeline = [
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = list(collection.aggregate(pipeline))

    # Calculate percentage for each language
    for language_data in result:
        language_data['percentage'] = (language_data['count'] / total_articles) * 100
    return jsonify(result)

@app.route('/articles_by_classes', methods=['GET'])
def articles_by_classes():
    pipeline = [
        {"$unwind": "$classes"},
        {"$group": {"_id": "$classes", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# New Endpoints

@app.route('/articles_by_keyword/<keyword>', methods=['GET'])
def articles_by_keyword(keyword):
    result = list(collection.find({"keywords": keyword}, {"title": 1, "_id": 0}))
    return jsonify(result)

@app.route('/articles_by_author/<author_name>', methods=['GET'])
def articles_by_author(author_name):
    result = list(collection.find({"author": author_name}, {"title": 1, "_id": 0}))
    return jsonify(result)

@app.route('/top_classes', methods=['GET'])
def top_classes():
    pipeline = [
        {"$unwind": "$classes"},
        {"$group": {"_id": "$classes", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/article_details/<postid>', methods=['GET'])
def article_details(postid):
    result = collection.find_one({"postid": postid}, {"_id": 0})
    return jsonify(result)

@app.route('/articles_with_video', methods=['GET'])
def articles_with_video():
    result = list(collection.find({"video_duration": {"$ne": None}}, {"title": 1, "_id": 0}))
    return jsonify(result)

@app.route('/articles_by_year/<int:year>', methods=['GET'])
def articles_by_year(year):
    pipeline = [
        {"$match": {"published_date": {"$regex": f"^{year}"}}},
        {"$count": "num_articles"}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/longest_articles', methods=['GET'])
def longest_articles():
    pipeline = [
        {"$project": {"title": 1, "word_count": {"$size": {"$split": ["$content", " "]}}}},
        {"$sort": {"word_count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/shortest_articles', methods=['GET'])
def shortest_articles():
    pipeline = [
        {"$project": {"title": 1, "word_count": {"$size": {"$split": ["$content", " "]}}}},
        {"$sort": {"word_count": 1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/articles_by_keyword_count', methods=['GET'])
def articles_by_keyword_count():
    pipeline = [
        {"$project": {"keyword_count": {"$size": "$keywords"}}},
        {"$group": {"_id": "$keyword_count", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/articles_with_thumbnail', methods=['GET'])
def articles_with_thumbnail():
    result = list(collection.find({"thumbnail": {"$ne": None}}, {"title": 1, "_id": 0}))
    return jsonify(result)

@app.route('/articles_updated_after_publication', methods=['GET'])
def articles_updated_after_publication():
    result = list(collection.find({"$expr": {"$gt": ["$last_updated", "$published_date"]}}, {"title": 1, "_id": 0}))
    return jsonify(result)

@app.route('/articles_by_coverage/<coverage>', methods=['GET'])
def articles_by_coverage(coverage):
    result = list(collection.find({"classes": coverage}, {"title": 1, "_id": 0}))
    return jsonify(result)

@app.route('/popular_keywords_last_X_days', methods=['GET'])
def popular_keywords_last_X_days():
    last_7_days = datetime.now() - timedelta(days=7)
    pipeline = [
        {"$match": {"published_date": {"$gte": last_7_days}}},
        {"$unwind": "$keywords"},
        {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/articles_by_month/<int:year>/<int:month>', methods=['GET'])
def articles_by_month(year, month):
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month + 1:02d}-01" if month < 12 else f"{year + 1}-01-01"
    pipeline = [
        {"$match": {"published_date": {"$gte": start_date, "$lt": end_date}}},
        {"$count": "num_articles"}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/articles_by_word_count_range/<int:min>/<int:max>', methods=['GET'])
def articles_by_word_count_range(min, max):
    pipeline = [
        {"$project": {"title": 1, "word_count": {"$size": {"$split": ["$content", " "]}}}},
        {"$match": {"word_count": {"$gte": min, "$lte": max}}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/articles_with_specific_keyword_count/<int:count>', methods=['GET'])
def articles_with_specific_keyword_count(count):
    result = list(collection.find({"$where": f"this.keywords.length == {count}"}, {"title": 1, "_id": 0}))
    return jsonify(result)

@app.route('/articles_by_specific_date/<date>', methods=['GET'])
def articles_by_specific_date(date):
    result = list(collection.find({"published_date": date}, {"title": 1, "_id": 0}))
    return jsonify(result)

@app.route('/articles_containing_text/<text>', methods=['GET'])
def articles_containing_text(text):
    result = list(collection.find({"content": {"$regex": text, "$options": "i"}}, {"title": 1, "_id": 0}))
    return jsonify(result)

@app.route('/articles_with_more_than/<int:word_count>', methods=['GET'])
def articles_with_more_than(word_count):
    pipeline = [
        {"$project": {"title": 1, "word_count": {"$size": {"$split": ["$content", " "]}}}},
        {"$match": {"word_count": {"$gt": word_count}}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/articles_grouped_by_coverage', methods=['GET'])
def articles_grouped_by_coverage():
    pipeline = [
        {"$unwind": "$classes"},
        {"$group": {"_id": "$classes", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/articles_last_X_hours', methods=['GET'])
def articles_last_X_hours():
    last_24_hours = datetime.now() - timedelta(hours=24)
    result = list(collection.find({"published_date": {"$gte": last_24_hours}}, {"title": 1, "_id": 0}))
    return jsonify(result)

@app.route('/articles_by_title_length', methods=['GET'])
def articles_by_title_length():
    pipeline = [
        {"$project": {"title_length": {"$size": {"$split": ["$title", " "]}}}},
        {"$group": {"_id": "$title_length", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/most_updated_articles', methods=['GET'])
def most_updated_articles():
    pipeline = [
        {"$project": {"title": 1, "update_count": {"$subtract": ["$last_updated", "$published_date"]}}},
        {"$sort": {"update_count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

if __name__ == '_main_':
    app.run(debug=True)