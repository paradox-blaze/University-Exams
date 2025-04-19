import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import time

API_URL = "http://localhost:80/"

st.set_page_config(page_title="Teacher Portal", page_icon="👩‍🏫", layout="wide")
st.title("👩‍🏫 Teacher Portal")

# Initialize session state variables
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = "teacher2"
if "exam_created" not in st.session_state:
    st.session_state.exam_created = False
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_view" not in st.session_state:
    st.session_state.current_view = "home"

# Sidebar navigation
page = st.sidebar.selectbox("Choose Section", [
    "🏠 Home",
])

# ===========================
# UTILITIES
# ===========================

def format_datetime(dt_str):
    return datetime.fromisoformat(dt_str).strftime("%Y-%m-%d %H:%M")

def get_teacher_name_by_id(teacher_id):
    try:
        res = requests.get(f"{API_URL}/user/get_name", params={"id": teacher_id})
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
        res = fetch_data(f"{API_URL}/questions/question/get", params={"id": question_id})

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
# STATE MANAGEMENT FUNCTIONS
# ===========================

def set_view(view_name):
    st.session_state.current_view = view_name

def show_create_exam():
    st.session_state.current_view = "create_exam"
    st.session_state.exam_created = False
    st.session_state.questions = []
    if "exam_details" in st.session_state:
        del st.session_state.exam_details

# ===========================
# CREATE EXAM AND ADD QUESTIONS
# ===========================

def get_exam_id():
    """Helper function to find the exam ID regardless of how it's stored in session state"""
    # Try different possible locations
    if "exam_details" in st.session_state:
        exam = st.session_state.exam_details
        if "examId" in exam:
            return exam["examId"]
        elif "id" in exam:
            return exam["id"]
        
        # Check for nested structures
        for key, value in exam.items():
            if isinstance(value, dict) and "id" in value:
                return value["id"]
    
    # Fallback to complete_exam
    if "complete_exam" in st.session_state:
        return st.session_state.complete_exam.get("examId", "unknown_id")
    
    # Last resort
    return "unknown_id"

def create_exam():
    st.title("Create New Exam")

    # Ensure the selected subject exists in session state
    if "selected_subject" not in st.session_state:
        st.warning("Please select a subject first.")
        return

    # Get the selected subject from session state
    subject = st.session_state.selected_subject
    st.subheader(f"Creating Exam for: {subject['name']} ({subject['code']})")

    # Form for creating an exam
    if not st.session_state.exam_created:
        with st.form(key="exam_form"):
            exam_title = st.text_input("Exam Title")
            
            exam_start_date = st.date_input("Start Date", value=datetime.now().date())
            exam_start_time = st.time_input("Start Time", value=datetime.now().time())
            
            # Combine date and time
            exam_start = datetime.combine(exam_start_date, exam_start_time)
            
            exam_duration = st.number_input("Duration (Minutes)", min_value=1, value=60, step=1)
            
            submit_button = st.form_submit_button("Create Exam")
            
            if submit_button:
                if not exam_title:
                    st.error("Please provide an exam title.")
                else:
                    # Calculate end time
                    exam_end = exam_start + timedelta(minutes=exam_duration)
                    
                    # Prepare exam data
                    exam_data = {
                        "title": exam_title,
                        "subjectId": subject["id"],
                        "startTime": exam_start.isoformat(),
                        "endTime": exam_end.isoformat(),
                        "durationMinutes": exam_duration,
                        "createdBy": st.session_state.teacher_id,
                        "isPublished": False,
                        "status": "draft"
                    }
                    
                    try:
                        # Send the request to create the exam
                        res = requests.post(f"{API_URL}/exam/exams/create", json=exam_data)
                        
                        if res.status_code == 200:
                            # Save the created exam details in session state
                            response_data = res.json()
                            
                            # Store both the API response and the complete exam details
                            st.session_state.exam_response = response_data
                            st.session_state.exam_details = {
                                "examId": response_data["examId"],
                                "title": exam_title,  # Store the title from the form
                                "subjectId": subject["id"],
                                "startTime": exam_start.isoformat(),
                                "endTime": exam_end.isoformat(),
                                "durationMinutes": exam_duration,
                                "status": "draft"
                            }
                            
                            st.session_state.exam_created = True
                            st.success("Exam created successfully!")
                            # Use rerun to refresh the page with the updated state
                            st.rerun()
                        else:
                            st.error(f"Failed to create exam. Error: {res.status_code}, Message: {res.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error while creating exam: {e}")
    else:
        # If exam is created, show the add questions form
        manage_questions_form()

