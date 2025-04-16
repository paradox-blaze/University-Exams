from fastapi import FastAPI, HTTPException,Request
from pydantic import BaseModel
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
classes_collection = db["classes"]
responses_collection = db.responses


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
    
class Class(BaseModel):
    id: str
    name: str
    subject_ids: List[str]

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


@app.get("/get_name")
def get_teacher_name(id: str):
    teacher = teachers_collection.find_one({"_id": id})
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {"teacher_name": teacher["name"]}

from fastapi import Path

@app.delete("/exams/{exam_id}")
def delete_exam(exam_id: str = Path(..., description="ID of the exam to delete")):
    # Delete exam
    result_exam = exams_collection.delete_one({"_id": exam_id})

    # Delete related questions
    result_questions = questions_collection.delete_many({"examId": exam_id})

    if result_exam.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Exam not found")

    return {
        "message": "Exam and associated questions deleted.",
        "questionsDeleted": result_questions.deleted_count
    }

@app.put("/exams/{exam_id}/publish")
async def publish_exam(exam_id: str, request: Request):
    # Try to read JSON body (if provided)
    try:
        body = await request.json()
        is_published = body.get("isPublished", True)
    except Exception:
        # No body sent, default to publish
        is_published = True

    new_status = "scheduled" if is_published else "draft"

    result = exams_collection.update_one(
        {"_id": exam_id},
        {"$set": {"isPublished": is_published, "status": new_status}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Exam not found")

    return {"message": f"Exam {'published' if is_published else 'unpublished'} successfully"}

@app.post("/exams/create")
def create_exam(data: dict):
    # Extract exam details
    title = data.get("title")
    subject_id = data.get("subjectId")
    start_time = data.get("startTime")
    end_time = data.get("endTime")
    duration_minutes = data.get("durationMinutes")
    created_by = data.get("createdBy")
    is_published = data.get("isPublished", False)
    status = data.get("status", "draft")

    # Construct a readable, unique _id
    exam_id = f"{subject_id}-{title.lower().replace(' ', '-')}"

    # Check if this ID already exists
    if exams_collection.find_one({"_id": exam_id}):
        raise HTTPException(status_code=400, detail="An exam with this ID already exists.")

    # Create the exam document with custom _id
    exam = {
        "_id": exam_id,
        "title": title,
        "subjectId": subject_id,
        "startTime": start_time,
        "endTime": end_time,
        "durationMinutes": duration_minutes,
        "createdBy": created_by,
        "isPublished": is_published,
        "status": status,
        "date": datetime.utcnow()
    }

    exams_collection.insert_one(exam)

    return {"message": "Exam created successfully!", "examId": exam_id}


from fastapi import HTTPException

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


from fastapi import HTTPException, Request

@app.put("/exams/update-status")
def update_exam_status(request: Request):
    data = request.json()  # Get the JSON body (no need for await)
    exam_id = data.get("examId")
    status = data.get("status")
    
    # Update exam status in the database (synchronous)
    exam = db.get_exam_by_id(exam_id)  # Assuming this is a synchronous DB call
    if exam:
        exam.status = status
        db.save_exam(exam)  # Assuming this is a synchronous DB save operation
        return {"message": "Exam status updated successfully!"}
    else:
        raise HTTPException(status_code=404, detail="Exam not found")

@app.get("/exams")
def get_exams_by_subject(subject_id: str):
    exams = exams_collection.find({"subjectId": subject_id})
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
        "marksAwarded": None
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


@app.delete("/questions/{question_id}")
def delete_question(question_id: str):
    result = questions_collection.delete_one({"_id": str_to_objectid(question_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question deleted successfully"}

@app.get("/exams/{exam_id}/questions")
def get_questions_for_exam(exam_id: str):
    try:
        # Match examId exactly as stored in MongoDB (likely a string, not ObjectId)
        questions = list(questions_collection.find({"examId": exam_id}))

        if not questions:
            return []  # Return empty list if no questions found

        # Format the questions for output
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch questions: {str(e)}")

@app.get("/question/get")
def get_question_by_id(id: str):
    try:
        question = db.questions.find_one({"_id": ObjectId(id)})
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        response = {
            "questionId": str(question["_id"]),
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

@app.get("/subjects")
def get_subjects_by_teacher(teacher_id: str):
    try:
        # Query MongoDB to find subjects by teacher_id in the teacherIds array
        subjects_cursor = db.subjects.find({"teacherIds": teacher_id})
        
        # Use count_documents() instead of the deprecated count()
        subject_count = db.subjects.count_documents({"teacherIds": teacher_id})
        
        if subject_count == 0:
            raise HTTPException(status_code=404, detail="No subjects found for this teacher")
        
        # Return a list of subjects for the given teacher
        subjects = [
            {
                "id": str(subject["_id"]),
                "name": subject["name"],
                "code": subject["code"],
                "teacherIds": subject["teacherIds"]
            }
            for subject in subjects_cursor
        ]
        
        return subjects
    
    except Exception as e:
        # Return a 500 Internal Server Error
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/subject-classes")
def get_classes_by_subject(subject_id: str):
    # Fetch the classes that are associated with the given subject
    classes = classes_collection.find({"subjectIds": subject_id})
    
    if not classes:
        raise HTTPException(status_code=404, detail="No classes found for the given subject")
    
    return [
        {
            "id": cclass["_id"],  # Convert ObjectId to string
            "name": cclass["name"],
            "subjectIds": cclass["subjectIds"]
        }
        for cclass in classes
    ]

# Run
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)


from fastapi import Path

from fastapi import Query

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
        "questionId": str_to_objectid(question_id)
    })

    return {
        "questionText": question["questionText"],
        "expectedKeywords": question.get("expectedKeywords", []),
        "responses": [
            {
                "responseId": str(resp["_id"]),
                "studentId": str(resp["studentId"]),
                "answerText": resp.get("longAnswerText", ""),
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
        "questionId": ObjectId(question_id)
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


@app.post("/exams/finalize-results")
def finalize_exam_results(exam_id: str = Query(...)):
    student_ids = db.responses.distinct("studentId", {"examId": exam_id})
    questions = list(db.questions.find({"examId": exam_id}))
    question_map = {str(q["_id"]): q for q in questions}

    for student_id in student_ids:
        responses = list(db.responses.find({"examId": exam_id, "studentId": student_id}))

        total = 0
        max_marks = 0

        for r in responses:
            q = question_map.get(str(r["questionId"]))
            if not q:
                continue
            total += r.get("marksAwarded") or 0
            max_marks += q.get("marks", 0)

        if max_marks == 0:
            continue

        percentage = (total / max_marks) * 100
        grade = "A" if percentage >= 80 else "B" if percentage >= 60 else "C"

        db.results.update_one(
            {"studentId": student_id, "examId": exam_id},
            {"$set": {
                "marksObtained": total,
                "totalMarks": max_marks,
                "percentage": percentage,
                "grade": grade,
                "computedAt": datetime.utcnow()
            }},
            upsert=True
        )

        # ✅ After storing results, update the exam status
        db.exams.update_one(
            {"_id": exam_id},
            {"$set": {"status": "ended"}}
        )

    return {"message": "Results finalized and stored successfully!"}
