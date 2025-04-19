import streamlit as st
import requests

API_URL = "http://localhost:80/"

st.title("🎓 University Admin Panel")

# Navigation
page = st.sidebar.selectbox("Choose Action", [
    "👩‍🏫 Teachers",
    "🧑‍🎓 Students",
    "🏫 Classes",
    "📝 Exams",
    "📘 Subjects",
    "📖 Stories",
    "📬 Requests"
])

# 1. Teachers Section
if page == "👩‍🏫 Teachers":
    st.subheader("👩‍🏫 Teachers")

    res = requests.get(f"{API_URL}/user/teachers")
    if res.status_code == 200:
        teachers = res.json()
        st.write("Existing Teachers")
        st.dataframe(teachers)

        st.subheader("➕ Add New Teacher")
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Create Teacher"):
            res = requests.post(f"{API_URL}/user/teachers", json={
                "name": name,
                "email": email,
                "password": password
            })
            if res.status_code == 200:
                st.success("Teacher created successfully!")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

        st.subheader("📚 Assign Teacher to Subject")

        subjects_res = requests.get(f"{API_URL}/classes/subjects").json()
        subject_names = [s["name"] for s in subjects_res]
        selected_subject = st.selectbox("Select Subject", subject_names)

        teachers_res = requests.get(f"{API_URL}/user/teachers").json()
        teacher_names = [t["name"] for t in teachers_res]
        selected_teacher = st.selectbox("Select Teacher", teacher_names)

        subject_id = subjects_res[subject_names.index(selected_subject)]["_id"]
        teacher_id = teachers_res[teacher_names.index(selected_teacher)]["_id"]

        if st.button("Assign Teacher"):
            res = requests.post(f"{API_URL}/classes/subjects/{subject_id}/assign_teacher", json={
                "teacher_id": teacher_id
            })
            if res.status_code == 200:
                st.success("Teacher assigned successfully!")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

        st.subheader("❌ Delete Teacher")
        teacher_to_delete = st.selectbox("Select Teacher to Delete", teacher_names)
        if st.button("Delete Teacher"):
            teacher_id = teachers_res[teacher_names.index(teacher_to_delete)]["_id"]
            res = requests.delete(f"{API_URL}/user/teachers/{teacher_id}")
            if res.status_code == 200:
                st.success("Teacher deleted.")
            else:
                st.error(res.json().get("detail", "Something went wrong."))
    else:
        st.error("Failed to fetch teachers.")

# 2. Students Section
elif page == "🧑‍🎓 Students":
    st.subheader("🧑‍🎓 Students")

    res = requests.get(f"{API_URL}/user/students")
    if res.status_code == 200:
        students = res.json()
        st.write("Existing Students")
        st.dataframe(students)

        st.subheader("➕ Add New Student")
        name = st.text_input("Name")
        email = st.text_input("Email")
        roll_number = st.text_input("Roll Number")
        student_class = st.text_input("Class ID (e.g. 10A)")
        password = st.text_input("Password", type="password")

        if st.button("Create Student"):
            res = requests.post(f"{API_URL}/user/students", json={
                "name": name,
                "email": email,
                "rollNumber": roll_number,
                "classId": student_class,
                "password": password
            })
            if res.status_code == 200:
                st.success("Student created successfully!")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

        st.subheader("❌ Delete Student")
        student_names = [s["name"] for s in students]
        selected_student = st.selectbox("Select Student to Delete", student_names)

        if st.button("Delete Student"):
            student_id = students[student_names.index(selected_student)]["_id"]
            res = requests.delete(f"{API_URL}/user/students/{student_id}")
            if res.status_code == 200:
                st.success("Student deleted.")
            else:
                st.error(res.json().get("detail", "Something went wrong."))
    else:
        st.error("Failed to fetch students.")

# 3. Classes Section
elif page == "🏫 Classes":
    st.subheader("🏫 Classes")

    students_res = requests.get(f"{API_URL}/user/students")
    if students_res.status_code == 200:
        students = students_res.json()
        class_list = sorted(set(s.get("classId", "Unknown") for s in students))
        selected_class = st.selectbox("Select Class", class_list)

        if selected_class:
            class_students = [s for s in students if s.get("classId") == selected_class]
            st.write(f"Students in class {selected_class}")
            st.dataframe(class_students)

        st.subheader("➕ Create Class")
        new_class_name = st.text_input("Class ID (e.g. 10C)")

        if st.button("Create Class"):
            if new_class_name:
                res = requests.post(f"{API_URL}/classes/classes", json={"class_name": new_class_name})
                if res.status_code == 200:
                    st.success(f"Class '{new_class_name}' created!")
                else:
                    st.error(res.json().get("detail", "Something went wrong."))
            else:
                st.error("Class name cannot be empty.")
    else:
        st.error("Failed to fetch students.")

