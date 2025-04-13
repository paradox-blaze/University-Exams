from pymongo import MongoClient
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017")
db = client.university  # Use the database `university`

# Collections
students = db.students
teachers = db.teachers
courses = db.courses
exams = db.exams
questions = db.questions

# Create sample data
students_data = [
    {"_id": ObjectId(), "name": "John Doe", "email": "johndoe@example.com", "course_ids": []},
    {"_id": ObjectId(), "name": "Alice Smith", "email": "alicesmith@example.com", "course_ids": []}
]

teachers_data = [
    {"_id": ObjectId(), "name": "Dr. Helen Brown", "email": "helenb@university.com", "assigned_courses": []},
    {"_id": ObjectId(), "name": "Prof. George White", "email": "georgew@university.com", "assigned_courses": []}
]

courses_data = [
    {"_id": ObjectId(), "course_name": "Mathematics 101", "teacher_id": teachers_data[0]["_id"], "exam_ids": []},
    {"_id": ObjectId(), "course_name": "Physics 101", "teacher_id": teachers_data[1]["_id"], "exam_ids": []}
]

exams_data = [
    {"_id": ObjectId(), "exam_name": "Midterm Math Exam", "course_id": courses_data[0]["_id"], "questions": []},
    {"_id": ObjectId(), "exam_name": "Midterm Physics Exam", "course_id": courses_data[1]["_id"], "questions": []}
]

questions_data = [
    {"_id": ObjectId(), "question_text": "What is 2 + 2?", "options": ["3", "4", "5"], "answer": "4", "exam_id": exams_data[0]["_id"]},
    {"_id": ObjectId(), "question_text": "What is the force of gravity?", "options": ["9.8m/s²", "8.9m/s²", "10.0m/s²"], "answer": "9.8m/s²", "exam_id": exams_data[1]["_id"]}
]

# Insert sample data
students.insert_many(students_data)
teachers.insert_many(teachers_data)
courses.insert_many(courses_data)
exams.insert_many(exams_data)
questions.insert_many(questions_data)

# Optional: Create indexes (for example, on email and course_id for fast lookups)
students.create_index([("email", 1)], unique=True)
teachers.create_index([("email", 1)], unique=True)
courses.create_index([("course_name", 1)], unique=True)

print("MongoDB initialized with sample data.")
