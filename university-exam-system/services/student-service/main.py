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

@app.get("/students")
def get_students():
    students = students_collection.find()
    return [
        {
            "id": str(s["_id"]),
            "name": s["name"],
            "email": s["email"],
            "rollNumber": s["rollNumber"],
            "class": s["class"]
        }
        for s in students
    ]

@app.get("/students/by-class")
def get_students_by_class(class_id: str):
    students = students_collection.find({"classId": class_id})
    
    if not students:
        raise HTTPException(status_code=404, detail="No students found for this class")
    
    return [
        {
            "id": str(student["_id"]),
            "name": student["name"],
            "email": student["email"],
            "rollNumber": student["rollNumber"],
            "class": student["classId"]
        }
        for student in students
    ]

@app.get("/students/{student_id}")
def get_student(student_id: str):
    student = students_collection.find_one({"_id": str_to_objectid(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return {
        "id": str(student["_id"]),
        "name": student["name"],
        "email": student["email"],
        "rollNumber": student["rollNumber"],
        "class": student["class"]
    }

from fastapi import APIRouter
from typing import Optional
from bson.objectid import ObjectId

@app.get("/responses")
def get_responses(student_id: str, exam_id: str):
    # Fetch all responses for this student and exam
    query = {"studentId": student_id, "examId": exam_id}
    responses = list(responses_collection.find(query))

    formatted_responses = []

    for r in responses:
        question = questions_collection.find_one({"_id": ObjectId(r["questionId"])})
        if not question:
            continue

        # Detect response type: MCQ or Long Answer
        if "selectedAnswerIndex" in r:
            # MCQ question
            options = question.get("options", [])
            selected_index = r["selectedAnswerIndex"]
            correct_index = question.get("correctAnswerIndex", -1)

            formatted_responses.append({
                "type": "MCQ",
                "questionId": str(r["questionId"]),  # Return questionId instead of question text
                "selectedOption": options[selected_index] if 0 <= selected_index < len(options) else "Invalid Option",
                "correctOption": options[correct_index] if 0 <= correct_index < len(options) else "Not Provided",
                "marksAwarded": r.get("marksAwarded", 0),
                "totalMarks": question.get("marks", 0),
            })

        elif "longAnswerText" in r:
            # Long answer question
            formatted_responses.append({
                "type": "Long Answer",
                "questionId": str(r["questionId"]),  # Return questionId instead of question text
                "studentAnswer": r.get("longAnswerText", ""),
                "marksAwarded": r.get("marksAwarded", 0),
                "totalMarks": question.get("marks", 0),
                "gradedBy": r.get("gradedBy", "Not graded"),
                "gradedAt": r.get("gradedAt", None),
            })

    return formatted_responses


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
def get_results_for_student(student_id: str, subject_id: Optional[str] = None):
    # Build the query to fetch results for the specific student
    query = {"studentId": student_id}

    # If a subject_id is provided, filter results by subject
    if subject_id:
        # Fetch exam IDs for the given subject_id
        exam_ids = exams_collection.find({"subjectId": subject_id}, {"_id": 1})
        exam_ids = [str(exam["_id"]) for exam in exam_ids]  # Convert ObjectId to string

        query["examId"] = {"$in": exam_ids}  # Add the subject-specific exam filter to the query

    # Fetch the results from the 'results' collection
    results = list(db.results.find(query))  # Convert the cursor to a list

    # Format the results to return in a readable format
    formatted_results = []
    for result in results:
        formatted_results.append({
            "examId": result["examId"],  # Title of the exam
            "marksObtained": result["marksObtained"],  # Marks obtained by the student
            "totalMarks": result["totalMarks"],  # Total marks for the exam
            "percentage": result["percentage"],  # Percentage calculated from marksObtained and totalMarks
            "grade": result["grade"],  # Grade (A, B, C, etc.)
            "computedAt": result["computedAt"],  # Timestamp when result was computed
        })

    return formatted_results


# New Route: Get all student results with subject-wise filtering (for admins or teachers)
@app.get("/all-results")
def get_all_results(subject_id: Optional[str] = None):
    all_results = []
    students = students_collection.find()

    for student in students:
        student_results = []
        responses = responses_collection.find({"studentId": student["_id"]})
        
        for response in responses:
            question = questions_collection.find_one({"_id": response["questionId"]})
            exam = exams_collection.find_one({"_id": response["examId"]})

            # If a subject_id is provided, filter results by subject
            if subject_id and exam["subjectId"] != subject_id:
                continue

            student_results.append({
                "examTitle": exam["title"],
                "questionText": question["questionText"],
                "answerText": response["answerText"],
                "marksObtained": response["marksObtained"],
                "questionType": response["questionType"]
            })
        
        if student_results:
            all_results.append({
                "studentId": str(student["_id"]),
                "studentName": student["name"],
                "results": student_results
            })
    
    return all_results

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
