# from crypt import methods

from flask import Flask, jsonify, Response, request
from pymongo import MongoClient
from datetime import datetime, timedelta
from flask_cors import CORS
import trendCalc
app = Flask(__name__)
CORS(app, supports_credentials=True)

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

@app.route('/top_keywords_by_time', methods=['GET'])
def top_keywords_by_time():
    # Get start and end dates from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not start_date_str or not end_date_str:
        return jsonify({"error": "Please provide start_date and end_date"}), 400
    # print(type(start_date))

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    print(start_date)
    try:
        pipeline = [
            {"$match": {"published_time": {"$gte": start_date, "$lte": end_date}}},
            {"$unwind": "$keywords"},
            {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]

        result = list(collection.aggregate(pipeline))
        print(result)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/top_authors', methods=['GET'])
def top_authors():
    pipeline = [
        {"$group": {"_id": "$author", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)
#
# @app.route('/articles_by_date', methods=['GET'])
# def articles_by_date():
#     pipeline = [
#         {"$group": {"_id": "$published_time", "count": {"$sum": 1}}},
#         {"$sort": {"_id": 1}}  # Sort by date
#     ]
#     result = list(collection.aggregate(pipeline))
#     return jsonify(result)
@app.route('/articles_by_date', methods=['GET'])
def articles_by_date():
    pipeline = [
        {
            # Convert published_time to a date string (YYYY-MM-DD)
            "$addFields": {
                "published_date": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$published_time"}
                }
            }
        },
        {
            # Group articles by the formatted date
            "$group": {"_id": "$published_date", "count": {"$sum": 1}}
        },
        {
            # Sort by date
            "$sort": {"_id": 1}
        }
    ]

    result = list(collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/articles_by_word_count', methods=['GET'])
def articles_by_word_count():
    try:
        # Define the aggregation pipeline to sort articles by word count in descending order
        pipeline = [
            {"$sort": {"word_count": -1}},  # Sort by word_count in descending order
            {"$project": {  # Optionally, include only specific fields
                "_id": 0,
                "post_id": 1,
                "word_count": 1
            }}
        ]

        result = list(collection.aggregate(pipeline))
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/articles_by_language', methods=['GET'])
def articles_by_language():
    total_articles = collection.count_documents({})  # Total number of articles
    pipeline = [
        {"$group": {"_id": "$lang", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = list(collection.aggregate(pipeline))

    # Calculate percentage for each language
    #for language_data in result:
      #  language_data['percentage'] = (language_data['count'] / total_articles) * 100
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
        {
            "$group": {
                "_id": "$classes",
                "count": {"$sum": 1},
                "published_time": {"$first": "$published_time"}  # Get the published_time of the first occurrence
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]

    result = []
    for item in collection.aggregate(pipeline):
        published_time_obj = item.get('published_time')

        # Ensure published_time_obj is a datetime object
        if isinstance(published_time_obj, datetime):
            published_timestamp = int(published_time_obj.timestamp())
        else:
            # If it's not already a datetime, convert it from a string
            published_time_obj = datetime.strptime(
                published_time_obj, "%a, %d %b %Y %H:%M:%S GMT"
            )
            published_timestamp = int(published_time_obj.timestamp())

        result.append({
            "_id": item['_id'],
            "count": item['count'],
            "published_time": published_timestamp
        })

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
        # Project title and calculate word_count based on the full_text field
        {"$project": {
            "title": 1,
            "url": 1,
            "_id": 0,  # Exclude _id from the output
            "word_count": {
                "$size": {"$split": [{"$ifNull": ["$full_text", ""]}, " "]}
            }
        }},
        {"$sort": {"word_count": -1}},
        {"$limit": 10}
    ]

    result = list(collection.aggregate(pipeline))

    # Convert ObjectId to string
    for article in result:
        article['post_id'] = str(article.get('post_id', ''))

    return jsonify(result)


@app.route('/shortest_articles', methods=['GET'])
def shortest_articles():
    pipeline = [
        # Project title and calculate word_count based on the full_text field
        {"$project": {
            "title": 1,
            "url": 1,
            "_id": 0,  # Exclude _id from the output
            "word_count": {
                "$size": { "$split": [{ "$ifNull": ["$full_text", ""] }, " "] }
            }
        }},
        {"$sort": {"word_count": 1}},  # Sort in ascending order for shortest articles
        {"$limit": 10}
    ]

    result = list(collection.aggregate(pipeline))

    # Convert ObjectId to string if necessary
    for article in result:
        article['post_id'] = str(article.get('post_id', ''))

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


@app.route('/trend_calc/<type>', methods=['GET'])
def trend_entity_calc(type):
    try:
        # Calculate entity trends
        entity_trends = trendCalc.calculate_entity_trends(entity_type=type)

        # Convert DataFrame to JSON
        result = entity_trends.to_json(orient="records")

        # Return JSON response with UTF-8 encoding
        return Response(response=result, status=200, content_type="application/json; charset=utf-8")

    except Exception as e:
        return Response(response=jsonify({"error": str(e)}), status=500, content_type="application/json; charset=utf-8")


@app.route('/get_keyword/<keyword>', methods=['GET'])
def get_keyword(keyword):
    # keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"error": "Please provide a keyword"}), 400

    # Search for documents containing the specified keyword
    query = {"keywords": keyword}
    projection = {"_id": 0, "published_time": 1, "post_id": 1}
    documents = list(collection.find(query, projection))  # Exclude MongoDB _id field from results

    return jsonify(documents)

@app.route('/most_positive_articles', methods=['GET'])
def most_positive_articles():
    result = list(collection.find({}, {"title": 1, "sentiment": 1, "_id": 0})
                 .sort("sentiment", -1))
    return jsonify(result)

@app.route('/most_negative_articles', methods=['GET'])
def most_negative_articles():
    result = list(collection.find({}, {"title": 1, "sentiment": 1, "_id": 0})
                 .sort("sentiment", 1))
    return jsonify(result)


@app.route('/articles_by_entity/<entity>', methods=['GET'])
def articles_by_entity(entity):
    try:
        # Search for articles that mention the entity in any of the my_entities sections
        result = list(collection.find({
            "$or": [
                {"my_entities.persons.word": entity},
                {"my_entities.locations.word": entity},
                {"my_entities.organizations.word": entity}
            ]
        }, {
            "title": 1,
            "post_id": 1,
            "_id": 0
        }))

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dashboard_count_time', methods=['GET'])
def dashboard_count_time():
    pipeline = [
        {
            "$project": {
                "published_date": {
                    "$toDate": "$published_time"
                }
            }
        },
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$published_date"}},
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    # Convert CommandCursor to a list of dictionaries
    results = list(collection.aggregate(pipeline))

    # Convert the _id to a timestamp (milliseconds since the epoch)
    for result in results:
        date_str = result['_id']
        result['_id'] = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp()) * 1000

    return jsonify(results)



@app.route('/authors_count', methods=['GET'])
def authors_count():
        # MongoDB aggregation pipeline to count articles by author
        pipeline = [
            {"$group": {"_id": "$author", "count": {"$sum": 1}}},  # Group by author and count
            {"$sort": {"count": -1}}  # Sort by count in descending order
        ]

        # Execute the aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Transform the result to a readable format
        authors_data = [{"author": doc["_id"], "article_count": doc["count"]} for doc in result]

        return jsonify(authors_data)


if __name__ == '__main__':
    app.run(debug=True)