def manage_questions_form():
    st.subheader("Manage Questions")

    exam_id = get_exam_id()
    exam = st.session_state.get("exam_details", {})
    exam_status = exam.get("status", "draft").lower()

    st.info(f"Exam: {exam.get('title', 'Unknown Exam')} | Status: {exam_status.upper()}")

    # === Fetch questions from backend ===
    questions = fetch_data(f"{API_URL}/questions/exams/{exam_id}/questions") or []

    if questions:
        st.subheader("📚 Questions")
        for idx, q in enumerate(questions, 1):
            with st.expander(f"Question {idx}: {q['type']}"):
                st.write(f"**Question:** {q['questionText']}")
                st.write(f"**Marks:** {q['marks']}")
                if q["type"] == "mcq":
                    st.write("**Options:**")
                    for i, opt in enumerate(q.get("options") or []):
                        st.write(f"{i + 1}. {opt}" + (" (Correct)" if i == q.get("correctAnswerIndex") else ""))
                else:
                    st.write(f"**Expected Keywords:** {', '.join(q.get('expectedKeywords', []))}")

                if exam_status == "draft":
                    if st.button("❌ Delete Question", key=f"delete_{q['id']}"):
                        try:
                            res = requests.delete(f"{API_URL}/questions/questions/{q['id']}")
                            if res.status_code == 200:
                                st.success("Question deleted successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to delete question.")
                        except Exception as e:
                            st.error(f"Error deleting question: {e}")
    else:
        st.info("No questions added yet.")

    # === Only allow adding questions in draft mode ===
    if exam_status == "draft":
        st.markdown("---")
        st.subheader("➕ Add Questions")

        question_type = st.radio("Question Type", ("MCQ", "Long Form"))

        if question_type == "MCQ":
            with st.form(key="mcq_form"):
                question_text = st.text_area("Question Text")
                options = [st.text_input(f"Option {i + 1}", key=f"{exam_id}_option_{i}") for i in range(4)]
                correct_answer_index = st.number_input("Correct Answer Index (0-3)", 0, 3)
                marks = st.number_input("Marks", min_value=1, value=5, step=1)
                submit_mcq = st.form_submit_button("Add MCQ Question")

                if submit_mcq:
                    if not question_text or not all(options[:2]):
                        st.error("Please provide question text and at least the first two options.")
                    else:
                        question = {
                            "examId": exam_id,
                            "questionText": question_text,
                            "type": "mcq",
                            "options": [opt for opt in options if opt],
                            "correctAnswerIndex": correct_answer_index,
                            "marks": marks
                        }
                        res = requests.post(f"{API_URL}/questions/questions/create", json=question)
                        if res.status_code == 200:
                            st.success("MCQ question added!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add question: {res.status_code}, {res.text}")

        elif question_type == "Long Form":
            with st.form(key="long_form"):
                question_text = st.text_area("Question Text")
                expected_keywords = st.text_input("Expected Keywords (comma-separated)")
                marks = st.number_input("Marks", min_value=1, value=10, step=1)
                submit_longform = st.form_submit_button("Add Long Form Question")

                if submit_longform:
                    if not question_text:
                        st.error("Please provide question text.")
                    else:
                        question = {
                            "examId": exam_id,
                            "questionText": question_text,
                            "type": "long",
                            "expectedKeywords": [k.strip() for k in expected_keywords.split(",")] if expected_keywords else [],
                            "marks": marks
                        }
                        res = requests.post(f"{API_URL}/questions/questions/create", json=question)
                        if res.status_code == 200:
                            st.success("Long-form question added!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add question: {res.status_code}, {res.text}")

    st.markdown("---")

    # === Bottom Button ===
    if exam_status == "draft":
        if st.button("💾 Save Draft"):
            st.success("Draft saved.")
            st.session_state.exam_created = False
            st.session_state.pop("exam_details", None)
            st.session_state.current_view = "home"
            st.rerun()
    else:
        if st.button("← Back"):
            st.session_state.pop("exam_details", None)
            st.session_state.current_view = "home"
            st.rerun()


