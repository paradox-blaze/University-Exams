from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from bson import ObjectId
import os

# MongoDB connection URL
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
client = MongoClient(mongo_url)
db = client.university  # Connect to the `university` database
students_collection = db.students

# FastAPI instance
app = FastAPI()

# Student model
class Student(BaseModel):
    name: str
    email: str
    course_ids: list

# Helper function to convert MongoDB object ID
def str_to_objectid(id: str):
    try:
        return ObjectId(id)
    except Exception:
        return None

# API Routes
@app.get("/students")
def get_students():
    students = students_collection.find()
    return [{"id": str(student["_id"]), "name": student["name"], "email": student["email"]} for student in students]

@app.post("/students")
def create_student(student: Student):
    student_data = student.dict()
    students_collection.insert_one(student_data)
    return {"message": "Student created successfully!"}

@app.get("/students/{id}")
def get_student(id: str):
    student = students_collection.find_one({"_id": str_to_objectid(id)})
    if student:
        return {"id": str(student["_id"]), "name": student["name"], "email": student["email"]}
    raise HTTPException(status_code=404, detail="Student not found")

@app.put("/students/{id}")
def update_student(id: str, student: Student):
    student_data = student.dict()
    result = students_collection.update_one({"_id": str_to_objectid(id)}, {"$set": student_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student updated successfully!"}

@app.delete("/students/{id}")
def delete_student(id: str):
    result = students_collection.delete_one({"_id": str_to_objectid(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully!"}
