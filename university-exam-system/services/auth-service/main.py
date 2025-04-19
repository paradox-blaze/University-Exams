from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import os

# MongoDB Setup
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
client = MongoClient(mongo_url)
db = client.university
students_collection = db.students
teachers_collection = db.teachers

app = FastAPI()

# Models
class LoginRequest(BaseModel):
    username: str
    password: str
    role: str  # 'admin', 'student', 'teacher'

@app.post("/login")
def login_user(data: LoginRequest):
    username = data.username
    password = data.password
    role = data.role

    if role == "admin":
        if username == "admin" and password == "password":
            return {
                "id": "admin",
                "name": "Administrator",
                "email": "admin@system.local",
                "role": "admin"
            }
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    elif role == "student":
        student = students_collection.find_one({"_id": username})
        if student and student.get("passwordHash") == password:
            return {
                "id": student["_id"],
                "name": student["name"],
                "email": student["email"],
                "role": "student"
            }
        raise HTTPException(status_code=401, detail="Invalid student credentials")

    elif role == "teacher":
        teacher = teachers_collection.find_one({"_id": username})
        if teacher and teacher.get("passwordHash") == password:
            return {
                "id": teacher["_id"],
                "name": teacher["name"],
                "email": teacher["email"],
                "role": "teacher"
            }
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    raise HTTPException(status_code=400, detail="Invalid role")
