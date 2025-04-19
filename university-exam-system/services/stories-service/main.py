from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://mongodb:27017")
db = client["university"]
stories = db["stories"]

@app.route("/stories", methods=["GET"])
def get_stories():
    all_stories = list(stories.find({}, {"_id": 0}))
    return jsonify(all_stories)

@app.route("/stories", methods=["POST"])
def add_story():
    data = request.json
    stories.insert_one(data)
    return jsonify({"msg": "Story added!"})

@app.route("/stories", methods=["DELETE"])
def delete_story():
    title = request.args.get("title")
    stories.delete_one({"title": title})
    return jsonify({"msg": "Story deleted!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
