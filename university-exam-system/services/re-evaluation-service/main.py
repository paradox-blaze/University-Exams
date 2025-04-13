from fastapi import FastAPI, HTTPException, Query
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
questions_collection = db.questions
responses_collection = db.responses
students_collection = db.students
reval_requests_collection = db.reval_requests

app = FastAPI()

# Helpers
def str_to_objectid(id: str):
    try:
        return ObjectId(id)
    except Exception:
        return None

def is_exam_reval(exam):
    return exam["status"] == "reval"

# Models
class RevalRequest(BaseModel):
    reason: str

class RevalRequestOut(BaseModel):
    request_id: str
    exam_id: str
    student_id: str
    reason: str
    status: str
    createdAt: datetime
    updatedAt: datetime

class RevalReview(BaseModel):
    marksObtained: int  # New marks after re-evaluation

# Routes

@app.post("/reval/{exam_id}/request")
def request_reval(exam_id: str, student_id: str, reval_request: RevalRequest):
    # Check if exam is in revaluation status
    exam = exams_collection.find_one({"_id": str_to_objectid(exam_id)})
    if not exam or not is_exam_reval(exam):
        raise HTTPException(status_code=404, detail="Exam not in reval status or not found")

    # Create revaluation request
    request_data = {
        "examId": str_to_objectid(exam_id),
        "studentId": str_to_objectid(student_id),
        "reason": reval_request.reason,
        "status": "pending",
        "createdAt": datetime.now(),
        "updatedAt": datetime.now()
    }

    # Insert reval request into the database
    reval_requests_collection.insert_one(request_data)

    return {"message": "Re-evaluation request submitted successfully!"}

@app.get("/reval/requests")
def get_reval_requests(exam_id: str):
    # Get revaluation requests for a specific exam
    requests = reval_requests_collection.find({"examId": str_to_objectid(exam_id), "status": "pending"})
    return [
        RevalRequestOut(
            request_id=str(req["_id"]),
            exam_id=str(req["examId"]),
            student_id=str(req["studentId"]),
            reason=req["reason"],
            status=req["status"],
            createdAt=req["createdAt"],
            updatedAt=req["updatedAt"]
        )
        for req in requests
    ]

@app.post("/reval/{request_id}/review")
def review_reval(request_id: str, reval_review: RevalReview):
    # Review and correct re-evaluation request
    request = reval_requests_collection.find_one({"_id": str_to_objectid(request_id)})
    if not request:
        raise HTTPException(status_code=404, detail="Re-evaluation request not found")

    # Update the student's response marks if necessary
    responses_collection.update_many(
        {"examId": request["examId"], "studentId": request["studentId"]},
        {"$set": {"marksObtained": reval_review.marksObtained}}
    )

    # Update the revaluation request status to approved
    reval_requests_collection.update_one(
        {"_id": str_to_objectid(request_id)},
        {"$set": {"status": "approved", "updatedAt": datetime.now()}}
    )

    return {"message": "Re-evaluation request reviewed and marks updated!"}

@app.get("/reval/requests/{request_id}")
def get_reval_request_status(request_id: str):
    # Check status of re-evaluation request
    request = reval_requests_collection.find_one({"_id": str_to_objectid(request_id)})
    if not request:
        raise HTTPException(status_code=404, detail="Re-evaluation request not found")

    return {"status": request["status"], "reason": request["reason"]}

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
