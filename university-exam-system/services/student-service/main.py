from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr, ValidationError
from bson import ObjectId
import os
import uvicorn

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
    email: EmailStr  # Ensures email is valid
    course_ids: list[str]  # Ensures course_ids is a list of strings

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
    try:
        student_data = student.dict()
        students_collection.insert_one(student_data)
        return {"message": "Student created successfully!"}
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

@app.get("/students/{id}")
def get_student(id: str):
    student = students_collection.find_one({"_id": str_to_objectid(id)})
    if student:
        return {"id": str(student["_id"]), "name": student["name"], "email": student["email"]}
    raise HTTPException(status_code=404, detail="Student not found")

@app.put("/students/{id}")
def update_student(id: str, student: Student):
    try:
        student_data = student.dict()
        result = students_collection.update_one({"_id": str_to_objectid(id)}, {"$set": student_data})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        return {"message": "Student updated successfully!"}
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

@app.delete("/students/{id}")
def delete_student(id: str):
    result = students_collection.delete_one({"_id": str_to_objectid(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully!"}

# Add endpoint to get student name by ID
@app.get("/students/{id}/name")
def get_student_name(id: str):
    student = students_collection.find_one({"_id": str_to_objectid(id)})
    if student:
        return {"name": student["name"]}
    raise HTTPException(status_code=404, detail="Student not found")

# Add endpoint to get exams for a student
@app.get("/students/{id}/exams")
def get_student_exams(id: str):
    student = students_collection.find_one({"_id": str_to_objectid(id)})
    if student:
        # Assuming exams are stored in a field called 'exams' in the student document
        return {"exams": student.get("exams", [])}
    raise HTTPException(status_code=404, detail="Student not found")

# Add endpoint to get courses for a student
@app.get("/students/{id}/courses")
def get_student_courses(id: str):
    student = students_collection.find_one({"_id": str_to_objectid(id)})
    if student:
        # Assuming courses are stored in a field called 'course_ids' in the student document
        return {"courses": student.get("course_ids", [])}
    raise HTTPException(status_code=404, detail="Student not found")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)