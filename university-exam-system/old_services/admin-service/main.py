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



class StudentAssignment(BaseModel):
    student_id: str

# ========== CREATE ROUTES ==========












# ========== ASSIGNMENT ROUTES ==========




# ========== STATUS ROUTES ==========



# ========== GET ROUTES ==========








# ========== DELETE ROUTES ==========\n






# ========== MAIN RUN ==========
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