def evaluate_exam():
    st.title("📝 Evaluate Exam")

    if "exam_details" not in st.session_state:
        st.warning("No exam selected for evaluation.")
        return

    exam = st.session_state.exam_details
    exam_id = exam.get("id") or exam.get("examId")
    st.subheader(f"Evaluating: {exam.get('title')}")

    # Fetch questions
    questions = fetch_data(f"{API_URL}/questions/exams/{exam_id}/questions") or []

    if not questions:
        st.info("No questions found for this exam.")
        return

    for question in questions:
        st.markdown("---")
        st.subheader(f"📖 {question['questionText']} _(Max Marks: {question['marks']})_")

        if question["type"] == "long":
            st.markdown(f"**Expected Keywords:** {', '.join(question.get('expectedKeywords', []))}")

            try:
                res = requests.get(
                    f"{API_URL}/response/exams/question-responses",
                    params={"exam_id": exam_id, "question_id": question["id"]}
                )
                if res.status_code == 200:
                    responses = res.json().get("responses", [])
                else:
                    st.error("Failed to fetch long responses.")
                    continue
            except Exception as e:
                st.error(f"Error fetching long responses: {e}")
                continue

            marks_to_submit = {}
            any_ungraded = False

            for resp in responses:
                marks_existing = resp.get("marksAwarded")

                with st.expander(f"🧑 Student: {resp['studentId']}"):
                    st.write(f"**Answer:** {resp['longAnswerText']}")

                    if marks_existing is not None:
                        st.success(f"Already graded: {marks_existing} / {question['marks']}")
                        st.write(f"**Graded By:** {resp.get('gradedBy', '-')}")
                        if resp.get("gradedAt"):
                            st.write(f"**Graded At:** {format_datetime(resp['gradedAt'])}")
                    else:
                        any_ungraded = True
                        marks_awarded = st.number_input(
                            f"Marks for {resp['studentId']}",
                            min_value=0,
                            max_value=question["marks"],
                            key=f"mark_{resp['responseId']}"
                        )
                        marks_to_submit[resp["responseId"]] = marks_awarded

            if any_ungraded:
                if st.button(f"✅ Submit Marks for '{question['questionText']}'"):
                    success = True
                    for rid, marks in marks_to_submit.items():
                        payload = {
                            "marks": marks,
                            "gradedBy": st.session_state.teacher_id
                        }
                        try:
                            res = requests.post(
                                f"{API_URL}/response/responses/grade",
                                params={"response_id": rid},
                                json=payload
                            )
                            if res.status_code != 200:
                                success = False
                        except Exception as e:
                            st.error(f"Error submitting marks: {e}")
                            success = False

                    if success:
                        st.success("All marks submitted!")
                        st.rerun()
                    else:
                        st.error("Some marks failed to submit.")

        elif question["type"] == "mcq":
            st.write("### 📊 MCQ Responses")
            try:
                res = requests.get(
                    f"{API_URL}/response/exams/question-responses/all",
                    params={"exam_id": exam_id, "question_id": question["id"]}
                )
                if res.status_code == 200:
                    responses = res.json().get("responses", [])
                else:
                    st.error("Failed to fetch MCQ responses.")
                    continue
            except Exception as e:
                st.error(f"Error fetching MCQs: {e}")
                continue

            for resp in responses:
                selected_index = resp.get("selectedAnswerIndex")
                correct_index = question.get("correctAnswerIndex")
                options = question.get("options", [])

                selected_option = options[selected_index] if 0 <= selected_index < len(options) else "Invalid"
                correct_option = options[correct_index] if 0 <= correct_index < len(options) else "Invalid"

                st.markdown(f"""
                - 🧑 **Student:** `{resp['studentId']}`
                - ✅ **Selected Option:** {selected_option}
                - 🎯 **Correct Option:** {correct_option}
                - 🏅 **Marks Awarded:** {resp.get('marksAwarded', 0)} / {question['marks']}
                """)

    st.markdown("## 🧮 Finalize Evaluation")
    if st.button("📊 Compute Final Results"):
        try:
            res = requests.post(
                f"{API_URL}/exam/exams/finalize-results",
                params={"exam_id": exam_id}
            )
            if res.status_code == 200:
                st.success("Results computed successfully!")
                time.sleep(1.5)  # 1.5 second delay
                st.session_state.current_view = "home"
                st.session_state.pop("exam_details", None)
                st.rerun()
            else:
                st.error("Failed to compute results.")
        except Exception as e:
            st.error(f"Error finalizing: {e}")



# ===========================
# ROUTE HANDLING
# ===========================

# Create exam view
if st.session_state.current_view == "create_exam":
    create_exam()

elif st.session_state.current_view == "evaluate_exam":
    evaluate_exam()

elif "current_view" in st.session_state and st.session_state.current_view == "add_questions":
    manage_questions_form()  # Call the function that displays the question form
    
