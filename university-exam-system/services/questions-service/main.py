from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
from pymongo import MongoClient
from bson import ObjectId
import os
import uvicorn

# MongoDB Setup
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
client = MongoClient(mongo_url)
db = client.university
exams_collection = db.exams
subjects_collection = db.subjects
students_collection = db.students
teachers_collection = db.teachers
questions_collection = db.questions
classes_collection = db.classes
responses_collection = db.responses
results_collection = db.results

app = FastAPI()

def str_to_objectid(id: str):
    try:
        return ObjectId(id)
    except Exception:
        return None
    
class QuestionCreate(BaseModel):
    questionText: str
    type: Literal["mcq", "long"]
    marks: int
    options: Optional[List[str]] = None
    correctAnswerIndex: Optional[int] = None
    expectedKeywords: Optional[List[str]] = None


@app.post("/exams/{exam_id}/questions")
def add_question(exam_id: str, question: QuestionCreate):
    exam_obj_id = str_to_objectid(exam_id)
    if not exams_collection.find_one({"_id": exam_obj_id}):
        raise HTTPException(status_code=404, detail="Exam not found")

    question_data = question.dict()
    question_data["examId"] = exam_obj_id

    # Validation for MCQ
    if question_data["type"] == "mcq":
        if not question_data.get("options") or question_data.get("correctAnswerIndex") is None:
            raise HTTPException(status_code=400, detail="MCQ must have options and correctAnswerIndex")
    
    # Validation for long
    if question_data["type"] == "long":
        if not question_data.get("expectedKeywords"):
            raise HTTPException(status_code=400, detail="Long questions must have expectedKeywords")

    questions_collection.insert_one(question_data)
    return {"message": "Question added successfully!"}

@app.post("/questions/create")
def create_question(data: dict):
    exam_id = data.get("examId")
    question_text = data.get("questionText")
    question_type = data.get("type", "").strip().lower()  # Normalize type
    marks = data.get("marks", 5)

    if not exam_id or not question_text or not question_type:
        raise HTTPException(status_code=400, detail="Missing required fields.")

    question = {
        "examId": exam_id,
        "questionText": question_text,
        "type": question_type,
        "marks": marks
    }

    if question_type == "mcq":
        options = data.get("options", [])
        correct_answer_index = data.get("correctAnswerIndex", -1)
        if not options or correct_answer_index < 0:
            raise HTTPException(status_code=400, detail="MCQ must include options and a correctAnswerIndex")
        question["options"] = options
        question["correctAnswerIndex"] = correct_answer_index

    elif question_type == "long":
        expected_keywords = data.get("expectedKeywords", [])
        question["expectedKeywords"] = expected_keywords

    else:
        raise HTTPException(status_code=400, detail="Unsupported question type.")

    questions_collection.insert_one(question)
    return {"message": "Question added successfully!"}

@app.delete("/questions/{question_id}")
def delete_question(question_id: str):
    result = questions_collection.delete_one({"_id": str_to_objectid(question_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question deleted successfully"}
    
@app.get("/question/get")
def get_question_by_id(id: str):
    try:
        question = db.questions.find_one({"_id": ObjectId(id)})
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        response = {
            "id": str(question["_id"]),
            "questionText": question.get("questionText", "No text provided"),
            "type": question.get("type", "unknown"),
        }

        # Optional: If MCQ, include options
        if question.get("type") == "mcq":
            response["options"] = question.get("options", [])

        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid question ID: {e}")
    
@app.get("/exams/{exam_id}/questions")
def get_questions(exam_id: str):
    exam = exams_collection.find_one({"_id": exam_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    questions = list(questions_collection.find({"examId": exam_id}))
    return [
        {
            "id": str(q["_id"]),
            "questionText": q["questionText"],
            "type": q["type"],
            "marks": q["marks"],
            "options": q.get("options", []),
            "correctAnswerIndex": q.get("correctAnswerIndex"),
            "expectedKeywords": q.get("expectedKeywords", [])
        }
        for q in questions
    ]


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)