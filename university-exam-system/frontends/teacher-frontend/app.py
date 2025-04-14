import streamlit as st
import requests
from datetime import datetime, timedelta

API_URL = "http://localhost:80/teacher/"   # FastAPI service endpoint

st.set_page_config(page_title="Teacher Portal", page_icon="👩‍🏫", layout="wide")
st.title("👩‍🏫 Teacher Portal")

# Mock teacher ID for demonstration
# In a real app, this would come from the login system
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = "67fc99737e9d30613b65d0fb"  # Example teacher ID

# Navigation
page = st.sidebar.selectbox("Choose Section", [
    "📚 My Exams",
    "📝 Create Exam",
    "❓ Manage Questions",
    "📊 Grade Responses"
])

# Utility functions
def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M")

# 1. MY EXAMS SECTION
if page == "📚 My Exams":
    st.header("📚 My Exams")
    
    try:
        # Fetch exams created by the teacher
        response = requests.get(f"{API_URL}/exams?teacher_id={st.session_state.teacher_id}")
        
        if response.status_code == 200:
            exams = response.json()
            
            if not exams:
                st.info("You haven't created any exams yet.")
            else:
                # Display exams in tabs by status
                statuses = ["scheduled", "live", "ended"]
                tabs = st.tabs(["📆 Scheduled", "🔴 Live", "✅ Ended"])
                
                for i, status in enumerate(statuses):
                    with tabs[i]:
                        filtered_exams = [exam for exam in exams if exam["status"] == status]
                        
                        if not filtered_exams:
                            st.info(f"No {status} exams.")
                        else:
                            for exam in filtered_exams:
                                with st.expander(f"{exam['title']} ({exam['status'].upper()})"):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write(f"**ID:** {exam['id']}")
                                        st.write(f"**Subject ID:** {exam['subjectId']}")
                                        st.write(f"**Status:** {exam['status'].upper()}")
                                    
                                    with col2:
                                        st.write(f"**Start Time:** {exam['startTime']}")
                                        st.write(f"**End Time:** {exam['endTime']}")
                                        st.write(f"**Duration:** {exam['durationMinutes']} minutes")
                                    
                                    st.write(f"**Published:** {'Yes' if exam['isPublished'] else 'No'}")
                                    
                                    # Add buttons to view questions or toggle publish status
                                    if st.button(f"View Questions for {exam['title']}", key=f"view_{exam['id']}"):
                                        st.session_state.selected_exam_id = exam['id']
                                        st.session_state.selected_exam_title = exam['title']
                                        st.experimental_rerun()
        else:
            st.error(f"Failed to fetch exams: {response.text}")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# 2. CREATE EXAM SECTION
