from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime
import os
import uvicorn

# MongoDB Setup
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
client = MongoClient(mongo_url)
db = client.university
exams_collection = db.exams
questions_collection = db.questions
teachers_collection = db.teachers

app = FastAPI()

# Helpers
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

def str_to_objectid(id: str):
    try:
        return ObjectId(id)
    except Exception:
        return None

# Models
class ExamCreate(BaseModel):
    subjectId: str
    title: str
    startTime: datetime
    endTime: datetime
    durationMinutes: int
    createdBy: str
    isPublished: bool = False

class ExamOut(BaseModel):
    id: str
    title: str
    subjectId: str
    createdBy: str
    startTime: datetime
    endTime: datetime
    durationMinutes: int
    status: str
    isPublished: bool

class QuestionCreate(BaseModel):
    questionText: str
    type: Literal["mcq", "long"]
    marks: int
    options: Optional[List[str]] = None
    correctAnswerIndex: Optional[int] = None
    expectedKeywords: Optional[List[str]] = None

# Routes

@app.post("/exams")
def create_exam(exam: ExamCreate):
    exam_data = exam.dict()
    exam_data["subjectId"] = str_to_objectid(exam.subjectId)
    exam_data["createdBy"] = str_to_objectid(exam.createdBy)
    exam_data["status"] = "scheduled"
    inserted = exams_collection.insert_one(exam_data)
    return {"message": "Exam created", "exam_id": str(inserted.inserted_id)}

@app.get("/exams")
def get_exams_by_teacher(teacher_id: str):
    exams = exams_collection.find({"createdBy": str_to_objectid(teacher_id)})
    return [
        {
            "id": str(exam["_id"]),
            "title": exam["title"],
            "subjectId": str(exam["subjectId"]),
            "createdBy": str(exam["createdBy"]),
            "startTime": exam["startTime"],
            "endTime": exam["endTime"],
            "durationMinutes": exam["durationMinutes"],
            "status": exam["status"],
            "isPublished": exam["isPublished"]
        }
        for exam in exams
    ]

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

@app.get("/exams/{exam_id}/questions/{question_id}/responses")
def get_responses_for_evaluation(exam_id: str, question_id: str):
    exam_obj = str_to_objectid(exam_id)
    question_obj = str_to_objectid(question_id)

    question = questions_collection.find_one({"_id": question_obj, "examId": exam_obj})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if question["type"] != "long":
        raise HTTPException(status_code=400, detail="Only long-format questions are evaluated manually.")

    responses = db.responses.find({
        "examId": exam_obj,
        "questionId": question_obj,
        "marksObtained": None
    })

    return {
        "questionText": question["questionText"],
        "expectedKeywords": question.get("expectedKeywords", []),
        "responses": [
            {
                "responseId": str(resp["_id"]),
                "studentId": str(resp["studentId"]),
                "answerText": resp["answerText"]
            } for resp in responses
        ]
    }

from fastapi import Body

@app.post("/responses/{response_id}/grade")
def grade_response(response_id: str, marks: int = Body(...), gradedBy: str = Body(...)):
    response_obj = str_to_objectid(response_id)
    teacher_obj = str_to_objectid(gradedBy)

    result = db.responses.update_one(
        {"_id": response_obj},
        {"$set": {"marksObtained": marks, "gradedBy": teacher_obj}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Response not found or already graded")

    return {"message": "Response graded successfully!"}


@app.get("/exams/{exam_id}/questions")
def get_questions(exam_id: str):
    exam_obj_id = str_to_objectid(exam_id)
    if not exams_collection.find_one({"_id": exam_obj_id}):
        raise HTTPException(status_code=404, detail="Exam not found")

    questions = questions_collection.find({"examId": exam_obj_id})
    return [
        {
            "id": str(q["_id"]),
            "questionText": q["questionText"],
            "type": q["type"],
            "marks": q["marks"],
            "options": q.get("options"),
            "correctAnswerIndex": q.get("correctAnswerIndex"),
            "expectedKeywords": q.get("expectedKeywords")
        }
        for q in questions
    ]

# Run
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
