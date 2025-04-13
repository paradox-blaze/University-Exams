from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
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

app = FastAPI()

# Helpers
def str_to_objectid(id: str):
    try:
        return ObjectId(id)
    except Exception:
        return None

# Models
class Student(BaseModel):
    name: str
    email: str
    course_ids: List[str]  # List of subject IDs

class Teacher(BaseModel):
    name: str
    email: str
    subject_ids: List[str]  # List of subject IDs

class ExamStatusUpdate(BaseModel):
    status: str  # 'live', 'completed', 'reval'

class SubjectAssignment(BaseModel):
    teacher_id: str  # Teacher ID to assign to subject

class StudentAssignment(BaseModel):
    student_id: str  # Student ID to assign to subject

# Routes

# Create a new student
@app.post("/admin/students")
def create_student(student: Student):
    student_data = student.dict()
    student_data["course_ids"] = [str_to_objectid(course_id) for course_id in student.course_ids]
    students_collection.insert_one(student_data)
    return {"message": "Student created successfully!"}

# Create a new teacher
@app.post("/admin/teachers")
def create_teacher(teacher: Teacher):
    teacher_data = teacher.dict()
    teacher_data["subject_ids"] = [str_to_objectid(subject_id) for subject_id in teacher.subject_ids]
    teachers_collection.insert_one(teacher_data)
    return {"message": "Teacher created successfully!"}

# Assign a teacher to a subject
@app.post("/admin/subjects/{subject_id}/assign_teacher")
def assign_teacher_to_subject(subject_id: str, assignment: SubjectAssignment):
    subject = subjects_collection.find_one({"_id": str_to_objectid(subject_id)})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    teacher = teachers_collection.find_one({"_id": str_to_objectid(assignment.teacher_id)})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Add teacher to subject
    subjects_collection.update_one(
        {"_id": str_to_objectid(subject_id)},
        {"$addToSet": {"teacherIds": str_to_objectid(assignment.teacher_id)}}
    )

    # Add subject to teacher
    teachers_collection.update_one(
        {"_id": str_to_objectid(assignment.teacher_id)},
        {"$addToSet": {"subject_ids": str_to_objectid(subject_id)}}
    )

    return {"message": "Teacher assigned to subject successfully!"}

# Assign a student to a subject
@app.post("/admin/subjects/{subject_id}/assign_student")
def assign_student_to_subject(subject_id: str, assignment: StudentAssignment):
    subject = subjects_collection.find_one({"_id": str_to_objectid(subject_id)})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    student = students_collection.find_one({"_id": str_to_objectid(assignment.student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Add student to subject
    subjects_collection.update_one(
        {"_id": str_to_objectid(subject_id)},
        {"$addToSet": {"studentsIds": str_to_objectid(assignment.student_id)}}
    )

    # Add subject to student
    students_collection.update_one(
        {"_id": str_to_objectid(assignment.student_id)},
        {"$addToSet": {"course_ids": str_to_objectid(subject_id)}}
    )

    return {"message": "Student assigned to subject successfully!"}

# Change exam status (e.g., 'live', 'completed', 'reval')
@app.put("/admin/exams/{exam_id}/status")
def change_exam_status(exam_id: str, status_update: ExamStatusUpdate):
    exam = exams_collection.find_one({"_id": str_to_objectid(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Update exam status
    exams_collection.update_one(
        {"_id": str_to_objectid(exam_id)},
        {"$set": {"status": status_update.status}}
    )

    return {"message": f"Exam status updated to {status_update.status}!"}

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
