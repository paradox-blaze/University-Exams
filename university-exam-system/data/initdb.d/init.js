db = db.getSiblingDB("university");

// Collections
const students = db.students;
const teachers = db.teachers;
const courses = db.courses;
const exams = db.exams;
const questions = db.questions;

// Check if the students collection already has data
if (students.countDocuments() === 0) {
    const teacher1 = ObjectId();
    const teacher2 = ObjectId();

    const student1 = ObjectId();
    const student2 = ObjectId();

    const course1 = ObjectId();
    const course2 = ObjectId();

    const exam1 = ObjectId();
    const exam2 = ObjectId();

    // Insert sample data only if collections are empty
    students.insertMany([
        { _id: student1, name: "Aarav Patel", email: "aarav.patel@example.com", course_ids: [course1] },
        { _id: student2, name: "Ishita Mehta", email: "ishita.mehta@example.com", course_ids: [course2] }
    ]);

    teachers.insertMany([
        { _id: teacher1, name: "Dr. Radhika Nair", email: "radhika.nair@university.com", assigned_courses: [course1] },
        { _id: teacher2, name: "Prof. Anil Kumar", email: "anil.kumar@university.com", assigned_courses: [course2] }
    ]);

    courses.insertMany([
        { _id: course1, course_name: "Data Structures", teacher_id: teacher1, exam_ids: [exam1] },
        { _id: course2, course_name: "Computer Networks", teacher_id: teacher2, exam_ids: [exam2] }
    ]);

    exams.insertMany([
        { _id: exam1, exam_name: "DSA Midterm", course_id: course1, questions: [] },
        { _id: exam2, exam_name: "Networks Midterm", course_id: course2, questions: [] }
    ]);

    questions.insertMany([
        {
            question_text: "Which data structure uses LIFO?",
            options: ["Queue", "Stack", "Linked List"],
            answer: "Stack",
            exam_id: exam1
        },
        {
            question_text: "Which protocol is used for secure communication over the internet?",
            options: ["HTTP", "FTP", "HTTPS"],
            answer: "HTTPS",
            exam_id: exam2
        }
    ]);

    // Create indexes
    students.createIndex({ email: 1 }, { unique: true });
    teachers.createIndex({ email: 1 }, { unique: true });
    courses.createIndex({ course_name: 1 }, { unique: true });

    print("✅ MongoDB initialized with sample university data.");
} else {
    print("🛑 Database already initialized, skipping seeding.");
}
