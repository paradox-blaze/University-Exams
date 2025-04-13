from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from bson import ObjectId
import os
import uvicorn

# MongoDB connection URL
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
client = MongoClient(mongo_url)
db = client.university  # Connect to the `university` database
teachers_collection = db.teachers

# FastAPI instance
app = FastAPI()

# Teacher model
class Teacher(BaseModel):
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
@app.get("/teachers")
def get_teachers():
    teachers = teachers_collection.find()
    return [{"id": str(teacher["_id"]), "name": teacher["name"], "email": teacher["email"]} for teacher in teachers]

@app.post("/teachers")
def create_teacher(teacher: Teacher):
    teacher_data = teacher.dict()
    teachers_collection.insert_one(teacher_data)
    return {"message": "Teacher created successfully!"}

@app.get("/teachers/{id}")
def get_teacher(id: str):
    teacher = teachers_collection.find_one({"_id": str_to_objectid(id)})
    if teacher:
        return {"id": str(teacher["_id"]), "name": teacher["name"], "email": teacher["email"]}
    raise HTTPException(status_code=404, detail="Teacher not found")

@app.put("/teachers/{id}")
def update_teacher(id: str, teacher: Teacher):
    teacher_data = teacher.dict()
    result = teachers_collection.update_one({"_id": str_to_objectid(id)}, {"$set": teacher_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return {"message": "Teacher updated successfully!"}

@app.delete("/teachers/{id}")
def delete_teacher(id: str):
    result = teachers_collection.delete_one({"_id": str_to_objectid(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return {"message": "Teacher deleted successfully!"}



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)