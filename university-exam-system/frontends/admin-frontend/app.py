import streamlit as st
import requests

API_URL = "http://localhost:80/admin/"  # Replace with actual admin service port

st.title("🎓 University Admin Panel")

# Navigation
page = st.sidebar.selectbox("Choose Action", [
    "👩‍🏫 Teachers",
    "🧑‍🎓 Students",
    "🏫 Classes",
    "📝 Exams",
    "📘 Subjects"
])

# 1. Teachers Section
if page == "👩‍🏫 Teachers":
    st.subheader("👩‍🏫 Teachers")

    # Fetch all teachers
    res = requests.get(f"{API_URL}/admin/teachers")
    if res.status_code == 200:
        teachers = res.json()
        st.write("Existing Teachers")
        st.dataframe(teachers)
        
        # Add New Teacher
        st.subheader("➕ Add New Teacher")

        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Create Teacher"):
            res = requests.post(f"{API_URL}/admin/teachers", json={
                "name": name,
                "email": email,
                "password": password
            })
            if res.status_code == 200:
                st.success("Teacher created successfully!")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

        # Assign Teacher to a Subject
        st.subheader("📚 Assign Teacher to Subject")

        subjects_res = requests.get(f"{API_URL}/admin/subjects").json()
        subject_names = [s["name"] for s in subjects_res]
        teachers_res = requests.get(f"{API_URL}/admin/teachers").json()
        teacher_names = [t["name"] for t in teachers_res]

        selected_subject = st.selectbox("Select Subject", subject_names)
        selected_teacher = st.selectbox("Select Teacher", teacher_names)

        subject_id = subjects_res[subject_names.index(selected_subject)]["_id"]
        teacher_id = teachers_res[teacher_names.index(selected_teacher)]["_id"]

        if st.button("Assign Teacher"):
            res = requests.post(f"{API_URL}/admin/subjects/{subject_id}/assign_teacher", json={
                "teacher_id": teacher_id
            })
            if res.status_code == 200:
                st.success("Teacher assigned to subject successfully!")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

        # Delete Teacher
        st.subheader("❌ Delete Teacher")

        teacher_to_delete = st.selectbox("Select Teacher to Delete", teacher_names)

        if st.button("Delete Teacher"):
            teacher_id_to_delete = teachers_res[teacher_names.index(teacher_to_delete)]["_id"]
            res = requests.delete(f"{API_URL}/admin/teachers/{teacher_id_to_delete}")
            if res.status_code == 200:
                st.success("Teacher deleted successfully!")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

    else:
        st.error("Failed to fetch teachers.")

# 2. Students Section
elif page == "🧑‍🎓 Students":
    st.subheader("🧑‍🎓 Students")

    # Fetch all students
    res = requests.get(f"{API_URL}/admin/students")
    if res.status_code == 200:
        students = res.json()
        st.write("Existing Students")
        st.dataframe(students)

        # Add New Student
        st.subheader("➕ Add New Student")

        name = st.text_input("Name")
        email = st.text_input("Email")
        roll_number = st.text_input("Roll Number")
        student_class = st.text_input("Class")
        password = st.text_input("Password", type="password")

        if st.button("Create Student"):
            res = requests.post(f"{API_URL}/admin/students", json={
                "name": name,
                "email": email,
                "rollNumber": roll_number,
                "class": student_class,
                "password": password
            })
            if res.status_code == 200:
                st.success("Student created successfully!")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

        # Assign Subjects to Student
        st.subheader("📘 Assign Subjects to Student")

        subjects_res = requests.get(f"{API_URL}/admin/subjects").json()
        subject_names = [s["name"] for s in subjects_res]

        students_res = requests.get(f"{API_URL}/admin/students").json()
        student_names = [s["name"] for s in students_res]

        selected_student = st.selectbox("Select Student", student_names)
        selected_subjects = st.multiselect("Select Subjects", subject_names)

        student_id = students_res[student_names.index(selected_student)]["_id"]
        subject_ids = [subjects_res[subject_names.index(s)]["_id"] for s in selected_subjects]

        if st.button("Assign Subjects"):
            res = requests.post(f"{API_URL}/admin/subjects/{student_id}/assign_student", json={
                "student_id": student_id,
                "course_ids": subject_ids
            })
            if res.status_code == 200:
                st.success("Subjects assigned to student successfully!")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

        # Delete Student
        st.subheader("❌ Delete Student")

        student_to_delete = st.selectbox("Select Student to Delete", student_names)

        if st.button("Delete Student"):
            student_id_to_delete = students_res[student_names.index(student_to_delete)]["_id"]
            res = requests.delete(f"{API_URL}/admin/students/{student_id_to_delete}")
            if res.status_code == 200:
                st.success("Student deleted successfully!")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

    else:
        st.error("Failed to fetch students.")

