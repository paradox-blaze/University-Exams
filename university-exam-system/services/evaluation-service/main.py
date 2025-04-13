from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import os

# MongoDB connection URL
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
client = MongoClient(mongo_url)
db = client.university  # Connect to the `university` database
exams_collection = db.exams

# FastAPI instance
app = FastAPI()

# API Routes
@app.get("/evaluation/exams")
def get_exams():
    exams = exams_collection.find()
    return [{"id": str(exam["_id"]), "name": exam["name"], "course_id": exam["course_id"]} for exam in exams]

@app.post("/evaluation/evaluate")
def evaluate_exam(exam_id: str, student_id: str, score: int):
    exam = exams_collection.find_one({"_id": exam_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Update exam evaluation
    result = exams_collection.update_one(
        {"_id": exam_id},
        {"$push": {"results": {"student_id": student_id, "score": score}}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to evaluate")
    
    return {"message": "Evaluation submitted successfully!"}

@app.get("/evaluation/results/{exam_id}")
def get_results(exam_id: str):
    exam = exams_collection.find_one({"_id": exam_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return {"exam_id": exam_id, "results": exam.get("results", [])}
