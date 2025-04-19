/*
---------------------------------------------------------
                    MongoDB Data Model
---------------------------------------------------------
This file describes the collections and their structures.
Each collection is used for a specific purpose in the
Student Examination System.
---------------------------------------------------------

1. **Students Collection**
---------------------------
Purpose: Stores student information and the subjects they are enrolled in.

Structure:
{
  "_id": ObjectId,                // Unique identifier for the student
  "name": String,                 // Full name of the student
  "email": String,                // Email address of the student
  "course_ids": [ObjectId]        // Array of subject IDs the student is enrolled in
}

Example Document:
{
  "_id": ObjectId("5f1b2b3a4c3e1a0dce78a3b1"),
  "name": "John Doe",
  "email": "john.doe@example.com",
  "course_ids": [
    ObjectId("5f1b2b3a4c3e1a0dce78a3b2"),  // Subject ID 1
    ObjectId("5f1b2b3a4c3e1a0dce78a3b3")   // Subject ID 2
  ]
}

2. **Teachers Collection**
---------------------------
Purpose: Stores teacher information and the subjects they are assigned to.

Structure:
{
  "_id": ObjectId,                // Unique identifier for the teacher
  "name": String,                 // Full name of the teacher
  "email": String,                // Email address of the teacher
  "subject_ids": [ObjectId]       // Array of subject IDs the teacher is assigned to
}

Example Document:
{
  "_id": ObjectId("5f1b2b3a4c3e1a0dce78a3b4"),
  "name": "Dr. Smith",
  "email": "dr.smith@example.com",
  "subject_ids": [
    ObjectId("5f1b2b3a4c3e1a0dce78a3b2"),  // Subject ID 1
    ObjectId("5f1b2b3a4c3e1a0dce78a3b5")   // Subject ID 3
  ]
}

3. **Subjects Collection**
---------------------------
Purpose: Stores information about subjects and the teachers/students related to those subjects.

Structure:
{
  "_id": ObjectId,                // Unique identifier for the subject
  "name": String,                 // Name of the subject (e.g., "Math", "Physics")
  "teacherIds": [ObjectId],       // Array of teacher IDs who teach this subject
  "studentsIds": [ObjectId]       // Array of student IDs enrolled in this subject
}

Example Document:
{
  "_id": ObjectId("5f1b2b3a4c3e1a0dce78a3b2"),
  "name": "Mathematics",
  "teacherIds": [
    ObjectId("5f1b2b3a4c3e1a0dce78a3b4")   // Teacher ID 1 (Dr. Smith)
  ],
  "studentsIds": [
    ObjectId("5f1b2b3a4c3e1a0dce78a3b1"),  // Student ID 1 (John Doe)
    ObjectId("5f1b2b3a4c3e1a0dce78a3b6")   // Student ID 2 (Jane Doe)
  ]
}

4. **Exams Collection**
---------------------------
Purpose: Stores information about exams, including exam status, and the relationship to subjects.

Structure:
{
  "_id": ObjectId,                // Unique identifier for the exam
  "title": String,                // Title of the exam (e.g., "Midterm Exam")
  "subjectId": ObjectId,          // Subject ID that the exam is associated with
  "startTime": DateTime,          // Start time of the exam
  "endTime": DateTime,            // End time of the exam
  "status": String,               // Status of the exam ('live', 'completed', 'reval')
  "durationMinutes": Integer      // Duration of the exam in minutes
}

Example Document:
{
  "_id": ObjectId("5f1b2b3a4c3e1a0dce78a3b7"),
  "title": "Midterm Exam",
  "subjectId": ObjectId("5f1b2b3a4c3e1a0dce78a3b2"),  // Subject ID (Mathematics)
  "startTime": ISODate("2025-04-15T10:00:00Z"),        // Exam start time
  "endTime": ISODate("2025-04-15T12:00:00Z"),          // Exam end time
  "status": "live",                                    // Exam is live
  "durationMinutes": 120                               // 2-hour exam
}

5. **Questions Collection**
---------------------------
Purpose: Stores questions for exams, with different types like MCQ and long format.

Structure:
{
  "_id": ObjectId,                // Unique identifier for the question
  "examId": ObjectId,             // Exam ID this question belongs to
  "questionText": String,         // Text of the question
  "type": String,         // Type of the question ('MCQ', 'Long format')
  "options": [String],            // Options for MCQ (optional for long-format)
  "correctAnswer": String         // Correct answer for the question
}

Example Document:
{
  "_id": ObjectId("5f1b2b3a4c3e1a0dce78a3b8"),
  "examId": ObjectId("5f1b2b3a4c3e1a0dce78a3b7"),  // Exam ID (Midterm Exam)
  "questionText": "What is 2 + 2?",
  "type": "MCQ",
  "options": ["3", "4", "5", "6"],
  "correctAnswer": "4"
}

6. **Responses Collection**
---------------------------
Purpose: Stores the responses given by students for each question in an exam.

Structure:
{
  "_id": ObjectId,                // Unique identifier for the response
  "studentId": ObjectId,          // Student ID who answered the question
  "examId": ObjectId,             // Exam ID this response is for
  "id": ObjectId,                // Question ID that was answered
  "answer": String,               // Answer provided by the student
  "marks": Integer,               // Marks awarded for this answer (calculated after evaluation)
  "isReval": Boolean              // Indicates if the answer is under re-evaluation
}

Example Document:
{
  "_id": ObjectId("5f1b2b3a4c3e1a0dce78a3b9"),
  "studentId": ObjectId("5f1b2b3a4c3e1a0dce78a3b1"),  // Student ID (John Doe)
  "examId": ObjectId("5f1b2b3a4c3e1a0dce78a3b7"),     // Exam ID (Midterm Exam)
  "id": ObjectId("5f1b2b3a4c3e1a0dce78a3b8"), // Question ID (What is 2 + 2?)
  "answer": "4",                                    // Student's answer
  "marks": 1,                                      // Marks awarded for the correct answer
  "isReval": false                                  // Answer is not under re-evaluation
}

7. **Revaluation Requests Collection**
---------------------------
Purpose: Stores revaluation requests made by students for their exam answers.

Structure:
{
  "_id": ObjectId,                // Unique identifier for the revaluation request
  "studentId": ObjectId,          // Student ID who requested re-evaluation
  "examId": ObjectId,             // Exam ID for the re-evaluation request
  "id": ObjectId,         // Question ID for the re-evaluation request
  "status": String,               // Status of the revaluation ('pending', 'approved', 'denied')
  "reason": String                // Reason for re-evaluation request
}

Example Document:
{
  "_id": ObjectId("5f1b2b3a4c3e1a0dce78a3ba"),
  "studentId": ObjectId("5f1b2b3a4c3e1a0dce78a3b1"),  // Student ID (John Doe)
  "examId": ObjectId("5f1b2b3a4c3e1a0dce78a3b7"),     // Exam ID (Midterm Exam)
  "id": ObjectId("5f1b2b3a4c3e1a0dce78a3b8"), // Question ID (What is 2 + 2?)
  "status": "pending",                                 // Revaluation request status
  "reason": "The answer should be considered correct due to ambiguous wording"
}

---------------------------------------------------------
*/