# Classes section
elif page == "🏫 Classes":
    st.subheader("🏫 Classes")

    # Fetch all students
    res = requests.get(f"{API_URL}/admin/students")
    if res.status_code == 200:
        students = res.json()

        # List available classes
        class_list = sorted(set(s["class"] for s in students))
        selected_class = st.selectbox("Select Class", class_list)

        if selected_class:
            filtered_students = [s for s in students if s["class"] == selected_class]
            st.write(f"👨‍🎓 Students in class **{selected_class}**")
            st.dataframe(filtered_students)
        
        # Create a new class
        st.subheader("➕ Create Class")
        new_class_name = st.text_input("Enter class name")

        if st.button("Create Class"):
            if new_class_name:
                res = requests.post(f"{API_URL}/admin/classes", json={"class_name": new_class_name})
                if res.status_code == 200:
                    st.success(f"Class '{new_class_name}' created successfully!")
                else:
                    st.error(res.json().get("detail", "Something went wrong."))
            else:
                st.error("Please enter a class name.")
    else:
        st.error("Failed to fetch students.")


# 4. Exams Section
# 4. Exams Section
elif page == "📝 Exams":
    st.subheader("📝 Exams")

    # Fetch all exams
    exams_res = requests.get(f"{API_URL}/admin/exams")
    if exams_res.status_code == 200:
        exams = exams_res.json()

        exam_options = {f"{exam['title']}": exam['_id'] for exam in exams}
        selected_exam_title = st.selectbox("Select Exam", list(exam_options.keys()))

        if selected_exam_title:
            exam_id = exam_options[selected_exam_title]

            # Change Exam Status
            st.subheader("🕒 Change Exam Status")
            exam_status = st.selectbox("Select Status", ["scheduled", "live", "ended", "reval"])

            if st.button("Update Exam Status"):
                res = requests.put(f"{API_URL}/admin/exams/{exam_id}/status", json={
                    "status": exam_status
                })
                if res.status_code == 200:
                    st.success(f"Exam status updated to {exam_status}!")
                else:
                    st.error(res.json().get("detail", "Something went wrong."))

            # Delete Exam
            st.subheader("❌ Delete Exam")
            if st.button("Delete Exam"):
                res = requests.delete(f"{API_URL}/admin/exams/{exam_id}")
                if res.status_code == 200:
                    st.success("Exam deleted successfully!")
                else:
                    st.error(res.json().get("detail", "Something went wrong."))

        # Create Exam
        st.subheader("➕ Create Exam")
        subjects_res = requests.get(f"{API_URL}/admin/subjects").json()
        subject_names = [s["name"] for s in subjects_res]
        selected_subject = st.selectbox("Select Subject", subject_names)

        exam_title = st.text_input("Enter Exam Title")
        start_time = st.date_input("Start Time")
        end_time = st.date_input("End Time")

        if st.button("Create Exam"):
            if exam_title and selected_subject and start_time and end_time:
                subject_id = subjects_res[subject_names.index(selected_subject)]["_id"]
                res = requests.post(f"{API_URL}/admin/exams", json={
                    "exam_title": exam_title,
                    "subject_id": subject_id,
                    "start_time": start_time,
                    "end_time": end_time
                })
                if res.status_code == 200:
                    st.success(f"Exam '{exam_title}' created successfully!")
                else:
                    st.error(res.json().get("detail", "Something went wrong."))
            else:
                st.error("Please fill in all fields for creating the exam.")
    else:
        st.error("Failed to fetch exams.")


# Subject section
elif page == "📘 Subjects":
    st.subheader("📘 Subjects")

    # Fetch all subjects
    subjects_res = requests.get(f"{API_URL}/admin/subjects").json()
    if subjects_res:
        st.write("Existing Subjects")
        st.dataframe(subjects_res)

        # Create a new subject
        st.subheader("➕ Create Subject")
        subject_name = st.text_input("Enter Subject Name")
        subject_code = st.text_input("Enter Subject Code")

        if st.button("Create Subject"):
            if subject_name and subject_code:
                res = requests.post(f"{API_URL}/admin/subjects", json={
                    "subject_name": subject_name,
                    "subject_code": subject_code
                })
                if res.status_code == 200:
                    st.success(f"Subject '{subject_name}' created successfully!")
                else:
                    st.error(res.json().get("detail", "Something went wrong."))
            else:
                st.error("Please enter both subject name and code.")
        
        # Delete Subject
        st.subheader("❌ Delete Subject")
        subject_names = [s["name"] for s in subjects_res]
        subject_to_delete = st.selectbox("Select Subject to Delete", subject_names)

        if st.button("Delete Subject"):
            subject_id_to_delete = subjects_res[subject_names.index(subject_to_delete)]["_id"]
            res = requests.delete(f"{API_URL}/admin/subjects/{subject_id_to_delete}")
            if res.status_code == 200:
                st.success("Subject deleted successfully!")
            else:
                st.error(res.json().get("detail", "Something went wrong."))
    else:
        st.error("Failed to fetch subjects.")
