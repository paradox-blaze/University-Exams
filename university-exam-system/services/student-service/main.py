from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
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
results_collection = db.results
subjects_collection = db.subjects
classes_collection = db.classes

app = FastAPI()

# Helpers
def get_student_courses(student_id: str):
    student = students_collection.find_one({"_id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    myclass = student['classId']
    my_class_object = classes_collection.find_one({"_id": myclass})
    print(my_class_object['subjectIds'])
    return my_class_object['subjectIds']

def is_exam_live(exam):
    return exam["status"] == "live" and exam["startTime"] <= datetime.now() <= exam["endTime"]

# Models
class AnswerSubmit(BaseModel):
    answerText: str
    marksObtained: Optional[int] = None
    questionType: str  # 'mcq' or 'long'

# Routes

@app.get("/students")
def get_students():
    students = students_collection.find()
    return [
        {
            "id": s["_id"],
            "name": s["name"],
            "email": s["email"],
            "rollNumber": s["rollNumber"],
            "class": s["class"]
        }
        for s in students
    ]

@app.get("/students/by-class")
def get_students_by_class(class_id: str):
    students = list(students_collection.find({"classId": class_id}))
    if not students:
        raise HTTPException(status_code=404, detail="No students found for this class")
    return [
        {
            "id": s["_id"],
            "name": s["name"],
            "email": s["email"],
            "rollNumber": s["rollNumber"],
            "class": s["classId"]
        }
        for s in students
    ]

@app.get("/students/{student_id}")
def get_student(student_id: str):
    student = students_collection.find_one({"_id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {
        "id": student["_id"],
        "name": student["name"],
        "email": student["email"],
        "rollNumber": student["rollNumber"],
        "class": student["classId"]
    }

@app.get("/exams")
def get_exams_for_student(student_id: str):
    student_courses = get_student_courses(student_id)
    exams = exams_collection.find({
        "subjectId": {"$in": student_courses},
        "status": "live",
        "startTime": {"$lte": datetime.now()},
        "endTime": {"$gte": datetime.now()}
    })
    return [
        {
            "exam_id": e["_id"],
            "title": e["title"],
            "subjectId": e["subjectId"],
            "startTime": e["startTime"],
            "endTime": e["endTime"],
            "durationMinutes": e["durationMinutes"]
        }
        for e in exams
    ]

@app.post("/exams/{exam_id}/questions/{question_id}/response")
def submit_answer(exam_id: str, question_id: str, student_id: str, answer: AnswerSubmit):
    exam = exams_collection.find_one({"_id": exam_id})
    if not exam or not is_exam_live(exam):
        raise HTTPException(status_code=404, detail="Exam not found or not live")

    question = questions_collection.find_one({"_id": ObjectId(question_id), "examId": exam_id})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    response_data = {
        "examId": exam_id,
        "questionId": ObjectId(question_id),
        "studentId": student_id,
        "answerText": answer.answerText,
        "marksAwarded": answer.marksObtained,
        "questionType": answer.questionType
    }
    responses_collection.insert_one(response_data)
    return {"message": "Response submitted successfully!"}

@app.get("/responses")
def get_responses(student_id: str, exam_id: str):
    query = {"studentId": student_id, "examId": exam_id}
    responses = list(responses_collection.find(query))

    result = []
    for r in responses:
        question = questions_collection.find_one({"_id": r["questionId"]})
        if not question:
            continue
        if "selectedAnswerIndex" in r:
            selected = r["selectedAnswerIndex"]
            correct = question.get("correctAnswerIndex", -1)
            options = question.get("options", [])
            qtext = question.get("questionText")
            result.append({
                "type": "MCQ",
                "questionId": str(r["questionId"]),
                "selectedOption": options[selected] if 0 <= selected < len(options) else "Invalid",
                "correctOption": options[correct] if 0 <= correct < len(options) else "Not Provided",
                "marksAwarded": r.get("marksAwarded", 0),
                "totalMarks": question.get("marks", 0),
                "questionText": question.get("questionText")
            })
        elif "longAnswerText" in r:
            result.append({
                "type": "Long Answer",
                "questionId": str(r["questionId"]),
                "studentAnswer": r.get("longAnswerText", ""),
                "marksAwarded": r.get("marksAwarded", 0),
                "totalMarks": question.get("marks", 0),
                "gradedBy": r.get("gradedBy", "Not graded"),
                "gradedAt": r.get("gradedAt"),
                "questionText": question.get("questionText")
            })
    return result

@app.get("/results")
def get_results_for_student(student_id: str, subject_id: Optional[str] = None):
    query = {"studentId": student_id}
    if subject_id:
        exam_ids = [e["_id"] for e in exams_collection.find({"subjectId": subject_id}, {"_id": 1})]
        query["examId"] = {"$in": exam_ids}
    results = results_collection.find(query)
    return [
        {
            "examId": r["examId"],
            "marksObtained": r["marksObtained"],
            "totalMarks": r["totalMarks"],
            "percentage": r["percentage"],
            "grade": r["grade"],
            "computedAt": r["computedAt"]
        }
        for r in results
    ]

@app.get("/all-results")
def get_all_results(subject_id: Optional[str] = None):
    final = []
    for s in students_collection.find():
        student_id = s["_id"]
        results = []
        for r in responses_collection.find({"studentId": student_id}):
            q = questions_collection.find_one({"_id": r["questionId"]})
            e = exams_collection.find_one({"_id": r["examId"]})
            if subject_id and e["subjectId"] != subject_id:
                continue
            results.append({
                "examTitle": e["title"],
                "questionText": q["questionText"],
                "answerText": r.get("answerText", r.get("longAnswerText", "")),
                "marksObtained": r.get("marksAwarded", 0),
                "questionType": r["questionType"]
            })
        if results:
            final.append({
                "studentId": student_id,
                "studentName": s["name"],
                "results": results
            })
    return final

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