# 4. Exams Section
elif page == "📝 Exams":
    st.subheader("📝 Exams")

    exams_res = requests.get(f"{API_URL}/exam/exams")
    if exams_res.status_code == 200:
        exams = exams_res.json()

        exam_titles = [e["title"] for e in exams]
        selected_exam = st.selectbox("Select Exam", exam_titles)
        exam_id = [e["_id"] for e in exams if e["title"] == selected_exam][0]

        st.subheader("🕒 Change Exam Status")
        new_status = st.selectbox("Select Status", ["draft", "scheduled", "live", "evaluation", "ended"])

        if st.button("Update Exam Status"):
            res = requests.put(f"{API_URL}/exam/exams/{exam_id}/status", json={"status": new_status})
            if res.status_code == 200:
                st.success(f"Status updated to {new_status}!")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

        st.subheader("❌ Delete Exam")
        if st.button("Delete Exam"):
            res = requests.delete(f"{API_URL}/exam/exams/{exam_id}")
            if res.status_code == 200:
                st.success("Exam deleted.")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

        st.subheader("➕ Create Exam")
        subjects = requests.get(f"{API_URL}/classes/subjects").json()
        subject_names = [s["name"] for s in subjects]
        selected_subject = st.selectbox("Subject", subject_names)
        title = st.text_input("Exam Title")
        start = st.date_input("Start Date")
        end = st.date_input("End Date")

        if st.button("Create Exam"):
            subject_id = subjects[subject_names.index(selected_subject)]["_id"]
            res = requests.post(f"{API_URL}/exam/exams", json={
                "exam_title": title,
                "subject_id": subject_id,
                "start_time": str(start),
                "end_time": str(end)
            })
            if res.status_code == 200:
                st.success("Exam created.")
            else:
                st.error(res.json().get("detail", "Something went wrong."))
    else:
        st.error("Failed to fetch exams.")

# 5. Subjects Section
elif page == "📘 Subjects":
    st.subheader("📘 Subjects")

    subjects = requests.get(f"{API_URL}/classes/subjects").json()
    if subjects:
        st.write("Subjects")
        st.dataframe(subjects)

        st.subheader("➕ Create Subject")
        name = st.text_input("Subject Name")
        code = st.text_input("Subject Code")

        if st.button("Create Subject"):
            res = requests.post(f"{API_URL}/classes/subjects", json={"subject_name": name, "subject_code": code})
            if res.status_code == 200:
                st.success("Subject created.")
            else:
                st.error(res.json().get("detail", "Something went wrong."))

        st.subheader("❌ Delete Subject")
        names = [s["name"] for s in subjects]
        selected_subject = st.selectbox("Select Subject to Delete", names)

        if st.button("Delete Subject"):
            subject_id = subjects[names.index(selected_subject)]["_id"]
            res = requests.delete(f"{API_URL}/classes/subjects/{subject_id}")
            if res.status_code == 200:
                st.success("Subject deleted.")
            else:
                st.error(res.json().get("detail", "Something went wrong."))
    else:
        st.error("Failed to fetch subjects.")

# 6. Stories Section
elif page == "📖 Stories":
    st.subheader("📖 Manage Stories")

    # Base URL of the Flask stories service
    STORIES_API = f"{API_URL}/stories/stories"  # Adjust if reverse-proxied or Docker network alias

    # ==== Show All Stories ====
    try:
        res = requests.get(STORIES_API)
        if res.status_code == 200:
            all_stories = res.json()
            if all_stories:
                for story in all_stories:
                    with st.expander(f"📘 {story.get('title', 'Untitled')}"):
                        st.write(f"✏️ **Author**: {story.get('author', 'N/A')}")
                        st.write(f"📖 **Content**:\n\n{story.get('content', 'No content')}")
                        if st.button(f"🗑 Delete Story: {story.get('title')}", key=story.get("title")):
                            del_res = requests.delete(STORIES_API, params={"title": story.get("title")})
                            if del_res.status_code == 200:
                                st.success("Story deleted successfully.")
                                st.rerun()
                            else:
                                st.error("Failed to delete story.")
            else:
                st.info("No stories available.")
        else:
            st.error("Failed to fetch stories.")
    except Exception as e:
        st.error(f"Error: {e}")

    st.markdown("---")
    st.subheader("➕ Add New Story")

    title = st.text_input("Story Title")
    author = st.text_input("Author Name")
    content = st.text_area("Story Content")

    if st.button("Submit Story"):
        if title and content:
            story_data = {
                "title": title,
                "author": author,
                "content": content
            }
            try:
                res = requests.post(STORIES_API, json=story_data)
                if res.status_code == 200:
                    st.success("Story added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add story.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Title and content are required.")

# 7. Handle Student Requests
elif page == "📬 Requests":
    st.subheader("📬 Student Requests")

    REQUESTS_API = f"{API_URL}/requests/requests"

    # === Fetch all requests ===
    try:
        res = requests.get(REQUESTS_API)
        if res.status_code == 200:
            all_requests = res.json()
            if not all_requests:
                st.info("No requests found.")
            else:
                for req in all_requests:
                    with st.expander(f"📌 {req['title']} (Status: {req['status'].capitalize()})"):
                        st.write(f"🧑 Requested By: `{req['requested_by']}`")
                        st.write(f"📂 Category: {req['category']}")
                        st.write(f"📝 Description:\n\n{req['description']}")
                        st.write(f"📅 Created At: {req.get('created_at', 'N/A')}")
                        if req.get("admin_comment"):
                            st.write(f"💬 Admin Comment: {req['admin_comment']}")

                        if req["status"] == "pending":
                            new_status = st.selectbox(
                                "Update Status",
                                options=["approved", "denied"],
                                key=f"status_{req['id']}"
                            )
                            comment = st.text_area("Admin Comment (Optional)", key=f"comment_{req['id']}")

                            if st.button("✅ Update", key=f"update_{req['id']}"):
                                try:
                                    update_data = {
                                        "status": new_status,
                                        "admin_comment": comment
                                    }
                                    update_res = requests.put(
                                        f"{REQUESTS_API}/{req['id']}",
                                        json=update_data
                                    )
                                    if update_res.status_code == 200:
                                        st.success("Request updated successfully.")
                                        st.rerun()
                                    else:
                                        st.error("Failed to update request.")
                                except Exception as e:
                                    st.error(f"Error: {e}")
        else:
            st.error("Failed to fetch requests.")
    except Exception as e:
        st.error(f"Error fetching requests: {e}")
