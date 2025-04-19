
# 🎓 University Management System (Full Stack)

This project is a modular university portal built using microservices. Each functionality—user management, exams, classes, responses, evaluation, requests, and stories—is isolated in its own service to ensure separation of concerns and scalability.
In total, the system runs across 14 Docker containers, including services, databases, frontends, and a reverse proxy.

---

## 🧰 Tech Stack

- **Frontend**: Streamlit (for Admin, Teacher, and Student portals)
- **Backend**: Python with FastAPI and Flask microservices
- **Database**:
  - MongoDB for all academic and story-related data
  - MySQL (via SQLAlchemy) for structured student request system
- **API Gateway / Reverse Proxy**: Nginx
- **Containerization**: Docker + Docker Compose

---

## 🗂 Services

### 1. User Service (`/user/`)
Built with FastAPI + MongoDB. Handles:
- CRUD for students and teachers
- Password hashing
- Lookup by ID
- Authentication endpoint

### 2. Classes Service (`/classes/`)
FastAPI + MongoDB. Handles:
- Class creation
- Subject creation and assignment
- Subject-teacher mapping
- Fetch subjects by teacher

### 3. Exam Service (`/exam/`)
FastAPI + MongoDB. Handles:
- Exam creation (draft/live)
- Publishing
- Fetching exams by student/teacher
- Result computation

### 4. Questions Service (`/questions/`)
FastAPI + MongoDB. Handles:
- Adding questions (MCQ or long)
- Viewing and deleting
- Linked to `examId`

### 5. Response Service (`/response/`)
FastAPI + MongoDB. Handles:
- Submitting exam responses
- Fetching and evaluating responses
- Grading
- Finalizing results per student

### 6. Stories Service (`/stories/`)
Flask + MongoDB. Handles:
- Creating, viewing, and deleting stories
- Used for announcements and motivational pieces

### 7. Requests Service (`/requests/`)
Flask + SQLAlchemy + MySQL. Handles:
- Student-submitted requests (leave, event participation, etc.)
- Admin approval and comments
- View by user or all requests

### 8. Auth Service (`/auth/`)
FastAPI + MongoDB. Centralized authentication:
- Admin: hardcoded
- Student/Teacher: pulls from student/teacher collection
- Returns user info on success

---

## 🔄 Reverse Proxy

All services are unified under `nginx`, which forwards traffic using location prefixes:

- `/user/` → `user-service:8000`
- `/classes/` → `classes-service:8001`
- `/exam/` → `exam-service:8002`
- `/questions/` → `questions-service:8003`
- `/response/` → `response-service:8004`
- `/stories/` → `stories-service:5000`
- `/requests/` → `requests-service:5001`
- `/auth/` → `auth-service:8005`

This makes internal routing seamless and accessible to frontend apps via a common `API_URL`.

---

## 🖥 Frontends

### Admin Portal
- Manage students, teachers, subjects, classes
- Assign teachers to subjects
- View and moderate requests
- Create/delete users

### Teacher Portal
- View assigned subjects
- Create exams, add questions
- Grade long answers
- Finalize and publish results

### Student Portal
- Attempt live exams
- View results
- Submit/view personal requests
- Read motivational stories

---

## 🚀 Running the Project

```docker-compose build
docker-compose up```

Access:

- Admin portal: `localhost:8501`
- Teacher portal: `localhost:8502`
- Student portal: `localhost:8503`

Nginx API gateway is available at `localhost` (port 80)

---

## 👤 Logins

- Admin:
  - Username: `admin`
  - Password: `password`

- Students/Teachers: Use records from MongoDB `students` or `teachers` collection.

---

## 📁 Directory Structure

- `services/`
  - `user-service/`
  - `classes-service/`
  - `exam-service/`
  - `questions-service/`
  - `response-service/`
  - `stories-service/`
  - `requests-service/`
  - `auth-service/`
- `nginx/`
  - `default.conf`
- `frontends/`
  - `admin/`
  - `teacher/`
  - `student/`
- `docker-compose.yml`
- `README.md`

---