# Home view with subject selection
elif page == "🏠 Home" and st.session_state.current_view == "home":
    if "selected_subject" not in st.session_state:
        st.header("🏠 My Subjects")
        subjects = fetch_data(f"{API_URL}/classes/subjects-by-teacher", params={"teacher_id": st.session_state.teacher_id})

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
    elif "selected_class" not in st.session_state:
        # Subject detail view
        subject = st.session_state.selected_subject
        st.header(f"📘 {subject['name']} ({subject['code']})")

        # Back button
        if st.button("← Back to Subjects"):
            st.session_state.pop("selected_subject", None)
            st.rerun()

        # Exams Section
        st.subheader("🧾 Exams")
        exams = fetch_data(f"{API_URL}/exam/exams/by-subject", params={"subject_id": subject['id']})
        
        if st.button("➕ Create New Exam", key="create_exam_btn"):
            show_create_exam()
            st.rerun()

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

                    # --- Evaluate Button: Only active when status is 'evaluation' ---
                    with c1:
                        if exam["status"] == "evaluation":
                            if st.button("✏️ Evaluate", key=f"eval_{exam['id']}"):
                                st.session_state.current_view = "evaluate_exam"
                                st.session_state.exam_details = exam
                                st.rerun()
                        else:
                            st.button("✏️ Evaluate", key=f"eval_{exam['id']}", disabled=True)

                    # --- Publish / Unpublish ---
                    with c2:
                        if exam["status"] == "draft":
                            if not exam["isPublished"]:
                                if st.button("🚀 Publish", key=f"publish_{exam['id']}"):
                                    try:
                                        res = requests.put(f"{API_URL}/exam/exams/{exam['id']}/publish")
                                        if res.status_code == 200:
                                            st.success("Exam published successfully!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to publish exam.")
                                    except Exception as e:
                                        st.error(f"Error publishing exam: {e}")
                            else:
                                if st.button("📤 Unpublish", key=f"unpublish_{exam['id']}"):
                                    try:
                                        res = requests.put(f"{API_URL}/exam/exams/{exam['id']}/publish", json={"isPublished": False})
                                        if res.status_code == 200:
                                            st.success("Exam unpublished successfully!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to unpublish exam.")
                                    except Exception as e:
                                        st.error(f"Error unpublishing exam: {e}")
                        else:
                            if exam["isPublished"]:
                                st.button("📤 Unpublish", key=f"unpublish_{exam['id']}", disabled=True)
                            else:
                                st.button("🚀 Publish", key=f"publish_{exam['id']}", disabled=True)


                    # --- Delete Button: Allowed unless status is 'live' ---
                    with c3:
                        if exam["status"] != "live":
                            if st.button("❌ Delete", key=f"delete_{exam['id']}"):
                                try:
                                    res = requests.delete(f"{API_URL}/exam/exams/{exam['id']}")
                                    if res.status_code == 200:
                                        st.success("Exam deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete exam.")
                                except Exception as e:
                                    st.error(f"Error deleting exam: {e}")
                        else:
                            st.button("❌ Delete", key=f"delete_{exam['id']}", disabled=True)

                    # --- Questions Navigation ---
                    with c4:
                        if st.button("📄 Questions", key=f"view_questions_{exam['id']}"):
                            st.session_state.current_view = "add_questions"
                            st.session_state.exam_details = exam
                            st.rerun()



        # Classes Section
        st.subheader("🏫 Classes Taking This Subject")
        classes = fetch_data(f"{API_URL}/classes/subject-classes", params={"subject_id": subject['id']})
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
    else:
        # Class detail view
        subject = st.session_state.selected_subject
        class_obj = st.session_state.selected_class
        
        # Extract class details from the object
        class_id = class_obj.get('id', 'N/A')
        class_name = class_obj.get('name', 'No Name Available')
        
        # Back button
        if st.button("← Back to Subject"):
            st.session_state.pop("selected_class", None)
            st.rerun()
        
        # Display header for selected class and subject
        st.header(f"👥 {class_name} ({class_id}) - {subject['name']}")

        # Fetching students data
        students = fetch_data(f"{API_URL}/classes/students/by-class", params={"class_id": class_id})

        if not students:
            st.info("No students found.")
        else:
            st.subheader("🎓 Student Results")
            
            for student in students:
                # Fetching individual student results using student_id and subject_id
                student_results = fetch_data(f"{API_URL}/exam/results", params={"student_id": student['id'], "subject_id": subject['id']}) or []

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
                                    f"{API_URL}/response/responses",
                                    params={"student_id": student['id'], "exam_id": r['examId']}
                                )

                                if responses:
                                    st.markdown("#### 📝 Responses")
                                    for q in responses:
                                        question_text = get_question_text(q.get("id"))
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