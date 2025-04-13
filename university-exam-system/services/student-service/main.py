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
responses_collection = db.responses
students_collection = db.students

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

def get_student_courses(student_id: str):
    student = students_collection.find_one({"_id": str_to_objectid(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student["course_ids"]

def is_exam_live(exam):
    return exam["status"] == "live" and exam["startTime"] <= datetime.now() <= exam["endTime"]

# Models
class AnswerSubmit(BaseModel):
    answerText: str
    marksObtained: Optional[int] = None  # For MCQs, this might be calculated automatically
    questionType: str  # 'mcq' or 'long'

class ExamOut(BaseModel):
    exam_id: str
    title: str
    subjectId: str
    startTime: datetime
    endTime: datetime
    durationMinutes: int

class QuestionOut(BaseModel):
    questionId: str
    questionText: str
    questionType: str
    marks: int
    options: Optional[List[str]] = None
    correctAnswerIndex: Optional[int] = None
    expectedKeywords: Optional[List[str]] = None

class ResultOut(BaseModel):
    examTitle: str
    questionText: str
    answerText: str
    marksObtained: Optional[int] = None
    questionType: str

# Routes

@app.get("/exams")
def get_exams_for_student(student_id: str):
    # Get the student's courses
    student_courses = get_student_courses(student_id)
    
    # Find exams related to those courses, and filter for live exams
    exams = exams_collection.find({
        "subjectId": {"$in": student_courses},
        "status": "live",
        "startTime": {"$lte": datetime.now()},
        "endTime": {"$gte": datetime.now()}
    })
    
    return [
        {
            "exam_id": str(exam["_id"]),
            "title": exam["title"],
            "subjectId": str(exam["subjectId"]),
            "startTime": exam["startTime"],
            "endTime": exam["endTime"],
            "durationMinutes": exam["durationMinutes"]
        }
        for exam in exams
    ]

@app.post("/exams/{exam_id}/questions/{question_id}/response")
def submit_answer(exam_id: str, question_id: str, student_id: str, answer: AnswerSubmit):
    exam = exams_collection.find_one({"_id": str_to_objectid(exam_id)})
    if not exam or not is_exam_live(exam):
        raise HTTPException(status_code=404, detail="Exam not found or not live")

    question = questions_collection.find_one({"_id": str_to_objectid(question_id), "examId": str_to_objectid(exam_id)})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    response_data = {
        "examId": str_to_objectid(exam_id),
        "questionId": str_to_objectid(question_id),
        "studentId": str_to_objectid(student_id),
        "answerText": answer.answerText,
        "marksObtained": answer.marksObtained,
        "questionType": answer.questionType
    }
    
    # Insert the response into the database
    responses_collection.insert_one(response_data)
    
    return {"message": "Response submitted successfully!"}

@app.get("/results")
def get_results_for_student(student_id: str):
    responses = responses_collection.find({"studentId": str_to_objectid(student_id)})
    
    # Format responses with marks
    results = []
    for response in responses:
        question = questions_collection.find_one({"_id": response["questionId"]})
        exam = exams_collection.find_one({"_id": response["examId"]})
        results.append({
            "examTitle": exam["title"],
            "questionText": question["questionText"],
            "answerText": response["answerText"],
            "marksObtained": response["marksObtained"],
            "questionType": response["questionType"]
        })
    
    return results


# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
