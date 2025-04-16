db = db.getSiblingDB("university");

// Drop existing data
db.students.drop();
db.teachers.drop();
db.subjects.drop();
db.exams.drop();
db.questions.drop();
db.responses.drop();
db.results.drop();
db.classes.drop();  // Added class collection

// === Insert Teachers ===
const teachers = [
  { _id: "teacher1", name: "Alice Smith", email: "alice@university.edu", passwordHash: "hash1" },
  { _id: "teacher2", name: "Bob Johnson", email: "bob@university.edu", passwordHash: "hash2" },
  { _id: "teacher3", name: "Carol White", email: "carol@university.edu", passwordHash: "hash3" },
  { _id: "teacher4", name: "David Brown", email: "david@university.edu", passwordHash: "hash4" },
  { _id: "teacher5", name: "Eva Green", email: "eva@university.edu", passwordHash: "hash5" }
];
db.teachers.insertMany(teachers);

// === Insert Subjects ===
const subjects = [
  { _id: "math1", name: "Mathematics", code: "MATH101", teacherIds: ["teacher1", "teacher2"] },
  { _id: "phys1", name: "Physics", code: "PHYS201", teacherIds: ["teacher2", "teacher3"] },
  { _id: "chem1", name: "Chemistry", code: "CHEM301", teacherIds: ["teacher3", "teacher4"] },
  { _id: "bio1",  name: "Biology", code: "BIO202", teacherIds: ["teacher4", "teacher5"] },
  { _id: "eng1",  name: "English", code: "ENG101", teacherIds: ["teacher5", "teacher1"] }
];
db.subjects.insertMany(subjects);

// === Insert Classes ===
const classes = [
  { _id: "10A", name: "Class 10A", subjectIds: ["math1", "phys1", "chem1"] },
  { _id: "10B", name: "Class 10B", subjectIds: ["math1", "bio1", "eng1"] }
];
db.classes.insertMany(classes);

// === Insert Students ===
const students = [
  { _id: "student1", name: "David Lee", email: "david@student.edu", rollNumber: "ST1001", classId: "10A", passwordHash: "s1" },
  { _id: "student2", name: "Emma Watson", email: "emma@student.edu", rollNumber: "ST1002", classId: "10A", passwordHash: "s2" },
  { _id: "student3", name: "Frank Green", email: "frank@student.edu", rollNumber: "ST1003", classId: "10A", passwordHash: "s3" },
  { _id: "student4", name: "Grace Kim", email: "grace@student.edu", rollNumber: "ST1004", classId: "10A", passwordHash: "s4" },
  { _id: "student5", name: "Henry Brown", email: "henry@student.edu", rollNumber: "ST1005", classId: "10A", passwordHash: "s5" },
  { _id: "student6", name: "Sophia Adams", email: "sophia@student.edu", rollNumber: "ST1006", classId: "10B", passwordHash: "s6" }
];
db.students.insertMany(students);

// === Insert Exams ===
const now = new Date();

