db = db.getSiblingDB("university");

// Drop existing data
db.students.drop();
db.teachers.drop();
db.subjects.drop();
db.exams.drop();
db.questions.drop();
db.responses.drop();
db.results.drop();

// === Insert Teachers ===
const teachers = [
  { _id: ObjectId(), name: "Alice Smith", email: "alice@university.edu", passwordHash: "hash1" },
  { _id: ObjectId(), name: "Bob Johnson", email: "bob@university.edu", passwordHash: "hash2" },
  { _id: ObjectId(), name: "Carol White", email: "carol@university.edu", passwordHash: "hash3" },
  { _id: ObjectId(), name: "David Brown", email: "david@university.edu", passwordHash: "hash4" },
  { _id: ObjectId(), name: "Eva Green", email: "eva@university.edu", passwordHash: "hash5" }
];
db.teachers.insertMany(teachers);

// === Insert Subjects ===
const subjects = [
  { _id: ObjectId(), name: "Mathematics", code: "MATH101", teacherId: teachers[0]._id },
  { _id: ObjectId(), name: "Physics", code: "PHYS201", teacherId: teachers[1]._id },
  { _id: ObjectId(), name: "Chemistry", code: "CHEM301", teacherId: teachers[2]._id },
  { _id: ObjectId(), name: "Biology", code: "BIO202", teacherId: teachers[3]._id },
  { _id: ObjectId(), name: "English", code: "ENG101", teacherId: teachers[4]._id }
];
db.subjects.insertMany(subjects);

// === Insert Students ===
const students = [
  { _id: ObjectId(), name: "David Lee", email: "david@student.edu", rollNumber: "ST1001", class: "10A", passwordHash: "s1", registeredSubjects: [subjects[0]._id, subjects[1]._id] },
  { _id: ObjectId(), name: "Emma Watson", email: "emma@student.edu", rollNumber: "ST1002", class: "10A", passwordHash: "s2", registeredSubjects: [subjects[0]._id, subjects[2]._id] },
  { _id: ObjectId(), name: "Frank Green", email: "frank@student.edu", rollNumber: "ST1003", class: "10A", passwordHash: "s3", registeredSubjects: [subjects[1]._id] },
  { _id: ObjectId(), name: "Grace Kim", email: "grace@student.edu", rollNumber: "ST1004", class: "10A", passwordHash: "s4", registeredSubjects: [subjects[2]._id, subjects[0]._id] },
  { _id: ObjectId(), name: "Henry Brown", email: "henry@student.edu", rollNumber: "ST1005", class: "10A", passwordHash: "s5", registeredSubjects: [subjects[0]._id, subjects[1]._id, subjects[2]._id] },
  { _id: ObjectId(), name: "Sophia Adams", email: "sophia@student.edu", rollNumber: "ST1006", class: "10B", passwordHash: "s6", registeredSubjects: [subjects[3]._id, subjects[4]._id] }
];
db.students.insertMany(students);

// === Insert Exams with startTime, endTime, status ===
const now = new Date();

