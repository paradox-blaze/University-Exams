from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
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

app = FastAPI()

# Models
class ExamStatusUpdate(BaseModel):
    status: str

class SubjectAssignment(BaseModel):
    teacher_id: str

class StudentAssignment(BaseModel):
    student_id: str

# ========== CREATE ROUTES ==========

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

@app.post("/subjects")
def create_subject(subject_name: str, subject_code: str):
    base_id = subject_code.lower()
    existing = list(subjects_collection.find({"_id": {"$regex": f"^{base_id}"}}))
    subject_id = f"{base_id}{len(existing) + 1}"

    if subjects_collection.find_one({"_id": subject_id}) or subjects_collection.find_one({"name": subject_name}):
        raise HTTPException(status_code=400, detail="Subject already exists")

    subject = {
        "_id": subject_id,
        "name": subject_name,
        "code": subject_code,
        "teacherIds": []
    }
    subjects_collection.insert_one(subject)
    return {"message": f"Subject '{subject_name}' created with ID '{subject_id}'!"}

@app.post("/classes")
def create_class(class_name: str):
    return {"message": f"Class '{class_name}' created (virtually)!"}

@app.post("/students")
def create_student(name: str, email: str, classId: str, password: str, rollNumber: Optional[str] = None):
    if students_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Student with this email already exists")

    base_id = "student"
    existing = list(students_collection.find({"_id": {"$regex": f"^{base_id}"}}))
    student_id = f"{base_id}{len(existing)+1}"

    student = {
        "_id": student_id,
        "name": name,
        "email": email,
        "rollNumber": rollNumber or student_id.upper(),
        "classId": classId,
        "passwordHash": password,
        "courseIds": []
    }
    students_collection.insert_one(student)
    return {"message": f"Student '{name}' created with ID '{student_id}'!"}

@app.post("/teachers")
def create_teacher(name: str, email: str, password: str):
    if teachers_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Teacher with this email already exists")

    base_id = "teacher"
    existing = list(teachers_collection.find({"_id": {"$regex": f"^{base_id}"}}))
    teacher_id = f"{base_id}{len(existing)+1}"

    teacher = {
        "_id": teacher_id,
        "name": name,
        "email": email,
        "passwordHash": password  # assumed to already be hashed or handled
    }
    teachers_collection.insert_one(teacher)
    return {"message": f"Teacher '{name}' created with ID '{teacher_id}'!"}


# ========== ASSIGNMENT ROUTES ==========

@app.post("/subjects/{subject_id}/assign_teacher")
def assign_teacher_to_subject(subject_id: str, assignment: SubjectAssignment):
    # Check if both subject and teacher exist
    subject = subjects_collection.find_one({"_id": subject_id})
    teacher = teachers_collection.find_one({"_id": assignment.teacher_id})
    
    if not subject or not teacher:
        raise HTTPException(status_code=404, detail="Subject or teacher not found")
    
    # Only update the subject document
    subjects_collection.update_one(
        {"_id": subject_id},
        {"$addToSet": {"teacherIds": assignment.teacher_id}}
    )
    
    return {"message": "Teacher assigned to subject successfully!"}


# ========== STATUS ROUTES ==========

@app.put("/exams/{exam_id}/status")
def change_exam_status(exam_id: str, status_update: ExamStatusUpdate):
    if not exams_collection.find_one({"_id": exam_id}):
        raise HTTPException(status_code=404, detail="Exam not found")

    exams_collection.update_one({"_id": exam_id}, {"$set": {"status": status_update.status}})
    return {"message": f"Exam status updated to {status_update.status}!"}

# ========== GET ROUTES ==========

@app.get("/students")
def get_all_students():
    students = list(students_collection.find())
    return [
        {
            "_id": s["_id"],
            "name": s.get("name"),
            "email": s.get("email"),
            "rollNumber": s.get("rollNumber"),
            "classId": s.get("classId"),
            "course_names": [subjects_collection.find_one({"_id": cid}).get("name") for cid in s.get("courseIds", []) if subjects_collection.find_one({"_id": cid})]
        }
        for s in students
    ]

@app.get("/teachers")
def get_all_teachers():
    teachers = list(teachers_collection.find())
    return [
        {
            "_id": t["_id"],
            "name": t.get("name"),
            "email": t.get("email"),
            "subject_names": [
                s["name"]
                for s in subjects_collection.find({"teacherIds": t["_id"]})
            ]
        }
        for t in teachers
    ]


@app.get("/subjects")
def get_all_subjects():
    subjects = list(subjects_collection.find())
    return [
        {
            "_id": s["_id"],
            "name": s.get("name"),
            "code": s.get("code"),
            "teacher_names": [teachers_collection.find_one({"_id": tid}).get("name") for tid in s.get("teacherIds", []) if teachers_collection.find_one({"_id": tid})]
        }
        for s in subjects
    ]

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

# ========== DELETE ROUTES ==========\n
@app.delete("/admin/students/{student_id}")
def delete_student(student_id: str):
    if not students_collection.find_one({"_id": student_id}):
        raise HTTPException(status_code=404, detail="Student not found")
    students_collection.delete_one({"_id": student_id})
    return {"message": "Student deleted successfully!"}

@app.delete("/admin/teachers/{teacher_id}")
def delete_teacher(teacher_id: str):
    if not teachers_collection.find_one({"_id": teacher_id}):
        raise HTTPException(status_code=404, detail="Teacher not found")
    teachers_collection.delete_one({"_id": teacher_id})
    return {"message": "Teacher deleted successfully!"}

@app.delete("/admin/subjects/{subject_id}")
def delete_subject(subject_id: str):
    if not subjects_collection.find_one({"_id": subject_id}):
        raise HTTPException(status_code=404, detail="Subject not found")
    subjects_collection.delete_one({"_id": subject_id})
    return {"message": "Subject deleted successfully!"}

@app.delete("/admin/exams/{exam_id}")
def delete_exam(exam_id: str):
    if not exams_collection.find_one({"_id": exam_id}):
        raise HTTPException(status_code=404, detail="Exam not found")
    exams_collection.delete_one({"_id": exam_id})
    return {"message": "Exam deleted successfully!"}

# ========== MAIN RUN ==========
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