const exams = [
  {
    _id: "math1-midterm",
    subjectId: "math1",
    title: "Math Midterm",
    date: now,
    durationMinutes: 90,
    createdBy: "teacher1",
    isPublished: true,
    startTime: new Date(now.getTime() + 1000 * 60 * 5),
    endTime: new Date(now.getTime() + 1000 * 60 * 95),
    status: "scheduled"
  },
  {
    _id: "phys1-quiz",
    subjectId: "phys1",
    title: "Physics Quiz",
    date: now,
    durationMinutes: 60,
    createdBy: "teacher2",
    isPublished: true,
    startTime: new Date(now.getTime() - 1000 * 60 * 30),
    endTime: new Date(now.getTime() + 1000 * 60 * 30),
    status: "live"
  },
  {
    _id: "chem1-finals",
    subjectId: "chem1",
    title: "Chemistry Finals",
    date: now,
    durationMinutes: 120,
    createdBy: "teacher3",
    isPublished: true,
    startTime: new Date(now.getTime() - 1000 * 60 * 180),
    endTime: new Date(now.getTime() - 1000 * 60 * 60),
    status: "ended"
  },
  {
    _id: "bio1-midterm",
    subjectId: "bio1",
    title: "Biology Midterm",
    date: now,
    durationMinutes: 120,
    createdBy: "teacher4",
    isPublished: true,
    startTime: new Date(now.getTime() + 1000 * 60 * 30),
    endTime: new Date(now.getTime() + 1000 * 60 * 150),
    status: "scheduled"
  },
  {
    _id: "eng1-literature",
    subjectId: "eng1",
    title: "English Literature Exam",
    date: now,
    durationMinutes: 90,
    createdBy: "teacher5",
    isPublished: true,
    startTime: new Date(now.getTime() - 1000 * 60 * 720),
    endTime: new Date(now.getTime() - 1000 * 60 * 630),
    status: "ended"
  }
];

db.exams.insertMany(exams);

// === Insert Questions ===
const questionTypes = ["mcq", "long"];
let questions = [];

exams.forEach((exam, idx) => {
  for (let i = 1; i <= 5; i++) {
    let type = questionTypes[i % 2];
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

// === Insert Responses ===
let responses = [];

students.forEach((student) => {
  const studentClass = db.classes.findOne({ _id: student.classId });
  studentClass.subjectIds.forEach((subjectId) => {
    const relevantExams = db.exams.find({ subjectId: subjectId }).toArray();

    relevantExams.forEach((exam) => {
      let qSubset = questions.filter(q => q.examId === exam._id).slice(0, 2);

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
});
db.responses.insertMany(responses);

// === Insert Results ===
students.forEach((student) => {
  const studentClass = db.classes.findOne({ _id: student.classId });
  studentClass.subjectIds.forEach((subjectId) => {
    const relevantExams = db.exams.find({ subjectId: subjectId }).toArray();

    relevantExams.forEach((exam) => {
      let studentResponses = responses.filter(r => r.studentId === student._id && r.examId === exam._id);
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
});

const mathEndTerm = {
  _id: "math1-endterm",
  subjectId: "math1",
  title: "Math End Term",
  date: now,
  durationMinutes: 120,
  createdBy: "teacher1",
  isPublished: true,
  startTime: new Date(now.getTime() - 1000 * 60 * 120),  // started 2 hours ago
  endTime: new Date(now.getTime() - 1000 * 60 * 60),     // ended 1 hour ago
  status: "evaluation"
};
db.exams.insertOne(mathEndTerm);

const mathEndTermQuestions = [];

for (let i = 1; i <= 3; i++) {
  const type = i % 2 === 0 ? "long" : "mcq";
  const question = {
    _id: ObjectId(),
    examId: "math1-endterm",
    questionText: `Math End Term Q${i}`,
    type: type,
    marks: type === "mcq" ? 2 : 5
  };

  if (type === "mcq") {
    question.options = ["A", "B", "C", "D"];
    question.correctAnswerIndex = i % 4;
  } else {
    question.expectedKeywords = ["integration", "limits"];
  }

  mathEndTermQuestions.push(question);
}
db.questions.insertMany(mathEndTermQuestions);

students.forEach((student) => {
  mathEndTermQuestions.forEach((q, idx) => {
    const resp = {
      _id: ObjectId(),
      studentId: student._id,
      examId: "math1-endterm",
      questionId: q._id,
      timestamp: new Date()
    };

    if (q.type === "mcq") {
      resp.selectedAnswerIndex = (idx + 1) % 4;
      resp.marksAwarded = resp.selectedAnswerIndex === q.correctAnswerIndex ? q.marks : 0;
    } else {
      resp.longAnswerText = `Answer with math explanation by ${student.name}`;
      resp.marksAwarded = null;  // not graded yet
    }

    db.responses.insertOne(resp);
  });
});
