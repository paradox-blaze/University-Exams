from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
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

class SubjectAssignment(BaseModel):
    teacher_id: str

@app.post("/subjects")
def create_subject(subject_name: str, subject_code: str):
    base_id = subject_code.lower()
    existing = list(subjects_collection.find({"_id": {"$regex": f"^{base_id}"}}))
    subject_id = f"{base_id}{len(existing) + 1}"

    if subjects_collection.find_one({"_id": subject_id}) or subjects_collection.find_one({"name": subject_name}):
        raise HTTPException(status_code=400, detail="Subject already exists")

    subject = {
        "_id": subject_id,
        "name": subject_name,
        "code": subject_code,
        "teacherIds": []
    }
    subjects_collection.insert_one(subject)
    return {"message": f"Subject '{subject_name}' created with ID '{subject_id}'!"}

@app.post("/classes")
def create_class(class_name: str):
    return {"message": f"Class '{class_name}' created (virtually)!"}

@app.post("/subjects/{subject_id}/assign_teacher")
def assign_teacher_to_subject(subject_id: str, assignment: SubjectAssignment):
    # Check if both subject and teacher exist
    subject = subjects_collection.find_one({"_id": subject_id})
    teacher = teachers_collection.find_one({"_id": assignment.teacher_id})
    
    if not subject or not teacher:
        raise HTTPException(status_code=404, detail="Subject or teacher not found")
    
    # Only update the subject document
    subjects_collection.update_one(
        {"_id": subject_id},
        {"$addToSet": {"teacherIds": assignment.teacher_id}}
    )
    
    return {"message": "Teacher assigned to subject successfully!"}

@app.get("/subjects")
def get_all_subjects():
    subjects = list(subjects_collection.find())
    return [
        {
            "_id": s["_id"],
            "name": s.get("name"),
            "code": s.get("code"),
            "teacherIds": s.get("teacherIds"),
            "teacher_names": [teachers_collection.find_one({"_id": tid}).get("name") for tid in s.get("teacherIds", []) if teachers_collection.find_one({"_id": tid})]
        }
        for s in subjects
    ]

@app.delete("/admin/subjects/{subject_id}")
def delete_subject(subject_id: str):
    if not subjects_collection.find_one({"_id": subject_id}):
        raise HTTPException(status_code=404, detail="Subject not found")
    subjects_collection.delete_one({"_id": subject_id})
    return {"message": "Subject deleted successfully!"}

@app.get("/students/by-class")
def get_students_by_class(class_id: str):
    students = list(students_collection.find({"classId": class_id}))
    if not students:
        raise HTTPException(status_code=404, detail="No students found for this class")
    return [
        {
            "id": s["_id"],
            "name": s["name"],
            "email": s["email"],
            "rollNumber": s["rollNumber"],
            "classId": s["classId"]
        }
        for s in students
    ]

@app.get("/subjects-by-teacher")
def get_subjects_by_teacher(teacher_id: str):
    try:
        # Query MongoDB to find subjects by teacher_id in the teacherIds array
        subjects_cursor = db.subjects.find({"teacherIds": teacher_id})
        
        # Use count_documents() instead of the deprecated count()
        subject_count = db.subjects.count_documents({"teacherIds": teacher_id})
        
        if subject_count == 0:
            raise HTTPException(status_code=404, detail="No subjects found for this teacher")
        
        # Return a list of subjects for the given teacher
        subjects = [
            {
                "id": str(subject["_id"]),
                "name": subject["name"],
                "code": subject["code"],
                "teacherIds": subject["teacherIds"]
            }
            for subject in subjects_cursor
        ]
        
        return subjects
    
    except Exception as e:
        # Return a 500 Internal Server Error
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/subject-classes")
def get_classes_by_subject(subject_id: str):
    # Fetch the classes that are associated with the given subject
    classes = classes_collection.find({"subjectIds": subject_id})
    
    if not classes:
        raise HTTPException(status_code=404, detail="No classes found for the given subject")
    
    return [
        {
            "id": cclass["_id"],  # Convert ObjectId to string
            "name": cclass["name"],
            "subjectIds": cclass["subjectIds"]
        }
        for cclass in classes
    ]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)