import streamlit as st
import requests
from datetime import datetime
import pandas as pd

API_URL = "http://localhost:80/"

st.set_page_config(page_title="Teacher Portal", page_icon="👩‍🏫", layout="wide")
st.title("👩‍🏫 Teacher Portal")

# Initialize session state
st.session_state.setdefault("teacher_id", "teacher1")

# Sidebar navigation
page = st.sidebar.selectbox("Choose Section", [
    "🏠 Home",
    "📝 Create Exam",
    "❓ Manage Questions",
    "📊 Grade Responses"
])

# ===========================
# UTILITIES
# ===========================

def format_datetime(dt_str):
    return datetime.fromisoformat(dt_str).strftime("%Y-%m-%d %H:%M")

def get_teacher_name_by_id(teacher_id):
    try:
        res = requests.get(f"{API_URL}/teacher/get_name", params={"id": teacher_id})
        if res.status_code == 200:
            return res.json().get("teacher_name", "Unknown Teacher")
    except Exception:
        pass
    return "Unknown Teacher"

def fetch_data(url, params=None):
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Error fetching data from {url}: {e}")
    return None

def get_question_text(question_id):
    try:
        # Call the API
        res = fetch_data(f"{API_URL}/teacher/question/get", params={"id": question_id})

        # Ensure the response contains the questionText
        if res and "questionText" in res:
            return res["questionText"]
        else:
            print("No 'questionText' found in response.")
            return "[Question not found]"

    except Exception as e:
        print(f"Error fetching question: {e}")
        return "[Error fetching question]"

# ===========================
# HOME PAGE
# ===========================

if page == "🏠 Home":
    st.header("🏠 My Subjects")
    subjects = fetch_data(f"{API_URL}/teacher/subjects", params={"teacher_id": st.session_state.teacher_id})

    if not subjects:
        st.info("You are not assigned to any subjects.")
    else:
        for subject in subjects:
            subject_name = subject['name']
            subject_code = subject['code']
            teacher_names = [get_teacher_name_by_id(tid) for tid in subject['teacherIds']]
            label = f"{subject_name} ({subject_code}) - Teachers: {', '.join(teacher_names)}"
            if st.button(label, key=f"subject_{subject['id']}"):
                st.session_state.selected_subject = subject
                st.session_state.pop("selected_class", None)
                st.rerun()

# ===========================
# SUBJECT DETAIL PAGE
# ===========================

if "selected_subject" in st.session_state and page == "🏠 Home" and "selected_class" not in st.session_state:
    subject = st.session_state.selected_subject
    st.header(f"📘 {subject['name']} ({subject['code']})")

    # ===== Exams Section =====
    st.subheader("🧾 Exams")
    exams = fetch_data(f"{API_URL}/teacher/exams", params={"subject_id": subject['id']})
    st.button("➕ Create New Exam", key="create_exam_btn")

    if not exams:
        st.info("No exams yet.")
    else:
        for exam in exams:
            with st.expander(f"{exam['title']} ({exam['status'].upper()})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Start:** {format_datetime(exam['startTime'])}")
                    st.write(f"**End:** {format_datetime(exam['endTime'])}")
                with col2:
                    st.write(f"**Status:** {exam['status'].capitalize()}")
                    st.write(f"**Published:** {'Yes' if exam['isPublished'] else 'No'}")

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.button("✏️ Evaluate", key=f"eval_{exam['id']}", disabled=exam["status"] != "ended")
                with c2:
                    st.button("♻️ Re-evaluate", key=f"reval_{exam['id']}", disabled=exam["status"] != "ended")
                with c3:
                    st.button("❌ Delete", key=f"delete_{exam['id']}", disabled=exam["status"] == "live")
                with c4:
                    st.button("📄 Questions", key=f"view_questions_{exam['id']}")

    # ===== Classes Section =====
    # ===== Classes Section =====
    st.subheader("🏫 Classes Taking This Subject")
    classes = fetch_data(f"{API_URL}/teacher/subject-classes", params={"subject_id": subject['id']})
    if not classes:
        st.info("No classes found.")
    else:
        for cls in classes:
            # Extract relevant class details
            class_id = cls.get('id', 'N/A')
            class_name = cls.get('name', 'No Name Available')
            subject_ids = cls.get('subjectIds', [])
            
            # Display class details in a structured format
            st.markdown(f"### Class: {class_name} ({class_id})")
            st.markdown(f"- **Class ID**: {class_id}")
            st.markdown(f"- **Subjects**: {', '.join(subject_ids) if subject_ids else 'No subjects available'}")
            
            # Button for selecting the class
            if st.button(f"👥 Select Class: {class_name}", key=f"class_{class_id}"):
                st.session_state.selected_class = cls
                st.rerun()



# ===========================
# CLASS DETAIL PAGE
# ===========================

if "selected_subject" in st.session_state and "selected_class" in st.session_state and page == "🏠 Home":
    subject = st.session_state.selected_subject
    class_obj = st.session_state.selected_class  # The class object (dictionary)
    
    # Extract class details from the object
    class_id = class_obj.get('id', 'N/A')
    class_name = class_obj.get('name', 'No Name Available')
    
    # Display header for selected class and subject
    st.header(f"👥 {class_name} ({class_id}) - {subject['name']}")

    # Fetching students data
    students = fetch_data(f"{API_URL}/student/students/by-class", params={"class_id": class_id})

    if not students:
        st.info("No students found.")
    else:
        st.subheader("🎓 Student Results")
        
        for student in students:
            # Fetching individual student results using student_id and subject_id
            student_results = fetch_data(f"{API_URL}/student/results", params={"student_id": student['id'], "subject_id": subject['id']}) or []

            with st.expander(f"👤 {student['name']} ({student['rollNumber']})"):
                if student_results:
                    for r in student_results:
                        st.markdown(f"### 📘 Exam: {r['examId']}")
                        st.markdown(
                            f"- **Marks Obtained:** {r['marksObtained']} / {r['totalMarks']}\n"
                            f"- **Percentage:** {r['percentage']:.2f}%\n"
                            f"- **Grade:** {r['grade']}"
                        )

                        button_key = f"view_responses_{student['id']}_{r['examId']}"

                        if st.button("📄 View Responses", key=button_key):
                            responses = fetch_data(
                                f"{API_URL}/student/responses",
                                params={"student_id": student['id'], "exam_id": r['examId']}
                            )

                            if responses:
                                st.markdown("#### 📝 Responses")
                                for q in responses:
                                    question_text = get_question_text(q.get("questionId"))
                                    st.markdown(f"**Q:** {question_text}")

                                    if q["type"] == "MCQ":
                                        st.markdown(f"- **Selected Option:** {q.get('selectedOption', '-')}")
                                        st.markdown(f"- **Correct Option:** {q.get('correctOption', '-')}")
                                    elif q["type"] == "Long Answer":
                                        st.markdown(f"- **Answer:** {q.get('studentAnswer', '-')}")
                                        st.markdown(f"- **Graded By:** {q.get('gradedBy', '-')}")
                                        if q.get("gradedAt"):
                                            st.markdown(f"- **Graded At:** {format_datetime(q['gradedAt'])}")
                                    
                                    st.markdown(f"- **Marks:** {q.get('marksAwarded', 0)} / {q.get('totalMarks', 0)}")
                                    st.markdown("---")
                            else:
                                st.warning("No responses found.")
                else:
                    st.write("❌ No results yet.")




# ===========================
# SIDEBAR FOOTER
# ===========================

st.sidebar.markdown("---")
st.sidebar.info(f"Teacher ID: {st.session_state.teacher_id}")
