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
subjects_collection = db.subjects
students_collection = db.students
teachers_collection = db.teachers
questions_collection = db.questions

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
    course_ids: List[str]

class Teacher(BaseModel):
    name: str
    email: str
    subject_ids: List[str]

class ExamStatusUpdate(BaseModel):
    status: str

class SubjectAssignment(BaseModel):
    teacher_id: str

class StudentAssignment(BaseModel):
    student_id: str

# ========== CREATE ROUTES ==========

# ========== CREATE ROUTES ==========

@app.post("/admin/classes")
def create_class(class_name: str):
    # Check if the class already exists
    if students_collection.find_one({"class": class_name}):
        raise HTTPException(status_code=400, detail="Class already exists")
    
    # Assuming no specific attributes other than name for the class
    students_collection.update_many(
        {},  # Update all students
        {"$set": {"class": class_name}}  # Set the new class for all students (optional)
    )
    return {"message": f"Class {class_name} created successfully!"}

@app.post("/admin/exams")
def create_exam(exam_title: str, subject_id: str, start_time: datetime, end_time: datetime):
    # Validate subject_id
    subject = subjects_collection.find_one({"_id": str_to_objectid(subject_id)})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Create the exam document
    exam = {
        "title": exam_title,
        "subjectId": str_to_objectid(subject_id),
        "startTime": start_time,
        "endTime": end_time,
        "status": "scheduled"  # Initial status is scheduled
    }
    exams_collection.insert_one(exam)
    return {"message": f"Exam '{exam_title}' created successfully!"}

@app.post("/admin/subjects")
def create_subject(subject_name: str, subject_code: str):
    # Check if the subject already exists
    if subjects_collection.find_one({"name": subject_name}):
        raise HTTPException(status_code=400, detail="Subject already exists")
    
    # Create the subject document
    subject = {
        "name": subject_name,
        "code": subject_code,
        "teacherIds": []  # Start with no teachers assigned
    }
    subjects_collection.insert_one(subject)
    return {"message": f"Subject '{subject_name}' created successfully!"}

# ========== ASSIGNMENT ROUTES ==========

@app.post("/admin/subjects/{subject_id}/assign_teacher")
def assign_teacher_to_subject(subject_id: str, assignment: SubjectAssignment):
    if not (subjects_collection.find_one({"_id": str_to_objectid(subject_id)}) and 
            teachers_collection.find_one({"_id": str_to_objectid(assignment.teacher_id)})):
        raise HTTPException(status_code=404, detail="Subject or teacher not found")
    
    subjects_collection.update_one(
        {"_id": str_to_objectid(subject_id)},
        {"$addToSet": {"teacherIds": str_to_objectid(assignment.teacher_id)}}
    )
    teachers_collection.update_one(
        {"_id": str_to_objectid(assignment.teacher_id)},
        {"$addToSet": {"subject_ids": str_to_objectid(subject_id)}}
    )
    return {"message": "Teacher assigned to subject successfully!"}

@app.post("/admin/subjects/{subject_id}/assign_student")
def assign_student_to_subject(subject_id: str, assignment: StudentAssignment):
    if not (subjects_collection.find_one({"_id": str_to_objectid(subject_id)}) and 
            students_collection.find_one({"_id": str_to_objectid(assignment.student_id)})):
        raise HTTPException(status_code=404, detail="Subject or student not found")
    
    subjects_collection.update_one(
        {"_id": str_to_objectid(subject_id)},
        {"$addToSet": {"studentsIds": str_to_objectid(assignment.student_id)}}
    )
    students_collection.update_one(
        {"_id": str_to_objectid(assignment.student_id)},
        {"$addToSet": {"course_ids": str_to_objectid(subject_id)}}
    )
    return {"message": "Student assigned to subject successfully!"}

# ========== STATUS ROUTES ==========

@app.put("/admin/exams/{exam_id}/status")
def change_exam_status(exam_id: str, status_update: ExamStatusUpdate):
    if not exams_collection.find_one({"_id": str_to_objectid(exam_id)}):
        raise HTTPException(status_code=404, detail="Exam not found")

    exams_collection.update_one(
        {"_id": str_to_objectid(exam_id)},
        {"$set": {"status": status_update.status}}
    )
    return {"message": f"Exam status updated to {status_update.status}!"}

# ========== GET ROUTES ==========

@app.get("/admin/students")
def get_all_students():
    students = list(students_collection.find())
    return [
        {
            "_id": str(s["_id"]),
            "name": s.get("name"),
            "email": s.get("email"),
            "class": s.get("class"),
            "rollNumber": s.get("rollNumber"),
            "course_names": [
                subjects_collection.find_one({"_id": ObjectId(cid)}).get("name") 
                for cid in s.get("course_ids", [])
            ]
        }
        for s in students
    ]

