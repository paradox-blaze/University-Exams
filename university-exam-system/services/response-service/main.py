from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from typing import Optional
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
subjects_collection = db.subjects
students_collection = db.students
teachers_collection = db.teachers
questions_collection = db.questions
classes_collection = db.classes
responses_collection = db.responses
results_collection = db.results

app = FastAPI()

class AnswerSubmit(BaseModel):
    longAnswerText: str
    marksObtained: Optional[int] = None
    type: str  # 'mcq' or 'long'

def str_to_objectid(id: str):
    try:
        return ObjectId(id)
    except Exception:
        return None

def is_exam_live(exam):
    return exam["status"] == "live" and exam["startTime"] <= datetime.now() <= exam["endTime"]

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
        "id": ObjectId(question_id),
        "studentId": student_id,
        "type": answer.type
    }

    if answer.type == "long":
        response_data["longAnswerText"] = answer.longAnswerText
        response_data["marksAwarded"] = None  # To be graded later by teacher
    elif answer.type == "mcq":
        try:
            selected_index = int(answer.marksObtained)  # misused field for index
            response_data["selectedAnswerIndex"] = selected_index
            # Auto-grade
            if selected_index == question.get("correctAnswerIndex"):
                response_data["marksAwarded"] = question.get("marks", 0)
            else:
                response_data["marksAwarded"] = 0
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid selectedAnswerIndex for MCQ")

    responses_collection.insert_one(response_data)
    return {"message": "Response submitted successfully!"}

@app.get("/responses")
def get_responses(student_id: str, exam_id: str):
    query = {"studentId": student_id, "examId": exam_id}
    responses = list(responses_collection.find(query))

    result = []
    for r in responses:
        question = questions_collection.find_one({"_id": r["id"]})
        if not question:
            continue
        if "selectedAnswerIndex" in r:
            selected = r["selectedAnswerIndex"]
            correct = question.get("correctAnswerIndex", -1)
            options = question.get("options", [])
            result.append({
                "type": "MCQ",
                "id": str(r["id"]),
                "selectedOption": options[selected] if 0 <= selected < len(options) else "Invalid",
                "correctOption": options[correct] if 0 <= correct < len(options) else "Not Provided",
                "marksAwarded": r.get("marksAwarded", 0),
                "totalMarks": question.get("marks", 0),
                "questionText": question.get("questionText")
            })
        elif "longAnswerText" in r:
            result.append({
                "type": "Long Answer",
                "id": str(r["id"]),
                "studentAnswer": r.get("longAnswerText", ""),
                "marksAwarded": r.get("marksAwarded", 0),
                "totalMarks": question.get("marks", 0),
                "gradedBy": r.get("gradedBy", "Not graded"),
                "gradedAt": r.get("gradedAt"),
                "questionText": question.get("questionText")
            })
    return result

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
        "id": question_obj,
        "marksAwarded": None
    })

    return {
        "questionText": question["questionText"],
        "expectedKeywords": question.get("expectedKeywords", []),
        "responses": [
            {
                "responseId": str(resp["_id"]),
                "studentId": str(resp["studentId"]),
                "longAnswerText": resp["longAnswerText"]
            } for resp in responses
        ]
    }

@app.get("/exams/question-responses")
def get_responses_for_question(
    exam_id: str = Query(...),
    question_id: str = Query(...)
):
    question = questions_collection.find_one({"_id": str_to_objectid(question_id), "examId": exam_id})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if question["type"] != "long":
        raise HTTPException(status_code=400, detail="Only long-format questions are evaluated manually.")

    responses = responses_collection.find({
        "examId": exam_id,
        "id": str_to_objectid(question_id)
    })

    return {
        "questionText": question["questionText"],
        "expectedKeywords": question.get("expectedKeywords", []),
        "responses": [
            {
                "responseId": str(resp["_id"]),
                "studentId": str(resp["studentId"]),
                "longAnswerText": resp.get("longAnswerText", ""),
                "marksAwarded": resp.get("marksAwarded"),
                "gradedBy": resp.get("gradedBy"),
                "gradedAt": resp.get("gradedAt")
            } for resp in responses
        ]
    }

@app.get("/exams/question-responses/all")
def get_all_mcq_responses(exam_id: str = Query(...), question_id: str = Query(...)):
    question = questions_collection.find_one({"_id": ObjectId(question_id)})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if question.get("type", "").lower() != "mcq":
        raise HTTPException(status_code=400, detail="Question is not of type MCQ")

    responses = list(responses_collection.find({
        "examId": exam_id,
        "id": ObjectId(question_id)
    }))

    formatted = []
    for r in responses:
        formatted.append({
            "responseId": str(r["_id"]),
            "studentId": r["studentId"],
            "selectedAnswerIndex": r.get("selectedAnswerIndex"),
            "marksAwarded": r.get("marksAwarded", 0)
        })

    return {"responses": formatted}

@app.post("/responses/grade")
def grade_response(response_id: str = Query(...), marks: int = Body(...), gradedBy: str = Body(...)):
    result = db.responses.update_one(
        {"_id": ObjectId(response_id)},
        {"$set": {
            "marksAwarded": marks,  # ✅ Unified field name
            "gradedBy": gradedBy,
            "gradedAt": datetime.utcnow()
        }}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Response not found or already graded")

    return {"message": "Response graded successfully!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)