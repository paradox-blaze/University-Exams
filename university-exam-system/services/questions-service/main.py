from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
import os

# MongoDB connection URL
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
client = MongoClient(mongo_url)
db = client.university  # Connect to the `university` database
questions_collection = db.questions

# FastAPI instance
app = FastAPI()

# Models for request bodies
class Question(BaseModel):
    question_text: str
    exam_id: str
    options: list
    correct_option: str

# API Routes
@app.post("/questions")
def create_question(question: Question):
    question_data = question.dict()
    questions_collection.insert_one(question_data)
    return {"message": "Question created successfully!"}

@app.get("/questions/{exam_id}")
def get_questions(exam_id: str):
    questions = questions_collection.find({"exam_id": exam_id})
    return [{"id": str(q["_id"]), "question_text": q["question_text"], "options": q["options"]} for q in questions]