@app.get("/admin/teachers")
def get_all_teachers():
    teachers = list(teachers_collection.find())
    return [
        {
            "_id": str(t["_id"]),
            "name": t.get("name"),
            "email": t.get("email"),
            "subject_names": [
                subjects_collection.find_one({"_id": ObjectId(sid)}).get("name")
                for sid in t.get("subject_ids", [])
            ]
        }
        for t in teachers
    ]

@app.get("/admin/subjects")
def get_all_subjects():
    subjects = list(subjects_collection.find())
    return [
        {
            "_id": str(s["_id"]),
            "name": s.get("name"),
            "code": s.get("code"),
            "teacher_names": [
                teachers_collection.find_one({"_id": ObjectId(tid)}).get("name")
                for tid in s.get("teacherIds", [])
            ]
        }
        for s in subjects
    ]

@app.get("/admin/exams")
def get_all_exams():
    exams = list(exams_collection.find())
    return [
        {
            "_id": str(e["_id"]),
            "title": e.get("title"),
            "subject_name": subjects_collection.find_one({"_id": ObjectId(e.get("subjectId"))}).get("name"),
            "status": e.get("status"),
            "startTime": e.get("startTime"),
            "endTime": e.get("endTime")
        }
        for e in exams
    ]

@app.get("/admin/questions")
def get_questions(examId: Optional[str] = Query(None)):
    query = {}
    if examId:
        query["examId"] = str_to_objectid(examId)
    questions = list(questions_collection.find(query))
    return [
        {
            "_id": str(q["_id"]),
            "exam_title": exams_collection.find_one({"_id": ObjectId(q["examId"])}).get("title"),
            "questionText": q["questionText"],
            "type": q["type"],
            "marks": q["marks"]
        }
        for q in questions
    ]

@app.get("/admin/classes/{class_name}/students")
def get_students_by_class(class_name: str):
    students = list(students_collection.find({"class": class_name}))
    return [
        {
            "_id": str(s["_id"]),
            "name": s.get("name"),
            "email": s.get("email"),
            "rollNumber": s.get("rollNumber"),
            "course_names": [
                subjects_collection.find_one({"_id": ObjectId(cid)}).get("name") 
                for cid in s.get("course_ids", [])
            ]
        }
        for s in students
    ]

@app.get("/admin/subjects/{subject_id}/teachers")
def get_teachers_for_subject(subject_id: str):
    subject = subjects_collection.find_one({"_id": str_to_objectid(subject_id)})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    teacher_ids = subject.get("teacherIds", [])
    teachers = list(teachers_collection.find({"_id": {"$in": teacher_ids}}))

    return [
        {"_id": str(t["_id"]), "name": t["name"], "email": t["email"]}
        for t in teachers
    ]

@app.get("/admin/teachers/{teacher_id}/subjects")
def get_subjects_for_teacher(teacher_id: str):
    teacher = teachers_collection.find_one({"_id": str_to_objectid(teacher_id)})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    subject_ids = teacher.get("subject_ids", [])
    subjects = list(subjects_collection.find({"_id": {"$in": subject_ids}}))

    return [
        {"_id": str(s["_id"]), "name": s["name"], "code": s["code"]}
        for s in subjects
    ]


# ========== DELETE ROUTES ==========

@app.delete("/admin/students/{student_id}")
def delete_student(student_id: str):
    student = students_collection.find_one({"_id": str_to_objectid(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    students_collection.delete_one({"_id": str_to_objectid(student_id)})
    return {"message": "Student deleted successfully!"}

@app.delete("/admin/teachers/{teacher_id}")
def delete_teacher(teacher_id: str):
    teacher = teachers_collection.find_one({"_id": str_to_objectid(teacher_id)})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    teachers_collection.delete_one({"_id": str_to_objectid(teacher_id)})
    return {"message": "Teacher deleted successfully!"}

@app.delete("/admin/subjects/{subject_id}")
def delete_subject(subject_id: str):
    subject = subjects_collection.find_one({"_id": str_to_objectid(subject_id)})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    subjects_collection.delete_one({"_id": str_to_objectid(subject_id)})
    return {"message": "Subject deleted successfully!"}

@app.delete("/admin/exams/{exam_id}")
def delete_exam(exam_id: str):
    exam = exams_collection.find_one({"_id": str_to_objectid(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    exams_collection.delete_one({"_id": str_to_objectid(exam_id)})
    return {"message": "Exam deleted successfully!"}

@app.delete("/admin/classes/{class_name}")
def delete_class(class_name: str):
    # Remove class from all students
    students_collection.update_many(
        {"class": class_name},
        {"$unset": {"class": ""}}
    )
    
    # Delete the class from the 'classes' collection
    result = db.classes.delete_one({"class_name": class_name})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Class {class_name} not found")
    
    return {"message": f"Class {class_name} deleted successfully!"}

# ========== MAIN RUN ==========
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
