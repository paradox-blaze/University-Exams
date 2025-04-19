import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:80/student"  # Reverse proxy to student service

st.set_page_config(page_title="Student Portal", page_icon="🎓", layout="wide")
st.title("🎓 Student Portal")

# ==============================
# Session State
# ==============================

if "student_id" not in st.session_state:
    st.session_state.student_id = "student1"

# Sidebar Navigation
page = st.sidebar.selectbox("Navigate", ["🏠 Home", "📝 Attempt Exam", "📄 My Results"])

# ==============================
# Helpers
# ==============================

def format_datetime(dt_str):
    try:
        return datetime.fromisoformat(dt_str).strftime("%Y-%m-%d %H:%M")
    except:
        return dt_str

def fetch_data(url, params=None):
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Failed to fetch from {url}")
            return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# ==============================
# 🏠 HOME PAGE
# ==============================

if page == "🏠 Home":
    st.header("Welcome!")

    student = fetch_data(f"{API_URL}/students/{st.session_state.student_id}")
    if student:
        st.subheader(f"👤 {student['name']} ({student['rollNumber']})")
        st.write(f"📧 Email: {student['email']}")
        st.write(f"🏫 Class: {student['class']}")
    else:
        st.error("Student profile not found.")

# ==============================
# 📝 ATTEMPT EXAM
# ==============================

elif page == "📝 Attempt Exam":
    st.header("📝 Live Exams")

    exams = fetch_data(f"{API_URL}/exams", params={"student_id": st.session_state.student_id})
    
    if not exams:
        st.info("No live exams available.")
    else:
        for exam in exams:
            with st.expander(f"{exam['title']} ({exam['exam_id']})"):
                st.write(f"📅 Start: {format_datetime(exam['startTime'])}")
                st.write(f"🕒 End: {format_datetime(exam['endTime'])}")
                st.write(f"⏱ Duration: {exam['durationMinutes']} min")

                # Load questions
                questions = fetch_data(f"{API_URL}/responses", params={
                    "student_id": st.session_state.student_id,
                    "exam_id": exam["exam_id"]
                })

                attempted_ids = [q["questionId"] for q in questions] if questions else []

                exam_questions = fetch_data(f"{API_URL}/exams/{exam['exam_id']}/questions") or []

                for q in exam_questions:
                    if q["questionId"] in attempted_ids:
                        st.success(f"✅ Already answered: {q['questionText']}")
                        continue

                    with st.form(key=f"{q['questionId']}"):
                        st.markdown(f"**Q: {q['questionText']}**")
                        st.markdown(f"_({q['marks']} marks)_")

                        if q["questionType"] == "mcq":
                            options = q.get("options", [])
                            selected = st.radio("Choose your answer:", options, key=f"radio_{q['questionId']}")
                            if st.form_submit_button("Submit"):
                                index = options.index(selected)
                                res = requests.post(
                                    f"{API_URL}/exams/{exam['exam_id']}/questions/{q['questionId']}/response",
                                    params={"student_id": st.session_state.student_id},
                                    json={
                                        "answerText": "",
                                        "marksObtained": 0,  # Will be auto-computed in backend
                                        "questionType": "mcq",
                                        "selectedAnswerIndex": index
                                    }
                                )
                                if res.status_code == 200:
                                    st.success("Answer submitted!")
                                    st.rerun()
                                else:
                                    st.error("Submission failed.")

                        elif q["questionType"] == "long":
                            answer_text = st.text_area("Your answer:")
                            if st.form_submit_button("Submit"):
                                res = requests.post(
                                    f"{API_URL}/exams/{exam['exam_id']}/questions/{q['questionId']}/response",
                                    params={"student_id": st.session_state.student_id},
                                    json={
                                        "answerText": answer_text,
                                        "questionType": "long"
                                    }
                                )
                                if res.status_code == 200:
                                    st.success("Answer submitted!")
                                    st.rerun()
                                else:
                                    st.error("Submission failed.")

# ==============================
# 📄 MY RESULTS
# ==============================

elif page == "📄 My Results":
    st.header("📊 My Results")

    results = fetch_data(f"{API_URL}/results", params={"student_id": st.session_state.student_id})
    if not results:
        st.info("No results available.")
    else:
        for r in results:
            with st.expander(f"📘 Exam: {r['examId']}"):
                st.write(f"**Marks Obtained:** {r['marksObtained']} / {r['totalMarks']}")
                st.write(f"**Percentage:** {r['percentage']:.2f}%")
                st.write(f"**Grade:** {r['grade']}")
                if r.get("computedAt"):
                    st.write(f"🕓 Computed: {format_datetime(r['computedAt'])}")

                # View responses for this exam
                responses = fetch_data(f"{API_URL}/responses", params={
                    "student_id": st.session_state.student_id,
                    "exam_id": r["examId"]
                })

                if responses:
                    st.markdown("#### 📝 Responses")
                    for resp in responses:
                        st.markdown(f"**Q:** {resp['questionText']}")
                        if resp["type"] == "MCQ":
                            st.markdown(f"- Selected: {resp['selectedOption']}")
                            st.markdown(f"- Correct: {resp['correctOption']}")
                        else:
                            st.markdown(f"- Answer: {resp['studentAnswer']}")
                            st.markdown(f"- Graded By: {resp.get('gradedBy', '-')}")
                            if resp.get("gradedAt"):
                                st.markdown(f"- Graded At: {format_datetime(resp['gradedAt'])}")

                        st.markdown(f"**Marks:** {resp['marksAwarded']} / {resp['totalMarks']}")
                        st.markdown("---")

# Sidebar Footer
st.sidebar.markdown("---")
st.sidebar.info(f"Student ID: `{st.session_state.student_id}`")
