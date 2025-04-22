from fastapi import FastAPI, HTTPException, Query, Path, Request
from pydantic import BaseModel
from typing import Optional
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

class ExamStatusUpdate(BaseModel):
    status: str

def get_student_courses(student_id: str):
    student = students_collection.find_one({"_id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    myclass = student['classId']
    my_class_object = classes_collection.find_one({"_id": myclass})
    print(my_class_object['subjectIds'])
    return my_class_object['subjectIds']

@app.post("/exams")
def create_exam(exam_title: str, subject_id: str, start_time: datetime, end_time: datetime):
    subject = subjects_collection.find_one({"_id": subject_id})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    base_id = exam_title.lower().replace(" ", "")
    existing = list(exams_collection.find({"_id": {"$regex": f"^{base_id}"}}))
    exam_id = f"{base_id}-{len(existing)+1}"

    if exams_collection.find_one({"_id": exam_id}):
        raise HTTPException(status_code=400, detail="Exam ID already exists")

    exam = {
        "_id": exam_id,
        "title": exam_title,
        "subjectId": subject_id,
        "startTime": start_time,
        "endTime": end_time,
        "status": "scheduled"
    }
    exams_collection.insert_one(exam)
    return {"message": f"Exam '{exam_title}' created with ID '{exam_id}'!"}

@app.put("/exams/{exam_id}/status")
def change_exam_status(exam_id: str, status_update: ExamStatusUpdate):
    if not exams_collection.find_one({"_id": exam_id}):
        raise HTTPException(status_code=404, detail="Exam not found")

    exams_collection.update_one({"_id": exam_id}, {"$set": {"status": status_update.status}})
    return {"message": f"Exam status updated to {status_update.status}!"}

@app.get("/exams")
def get_all_exams():
    exams = list(exams_collection.find())
    return [
        {
            "_id": e["_id"],
            "title": e.get("title"),
            "subject_name": subjects_collection.find_one({"_id": e.get("subjectId")}).get("name"),
            "status": e.get("status"),
            "startTime": e.get("startTime"),
            "endTime": e.get("endTime")
        }
        for e in exams
    ]

@app.delete("/admin/exams/{exam_id}")
def delete_exam(exam_id: str):
    if not exams_collection.find_one({"_id": exam_id}):
        raise HTTPException(status_code=404, detail="Exam not found")
    exams_collection.delete_one({"_id": exam_id})
    return {"message": "Exam deleted successfully!"}

@app.get("/exams/by-student")
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
            q = questions_collection.find_one({"_id": r["id"]})
            e = exams_collection.find_one({"_id": r["examId"]})
            if subject_id and e["subjectId"] != subject_id:
                continue
            results.append({
                "examTitle": e["title"],
                "questionText": q["questionText"],
                "longAnswerText": r.get("longAnswerText", r.get("longAnswerText", "")),
                "marksObtained": r.get("marksAwarded", 0),
                "type": r["type"]
            })
        if results:
            final.append({
                "studentId": student_id,
                "studentName": s["name"],
                "results": results
            })
    return final


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

@app.get("/exams/by-subject")
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

from fastapi import FastAPI, HTTPException, Query
from datetime import datetime

@app.post("/exams/finalize-results")
def finalize_exam_results(exam_id: str = Query(...)):
    student_ids = db.responses.distinct("studentId", {"examId": exam_id})
    questions = list(db.questions.find({"examId": exam_id}))
    question_map = {str(q["_id"]): q for q in questions}

    # 🔍 Fetch grade boundaries from config
    config = db.config.find_one({"_id": "grade_boundaries"})
    if not config:
        raise HTTPException(status_code=500, detail="Grade boundaries not configured")

    for student_id in student_ids:
        responses = list(db.responses.find({"examId": exam_id, "studentId": student_id}))

        total = 0
        max_marks = 0

        for r in responses:
            q = question_map.get(str(r["id"]))
            if not q:
                continue
            total += r.get("marksAwarded", 0)
            max_marks += q.get("marks", 0)

        if max_marks == 0:
            continue

        percentage = (total / max_marks) * 100

        # 🎯 Grade logic using dynamic config
        if percentage >= config.get("A", 80):
            grade = "A"
        elif percentage >= config.get("B", 60):
            grade = "B"
        elif percentage >= config.get("C", 40):
            grade = "C"
        else:
            grade = "F"

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

    # ✅ Mark exam as ended
    db.exams.update_one(
        {"_id": exam_id},
        {"$set": {"status": "ended"}}
    )

    return {"message": "Results finalized and stored successfully!"}

from pydantic import BaseModel
from fastapi import Body

class GradeBoundaries(BaseModel):
    A: int
    B: int
    C: int

@app.put("/config/grade-boundaries")
def update_grade_boundaries(boundaries: GradeBoundaries = Body(...)):
    result = db.config.update_one(
        {"_id": "grade_boundaries"},
        {"$set": boundaries.dict()},
        upsert=True
    )
    return {"message": "Grade boundaries updated."}

@app.get("/config/grade-boundaries")
def get_grade_boundaries():
    config = db.config.find_one({"_id": "grade_boundaries"})
    if not config:
        raise HTTPException(status_code=404, detail="Grade boundaries not found")
    
    return {
        "A": config.get("A", 80),
        "B": config.get("B", 60),
        "C": config.get("C", 40)
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)