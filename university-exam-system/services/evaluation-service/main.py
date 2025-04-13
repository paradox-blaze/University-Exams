from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from typing import Dict
import os
import uvicorn

# MongoDB setup
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
client = MongoClient(mongo_url)
db = client.university
exams_collection = db.exams
questions_collection = db.questions

app = FastAPI()

# --- Request Model ---
class EvaluationRequest(BaseModel):
    exam_id: str
    student_id: str
    answers: Dict[str, str]  # question_id: answer or selected option

# --- GET all exams ---
@app.get("/evaluation/exams")
def get_exams():
    exams = exams_collection.find()
    return [{"id": str(exam["_id"]), "name": exam["name"], "course_id": exam["course_id"]} for exam in exams]

# --- POST auto evaluation ---
@app.post("/evaluation/evaluate")
def evaluate_exam(data: EvaluationRequest):
    try:
        exam_obj_id = ObjectId(data.exam_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid exam_id format")

    exam = exams_collection.find_one({"_id": exam_obj_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # --- Check for duplicate submission ---
    existing = exam.get("results", [])
    for res in existing:
        if res.get("student_id") == data.student_id:
            raise HTTPException(status_code=409, detail="Student has already submitted this exam")

    # --- Fetch all questions for that exam ---
    questions = questions_collection.find({"exam_id": data.exam_id})

    obtained_score = 0
    total_marks = 0
    long_answers = []

    for q in questions:
        qid = str(q["_id"])
        marks = q.get("marks", 1)
        total_marks += marks
        q_type = q.get("question_type")
        student_answer = data.answers.get(qid)

        if q_type == "mcq":
            correct = q.get("correct_option")
            if student_answer and student_answer == correct:
                obtained_score += marks
        elif q_type == "long":
            # Store long answers for manual checking
            long_answers.append({
                "question_id": qid,
                "answer": student_answer or "",
                "marks_awarded": None
            })

    # --- Save the result ---
    evaluation_result = {
        "student_id": data.student_id,
        "score": obtained_score,
        "total_marks": total_marks,
        "submitted_at": datetime.utcnow(),
        "long_answers": long_answers
    }

    result = exams_collection.update_one(
        {"_id": exam_obj_id},
        {"$push": {"results": evaluation_result}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to save evaluation")

    return {
        "message": "Evaluation completed!",
        "student_id": data.student_id,
        "score": obtained_score,
        "total_marks": total_marks
    }

# --- GET exam results ---
@app.get("/evaluation/results/{exam_id}")
def get_results(exam_id: str):
    try:
        exam_obj_id = ObjectId(exam_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid exam_id format")

    exam = exams_collection.find_one({"_id": exam_obj_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    return {
        "exam_id": exam_id,
        "results": exam.get("results", [])
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)