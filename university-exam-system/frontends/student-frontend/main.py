import streamlit as st
import requests
from datetime import datetime
import time

API_URL = "http://nginx/"  # Reverse proxy to student service

st.set_page_config(page_title="Student Portal", page_icon="🎓", layout="wide")
st.title("🎓 Student Portal")

# ==============================
# Session State
# ==============================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.student_id = None
    st.session_state.student_name = None

if not st.session_state.logged_in:
    st.subheader("🔐 Student Login")

    username = st.text_input("Username (e.g. student1)")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            res = requests.post(
                f"{API_URL}/auth/login",
                json={"username": username, "password": password, "role": "student"}
            )
            if res.status_code == 200:
                user = res.json()
                st.session_state.logged_in = True
                st.session_state.student_id = user["id"]
                st.session_state.student_name = user["name"]
                st.success(f"Welcome {user['name']}!")
                st.rerun()
            else:
                st.error(res.json().get("detail", "Login failed"))
        except Exception as e:
            st.error(f"Login error: {e}")

    st.stop()

# Sidebar Navigation
page = st.sidebar.selectbox("Navigate", ["🏠 Home", "📝 Attempt Exam", "📄 My Results", "📬 My Requests"])

if st.session_state.logged_in:
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.student_id = None
        st.session_state.student_name = None
        st.experimental_rerun()

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

    student = fetch_data(f"{API_URL}/user/students/{st.session_state.student_id}")
    if student:
        st.subheader(f"👤 {student['name']} ({student['rollNumber']})")
        st.write(f"📧 Email: {student['email']}")
        st.write(f"🏫 Class: {student['classId']}")
    else:
        st.error("Student profile not found.")

    st.markdown("---")
    st.subheader("📚 Stories")

    # Fetch stories from the story service
    try:
        res = requests.get(f"{API_URL}/stories/stories")  # or your actual story service URL
        if res.status_code == 200:
            stories = res.json()
            if stories:
                display_area = st.empty()
                idx = 0
                # Cycle through the stories
                while True:
                    story = stories[idx]
                    with display_area.container():
                        st.markdown(f"### ✨ {story.get('title', 'Untitled')}")
                        st.write(story.get('content', 'No content provided.'))

                    time.sleep(5)  # Wait 5 seconds before showing the next one
                    idx = (idx + 1) % len(stories)
            else:
                st.info("No stories available.")
        else:
            st.error("Failed to fetch stories.")
    except Exception as e:
        st.error(f"Error fetching stories: {e}")
    

# ==============================
# 📝 ATTEMPT EXAM
# ==============================

elif page == "📝 Attempt Exam":
    st.header("📝 Live Exams")

    exams = fetch_data(f"{API_URL}/exam/exams/by-student", params={"student_id": st.session_state.student_id})
    
    if not exams:
        st.info("No live exams available.")
    else:
        for exam in exams:
            print(exam)
            with st.expander(f"{exam['title']} ({exam['exam_id']})"):
                st.write(f"📅 Start: {format_datetime(exam['startTime'])}")
                st.write(f"🕒 End: {format_datetime(exam['endTime'])}")
                st.write(f"⏱ Duration: {exam['durationMinutes']} min")

                # Load attempted responses
                responses = fetch_data(f"{API_URL}/response/responses", params={
                    "student_id": st.session_state.student_id,
                    "exam_id": exam["exam_id"]
                }) or []

                attempted_ids = [r["id"] for r in responses]
                exam_questions = fetch_data(f"{API_URL}/exam/exams/{exam['exam_id']}/questions") or []

                if len(attempted_ids) == len(exam_questions):
                    st.success("✅ Exam Attempted Successfully!")
                    continue

                for q in exam_questions:
                    if q["id"] in attempted_ids:
                        st.success(f"✅ Already answered: {q['questionText']}")
                        continue

                    with st.form(key=f"{q['id']}"):
                        st.markdown(f"**Q: {q['questionText']}**")
                        st.markdown(f"_({q['marks']} marks)_")

                        if q["type"] == "mcq":
                            options = q.get("options", [])
                            selected = st.radio("Choose your answer:", options, key=f"radio_{q['id']}")
                            submitted = st.form_submit_button("Submit")
                            if submitted:
                                try:
                                    index = options.index(selected)
                                    res = requests.post(
                                        f"{API_URL}/exam/exams/{exam['exam_id']}/questions/{q['id']}/response",
                                        params={"student_id": st.session_state.student_id},
                                        json={
                                            "marksObtained": index,  # misuse field to send index
                                            "type": "mcq"
                                        }
                                    )
                                    if res.status_code == 200:
                                        st.success("Answer submitted!")
                                        st.rerun()
                                    else:
                                        st.error(f"Submission failed: {res.text}")
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        elif q["type"] == "long":
                            answer_text = st.text_area("Your answer:", key=f"long_{q['id']}")
                            submitted = st.form_submit_button("Submit")
                            if submitted:
                                res = requests.post(
                                    f"{API_URL}/exam/exams/{exam['exam_id']}/questions/{q['id']}/response",
                                    params={"student_id": st.session_state.student_id},
                                    json={
                                        "longAnswerText": answer_text,
                                        "type": "long"
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

    results = fetch_data(f"{API_URL}/exam/results", params={"student_id": st.session_state.student_id})
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
                responses = fetch_data(f"{API_URL}/response/responses", params={
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

# 8. My Requests Section
elif page == "📬 My Requests":
    st.subheader("📬 Your Requests")

    REQUESTS_API = f"{API_URL}/requests/requests"

    # === Fetch requests made by current student ===
    try:
        req_res = requests.get(f"{REQUESTS_API}/{st.session_state.student_id}")
        if req_res.status_code == 200:
            student_requests = req_res.json()
            if not student_requests:
                st.info("You haven't submitted any requests yet.")
            else:
                for req in student_requests:
                    with st.expander(f"📌 {req['title']} (Status: {req['status'].capitalize()})"):
                        st.write(f"📂 Category: {req['category']}")
                        st.write(f"📝 Description:\n\n{req['description']}")
                        st.write(f"📅 Created At: {req.get('created_at', 'N/A')}")
                        if req.get("admin_comment"):
                            st.write(f"💬 Admin Comment: {req['admin_comment']}")
        else:
            st.error("Failed to load your requests.")
    except Exception as e:
        st.error(f"Error fetching your requests: {e}")

    st.markdown("---")
    st.subheader("🆕 Submit New Request")

    with st.form("request_form"):
        req_title = st.text_input("Request Title")
        req_desc = st.text_area("Description")
        req_cat = st.selectbox("Category", ["Leave", "Event", "Facility", "Other"])

        submitted = st.form_submit_button("📤 Submit Request")
        if submitted:
            if req_title and req_desc and req_cat:
                payload = {
                    "title": req_title,
                    "description": req_desc,
                    "category": req_cat,
                    "requested_by": st.session_state.student_id
                }
                try:
                    res = requests.post(f"{REQUESTS_API}", json=payload)
                    if res.status_code == 201:
                        st.success("Request submitted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to submit request.")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please fill in all fields.")

# Sidebar Footer
st.sidebar.markdown("---")
st.sidebar.info(f"Student ID: `{st.session_state.student_id}`")
