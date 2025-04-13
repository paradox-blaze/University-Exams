from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
import os

# MongoDB connection URL
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
client = MongoClient(mongo_url)
db = client.university  # Connect to the `university` database
courses_collection = db.courses
exams_collection = db.exams

# FastAPI instance
app = FastAPI()

# Models for request bodies
class Course(BaseModel):
    name: str
    teacher_id: str

class Exam(BaseModel):
    name: str
    course_id: str
    date: str

# API Routes
@app.get("/admin/students")
def list_students():
    students = db.students.find()
    return [{"id": str(student["_id"]), "name": student["name"]} for student in students]

@app.get("/admin/teachers")
def list_teachers():
    teachers = db.teachers.find()
    return [{"id": str(teacher["_id"]), "name": teacher["name"]} for teacher in teachers]

@app.post("/admin/courses")
def create_course(course: Course):
    course_data = course.dict()
    courses_collection.insert_one(course_data)
    return {"message": "Course created successfully!"}

@app.post("/admin/exams")
def create_exam(exam: Exam):
    exam_data = exam.dict()
    exams_collection.insert_one(exam_data)
    return {"message": "Exam created successfully!"}

@app.post("/admin/assign_teacher")
def assign_teacher(course_id: str, teacher_id: str):
    courses_collection.update_one({"_id": course_id}, {"$set": {"teacher_id": teacher_id}})
    return {"message": "Teacher assigned to course successfully!"}
