from fastapi import FastAPI, HTTPException
from typing import Optional
from pymongo import MongoClient
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

@app.get("/students")
def get_all_students():
    students = list(students_collection.find())
    students_other = students_collection.find()
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

@app.delete("/admin/students/{student_id}")
def delete_student(student_id: str):
    if not students_collection.find_one({"_id": student_id}):
        raise HTTPException(status_code=404, detail="Student not found")
    students_collection.delete_one({"_id": student_id})
    return {"message": "Student deleted successfully!"}

@app.delete("/teachers/{teacher_id}")
def delete_teacher(teacher_id: str):
    if not teachers_collection.find_one({"_id": teacher_id}):
        raise HTTPException(status_code=404, detail="Teacher not found")
    teachers_collection.delete_one({"_id": teacher_id})
    return {"message": "Teacher deleted successfully!"}

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
        "classId": student["classId"]
    }

@app.get("/get_name")
def get_teacher_name(id: str):
    teacher = teachers_collection.find_one({"_id": id})
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {"teacher_name": teacher["name"]}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)