elif page == "📝 Create Exam":
    st.header("📝 Create New Exam")
    
    with st.form("create_exam_form"):
        title = st.text_input("Exam Title", placeholder="Enter exam title")
        subject_id = st.text_input("Subject ID", placeholder="Enter subject ID")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
            start_time = st.time_input("Start Time")
        with col2:
            end_date = st.date_input("End Date")
            end_time = st.time_input("End Time")
        
        # Combine date and time
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)
        
        duration = st.number_input("Duration (minutes)", min_value=5, max_value=240, value=60)
        publish = st.checkbox("Publish Exam", value=False)
        
        submit_button = st.form_submit_button("Create Exam")
        
        if submit_button:
            if not title or not subject_id:
                st.error("Please fill in all required fields.")
            elif end_datetime <= start_datetime:
                st.error("End time must be after start time.")
            else:
                try:
                    # Format datetime for API
                    start_iso = start_datetime.isoformat()
                    end_iso = end_datetime.isoformat()
                    
                    # Prepare payload
                    payload = {
                        "title": title,
                        "subjectId": subject_id,
                        "startTime": start_iso,
                        "endTime": end_iso,
                        "durationMinutes": duration,
                        "createdBy": st.session_state.teacher_id,
                        "isPublished": publish
                    }
                    
                    # Make API call
                    response = requests.post(f"{API_URL}/exams", json=payload)
                    
                    if response.status_code == 200:
                        st.success("Exam created successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"Failed to create exam: {response.text}")
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

# 3. MANAGE QUESTIONS SECTION
elif page == "❓ Manage Questions":
    st.header("❓ Manage Questions")
    
    # Get exam ID either from URL parameter or input field
    if "selected_exam_id" in st.session_state:
        exam_id = st.session_state.selected_exam_id
        st.info(f"Working with exam: {st.session_state.selected_exam_title}")
    else:
        exam_id = st.text_input("Enter Exam ID", placeholder="Enter the exam ID to manage questions")
    
    if exam_id:
        # Fetch existing questions for this exam
        try:
            response = requests.get(f"{API_URL}/exams/{exam_id}/questions")
            
            if response.status_code == 200:
                questions = response.json()
                
                # Display existing questions
                st.subheader("Existing Questions")
                if not questions:
                    st.info("No questions added to this exam yet.")
                else:
                    for i, q in enumerate(questions):
                        with st.expander(f"Question {i+1}: {q['questionText'][:50]}..."):
                            st.write(f"**Question:** {q['questionText']}")
                            st.write(f"**Type:** {q['type']}")
                            st.write(f"**Marks:** {q['marks']}")
                            
                            if q['type'] == "mcq":
                                st.write("**Options:**")
                                for j, opt in enumerate(q['options']):
                                    st.write(f"{j+1}. {opt}{' ✓' if j == q['correctAnswerIndex'] else ''}")
                            else:  # Long answer
                                st.write("**Expected Keywords:**")
                                st.write(", ".join(q['expectedKeywords']))
                
                # Add new question form
                st.subheader("Add New Question")
                with st.form("add_question_form"):
                    question_text = st.text_area("Question Text", placeholder="Enter the question text")
                    question_type = st.selectbox("Question Type", ["mcq", "long"])
                    marks = st.number_input("Marks", min_value=1, max_value=20)
                    
                    if question_type == "mcq":
                        st.write("Enter Options (one per line)")
                        options_text = st.text_area("Options", placeholder="Enter each option on a new line")
                        correct_index = st.number_input("Correct Option Index (0-based)", min_value=0, max_value=10)
                        expected_keywords = None
                    else:  # Long answer
                        options_text = None
                        correct_index = None
                        expected_keywords = st.text_input("Expected Keywords (comma separated)", placeholder="keyword1, keyword2, ...")
                    
                    submit_button = st.form_submit_button("Add Question")
                    
                    if submit_button:
                        try:
                            # Prepare payload
                            payload = {
                                "questionText": question_text,
                                "type": question_type,
                                "marks": marks
                            }
                            
                            if question_type == "mcq":
                                options = [opt.strip() for opt in options_text.split("\n") if opt.strip()]
                                payload["options"] = options
                                payload["correctAnswerIndex"] = int(correct_index)
                            else:  # Long answer
                                keywords = [kw.strip() for kw in expected_keywords.split(",") if kw.strip()]
                                payload["expectedKeywords"] = keywords
                            
                            # Make API call
                            response = requests.post(f"{API_URL}/exams/{exam_id}/questions", json=payload)
                            
                            if response.status_code == 200:
                                st.success("Question added successfully!")
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed to add question: {response.text}")
                        
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
            
            else:
                st.error(f"Failed to fetch questions: {response.text}")
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# 4. GRADE RESPONSES SECTION
elif page == "📊 Grade Responses":
    st.header("📊 Grade Responses")
    
    # Get exam ID and question ID
    exam_id = st.text_input("Enter Exam ID", placeholder="Enter the exam ID for grading")
    
    if exam_id:
        question_id = st.text_input("Enter Question ID", placeholder="Enter the long-format question ID")
        
        if question_id:
            try:
                # Fetch responses for evaluation
                response = requests.get(f"{API_URL}/exams/{exam_id}/questions/{question_id}/responses")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display question information
                    st.subheader("Question")
                    st.write(data["questionText"])
                    
                    st.write("**Expected Keywords:**")
                    st.write(", ".join(data["expectedKeywords"]))
                    
                    # Display responses
                    st.subheader("Student Responses")
                    
                    if not data["responses"]:
                        st.info("No responses found for grading.")
                    else:
                        for i, resp in enumerate(data["responses"]):
                            with st.expander(f"Response {i+1} - Student ID: {resp['studentId']}"):
                                st.write("**Response:**")
                                st.write(resp["answerText"])
                                
                                marks = st.slider("Marks", min_value=0, max_value=10, key=f"marks_{resp['responseId']}")
                                
                                if st.button("Submit Grade", key=f"grade_{resp['responseId']}"):
                                    try:
                                        # Submit grade
                                        grade_response = requests.post(
                                            f"{API_URL}/responses/{resp['responseId']}/grade",
                                            json={"marks": marks, "gradedBy": st.session_state.teacher_id}
                                        )
                                        
                                        if grade_response.status_code == 200:
                                            st.success("Response graded successfully!")
                                        else:
                                            st.error(f"Failed to grade response: {grade_response.text}")
                                    
                                    except Exception as e:
                                        st.error(f"An error occurred: {str(e)}")
                
                else:
                    st.error(f"Failed to fetch responses: {response.text}")
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Add a footer
st.sidebar.markdown("---")
st.sidebar.info("Teacher ID: " + st.session_state.teacher_id)