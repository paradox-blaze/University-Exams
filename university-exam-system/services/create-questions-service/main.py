from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from bson import ObjectId
import os
from typing import Optional, List

# MongoDB connection
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
client = MongoClient(mongo_url)
db = client.university
questions_collection = db.questions

app = FastAPI()

# Base Question Schema
class BaseQuestion(BaseModel):
    question_text: str
    exam_id: str
    question_type: str  # "mcq" or "long"
    marks: int
    options: Optional[List[str]] = None
    correct_option: Optional[str] = None

# Update Schema
class UpdateQuestion(BaseModel):
    question_text: Optional[str] = None
    exam_id: Optional[str] = None
    question_type: Optional[str] = None
    marks: Optional[int] = None
    options: Optional[List[str]] = None
    correct_option: Optional[str] = None

# Utility to convert Mongo object
def question_to_dict(q):
    return {
        "id": str(q["_id"]),
        "question_text": q["question_text"],
        "exam_id": q["exam_id"],
        "question_type": q["question_type"],
        "marks": q["marks"],
        "options": q.get("options"),
        "correct_option": q.get("correct_option")
    }

# --- CREATE ---
@app.post("/questions")
def create_question(question: BaseQuestion):
    q = question.dict()
    
    if q["question_type"] == "mcq":
        if not q.get("options") or not q.get("correct_option"):
            raise HTTPException(status_code=400, detail="MCQ must include options and correct_option.")
    elif q["question_type"] == "long":
        q["options"] = None
        q["correct_option"] = None
    else:
        raise HTTPException(status_code=400, detail="question_type must be either 'mcq' or 'long'.")

    result = questions_collection.insert_one(q)
    return {"id": str(result.inserted_id), "message": "Question created successfully"}

# --- READ ALL (by exam ID) ---
@app.get("/questions/{exam_id}")
def get_questions(exam_id: str):
    questions = questions_collection.find({"exam_id": exam_id})
    return [question_to_dict(q) for q in questions]

# --- READ SINGLE ---
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
        raise HTTPException(status_code=400, detail="No fields provided for update.")
    
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