const exams = [
  {
    _id: ObjectId(),
    subjectId: subjects[0]._id,
    title: "Math Midterm",
    date: now,
    durationMinutes: 90,
    createdBy: teachers[0]._id,
    isPublished: true,
    startTime: new Date(now.getTime() + 1000 * 60 * 5), // 5 mins from now
    endTime: new Date(now.getTime() + 1000 * 60 * 95),  // +90 mins
    status: "scheduled"
  },
  {
    _id: ObjectId(),
    subjectId: subjects[1]._id,
    title: "Physics Quiz",
    date: now,
    durationMinutes: 60,
    createdBy: teachers[1]._id,
    isPublished: true,
    startTime: new Date(now.getTime() - 1000 * 60 * 30), // started 30 mins ago
    endTime: new Date(now.getTime() + 1000 * 60 * 30),   // ends in 30 mins
    status: "live"
  },
  {
    _id: ObjectId(),
    subjectId: subjects[2]._id,
    title: "Chemistry Finals",
    date: now,
    durationMinutes: 120,
    createdBy: teachers[2]._id,
    isPublished: true,
    startTime: new Date(now.getTime() - 1000 * 60 * 180), // started 3 hrs ago
    endTime: new Date(now.getTime() - 1000 * 60 * 60),    // ended 1 hr ago
    status: "ended"
  },
  {
    _id: ObjectId(),
    subjectId: subjects[3]._id,
    title: "Biology Midterm",
    date: now,
    durationMinutes: 120,
    createdBy: teachers[3]._id,
    isPublished: true,
    startTime: new Date(now.getTime() + 1000 * 60 * 30), // starts in 30 mins
    endTime: new Date(now.getTime() + 1000 * 60 * 150),  // +2 hrs
    status: "scheduled"
  },
  {
    _id: ObjectId(),
    subjectId: subjects[4]._id,
    title: "English Literature Exam",
    date: now,
    durationMinutes: 90,
    createdBy: teachers[4]._id,
    isPublished: true,
    startTime: new Date(now.getTime() - 1000 * 60 * 720), // started 12 hrs ago
    endTime: new Date(now.getTime() - 1000 * 60 * 630),   // ended 10.5 hrs ago
    status: "ended"
  }
];

db.exams.insertMany(exams);

// === Insert Questions for each Exam ===
const questionTypes = ["mcq", "long"];
let questions = [];

exams.forEach((exam, idx) => {
  for (let i = 1; i <= 5; i++) {
    let type = questionTypes[i % 2]; // alternate between mcq and long
    let q = {
      _id: ObjectId(),
      examId: exam._id,
      questionText: `Question ${i} for ${exam.title}`,
      type: type,
      marks: type === "mcq" ? 2 : 5
    };

    if (type === "mcq") {
      q.options = ["Option A", "Option B", "Option C", "Option D"];
      q.correctAnswerIndex = i % 4;
    } else {
      q.expectedKeywords = ["keyword1", "keyword2"];
    }

    questions.push(q);
  }
});
db.questions.insertMany(questions);

// === Insert Sample Responses for all students ===
let responses = [];

students.forEach((student) => {
  exams.forEach((exam) => {
    let qSubset = questions.filter(q => q.examId.equals(exam._id)).slice(0, 2); // 2 questions per exam

    qSubset.forEach((q, idx) => {
      let response = {
        _id: ObjectId(),
        studentId: student._id,
        examId: exam._id,
        questionId: q._id,
        timestamp: new Date()
      };

      if (q.type === "mcq") {
        response.selectedAnswerIndex = (idx + 1) % 4;
        response.marksAwarded = response.selectedAnswerIndex === q.correctAnswerIndex ? q.marks : 0;
      } else {
        response.longAnswerText = "Sample answer text for long question.";
        response.marksAwarded = 3;
        response.gradedBy = exam.createdBy;
        response.gradedAt = new Date();
      }

      responses.push(response);
    });
  });
});

db.responses.insertMany(responses);

// === Compute and Insert Sample Results ===
students.forEach((student) => {
  exams.forEach((exam) => {
    let studentResponses = responses.filter(r => r.studentId.equals(student._id) && r.examId.equals(exam._id));
    if (studentResponses.length === 0) return;

    const total = studentResponses.reduce((sum, r) => sum + r.marksAwarded, 0);
    const maxMarks = studentResponses.reduce((sum, r) => {
      const q = questions.find(q => q._id.equals(r.questionId));
      return sum + (q ? q.marks : 0);
    }, 0);

    db.results.insertOne({
      studentId: student._id,
      examId: exam._id,
      marksObtained: total,
      totalMarks: maxMarks,
      percentage: (total / maxMarks) * 100,
      grade: total > 0.8 * maxMarks ? "A" : total > 0.6 * maxMarks ? "B" : "C",
      computedAt: new Date()
    });
  });
});
