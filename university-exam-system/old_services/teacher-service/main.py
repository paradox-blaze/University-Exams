from fastapi import FastAPI, HTTPException,Request
from pydantic import BaseModel
from typing import List, Optional, Literal
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
questions_collection = db.questions
teachers_collection = db.teachers
classes_collection = db["classes"]
responses_collection = db.responses


app = FastAPI()

# Helpers
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


    
class Class(BaseModel):
    id: str
    name: str
    subject_ids: List[str]

# Models
class ExamCreate(BaseModel):
    subjectId: str
    title: str
    startTime: datetime
    endTime: datetime
    durationMinutes: int
    createdBy: str
    isPublished: bool = False

class ExamOut(BaseModel):
    id: str
    title: str
    subjectId: str
    createdBy: str
    startTime: datetime
    endTime: datetime
    durationMinutes: int
    status: str
    isPublished: bool

class QuestionCreate(BaseModel):
    questionText: str
    type: Literal["mcq", "long"]
    marks: int
    options: Optional[List[str]] = None
    correctAnswerIndex: Optional[int] = None
    expectedKeywords: Optional[List[str]] = None

# Routes




from fastapi import Path






from fastapi import HTTPException



from fastapi import HTTPException, Request






from fastapi import Body

















from fastapi import Path

from fastapi import Query









