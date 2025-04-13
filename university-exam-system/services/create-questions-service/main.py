from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from bson import ObjectId
import os

# MongoDB connection URL
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
client = MongoClient(mongo_url)
db = client.university
questions_collection = db.questions

# FastAPI instance
app = FastAPI()

# Pydantic Models
class Question(BaseModel):
    question_text: str
    exam_id: str
    options: list
    correct_option: str

class UpdateQuestion(BaseModel):
    question_text: str | None = None
    exam_id: str | None = None
    options: list | None = None
    correct_option: str | None = None

# Utility to convert Mongo _id
def question_to_dict(question):
    return {
        "id": str(question["_id"]),
        "question_text": question["question_text"],
        "exam_id": question["exam_id"],
        "options": question["options"],
        "correct_option": question["correct_option"]
    }

# --- CREATE ---
@app.post("/questions")
def create_question(question: Question):
    question_data = question.dict()
    result = questions_collection.insert_one(question_data)
    return {"id": str(result.inserted_id), "message": "Question created successfully"}

# --- READ ALL for an exam ---
@app.get("/questions/{exam_id}")
def get_questions(exam_id: str):
    questions = questions_collection.find({"exam_id": exam_id})
    return [question_to_dict(q) for q in questions]

# --- READ SINGLE question ---
@app.get("/question/{question_id}")
def get_question(question_id: str):
    question = questions_collection.find_one({"_id": ObjectId(question_id)})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question_to_dict(question)

# --- UPDATE ---
@app.put("/question/{question_id}")
def update_question(question_id: str, updated: UpdateQuestion):
    update_data = {k: v for k, v in updated.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update fields provided")
    result = questions_collection.update_one({"_id": ObjectId(question_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question updated successfully"}

# --- DELETE ---
@app.delete("/question/{question_id}")
def delete_question(question_id: str):
    result = questions_collection.delete_one({"_id": ObjectId(question_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question deleted successfully"}
