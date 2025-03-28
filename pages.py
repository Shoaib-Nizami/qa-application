
'''

            elif selected == "Add Country":
                add_country_form()
            elif selected == "Add City":
                add_city_form()
            elif selected == "Add Project":
                add_project_form()
            elif selected == "Add Plan":
                add_plan_form()
            elif selected == "Add Role":
                add_role_form()

'''


import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, Column, Integer, String, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from models import (
    User, countryIT, cityIT, projectIT, planIT, Role, Comment, Chat, Attachments, 
    StatusCount, ModifiedLog, DeletedLog, ToDoList, TaskHistory, TestCase,
    create_superadmin, generate_password_hash, check_password_hash, generate_sequential_code
)


DATABASE_URL = 'sqlite:///dataQatables.db'
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(bind=engine))
db_session = SessionLocal()

def dashboard():
    # Dashboard data
    def get_summary_data():
        
        with SessionLocal() as session:
            project_summary = session.query(ToDoList.project, func.count(ToDoList.id)).group_by(ToDoList.project).all()
            status_summary = session.query(ToDoList.status, func.count(ToDoList.id)).group_by(ToDoList.status).all()
            priority_summary = session.query(ToDoList.priority, func.count(ToDoList.id)).group_by(ToDoList.priority).all()
            severity_summary = session.query(ToDoList.severity, func.count(ToDoList.id)).group_by(ToDoList.severity).all()
        return project_summary, status_summary, priority_summary, severity_summary

    # Fetch Graph Data
    def get_graph_data():
        
        with SessionLocal() as session:
            project_test_cases = (
                session.query(ToDoList.project, func.count(func.distinct(TestCase.id)))
                .join(TestCase, ToDoList.tasks_assigned == TestCase.task_id)
                .group_by(ToDoList.project)
                .all()
            )

            status_count = (
                session.query(TestCase.status, func.count(func.distinct(TestCase.id)))
                .group_by(TestCase.status)
                .all()
            )

            build_versions = (
                session.query(TestCase.build_version, func.count(func.distinct(TestCase.id)))
                .filter(TestCase.build_version.isnot(None))
                .group_by(TestCase.build_version)
                .all()
            )
        return project_test_cases, status_count, build_versions
    
    # 📌 **Dashboard Page**
    if st.sidebar.selectbox("Select Page:", ["Dashboard"]) == "Dashboard":
        # 🔍 **Fetch Data**
        project_summary, status_summary, priority_summary, severity_summary = get_summary_data()
        project_test_cases, status_count, build_versions = get_graph_data()

        # 📌 **Summary Overview**
        st.header("Tasks Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.subheader("📂 Project-wise Tasks")
            st.table(pd.DataFrame(project_summary, columns=["Project", "Total Tasks"]))
        with col2:
            st.subheader("📊 Status-wise Tasks")
            st.table(pd.DataFrame(status_summary, columns=["Status", "Total Tasks"]))
        with col3:
            st.subheader("⚡ Priority-wise Tasks")
            st.table(pd.DataFrame(priority_summary, columns=["Priority", "Total Tasks"]))
        with col4:
            st.subheader("🚨 Severity-wise Defects")
            st.table(pd.DataFrame(severity_summary, columns=["Severity", "Total Defects"]))
        
            
        
        # 📊 **Test Case Analysis**
        st.header("📊 Test Case Analysis")
        graph_option = st.selectbox("Select Graph Type:", ["Project-wise Test Cases", "Status-wise Test Cases", "Build Version-wise Analysis"])
        
        # 📌 **Graph 1: Project-wise Test Cases**
        if graph_option == "Project-wise Test Cases":
            df = pd.DataFrame(project_test_cases, columns=["Project", "Test Case Count"])
            if not df.empty:
                fig = px.bar(df, x="Project", y="Test Case Count", title="Test Cases per Project", text="Test Case Count", color="Project")
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig)
            else:
                st.warning("⚠️ No data available for Project-wise Test Cases.")
        
        # 📌 **Graph 2: Status-wise Test Cases**
        elif graph_option == "Status-wise Test Cases":
            df = pd.DataFrame(status_count, columns=["Status", "Count"])
            if not df.empty:
                color_map = {
                    "Pass": "#4CAF50",        # **Deep Green (Success)**
                    "Fail": "#D72638",       # **Professional Red (Failure)**
                    "Blocked": "#FF9F1C",    # **Muted Orange (Blocked)**
                    "Pending": "#8982c4", # **Steel Blue (Ongoing)**
                    "Pass (fixed)": "lightgreen" # **Soft Green (Fixed)**
                }
                fig = px.pie(df, names="Status", values="Count", title="Test Case Status Distribution", color="Status", color_discrete_map=color_map)
                st.plotly_chart(fig)
            else:
                st.warning("⚠️ No data available for Status-wise Test Cases.")
        

        # 📌 **Graph 3: Build Version-wise Test Cases**
        elif graph_option == "Build Version-wise Analysis":
            with SessionLocal() as session:
                projects = [p[0] for p in session.query(ToDoList.project).distinct().all()]
            selected_project = st.selectbox("Select Project:", projects)

            with SessionLocal() as session:
                build_versions = [
                    b[0] for b in session.query(TestCase.build_version)
                    .join(ToDoList, TestCase.task_id == ToDoList.tasks_assigned)
                    .filter(ToDoList.project == selected_project)
                    .distinct()
                    .all()
                ]

            if build_versions:
                selected_version = st.multiselect("Select Build Version(s):", build_versions, default=build_versions)

                if selected_version:
                    with SessionLocal() as session:
                        version_data = (
                            session.query(
                                TestCase.build_version,
                                TestCase.status,
                                func.count(func.distinct(TestCase.id)).label("Test Case Count")
                            )
                            .join(ToDoList, ToDoList.tasks_assigned == TestCase.task_id)
                            .filter(ToDoList.project == selected_project)
                            .filter(TestCase.build_version.in_(selected_version))
                            .group_by(TestCase.build_version, TestCase.status)
                            .order_by(TestCase.build_version)
                            .all()
                        )

                    df = pd.DataFrame(version_data, columns=["Build Version", "Status", "Test Case Count"])

                    if not df.empty:
                        # 🎨 **Professional Color Palette**

                        color_map = {
                            "Pass": "#4CAF50",        # **Deep Green (Success)**
                            "Fail": "#D72638",       # **Professional Red (Failure)**
                            "Blocked": "#FF9F1C",    # **Muted Orange (Blocked)**
                            "Pending": "#8982c4", # **Steel Blue (Ongoing)**
                            "Pass (fixed)": "lightgreen" # **Soft Green (Fixed)**
                        }

                        # 📊 **Modern Graph Styling**
                        fig = px.bar(
                            df,
                            x="Build Version",
                            y="Test Case Count",
                            title=f"Test Case Analysis by Build Version for {selected_project}",
                            text="Test Case Count",
                            color="Status",
                            color_discrete_map=color_map,
                            labels={"Build Version": "Build Version", "Test Case Count": "Number of Test Cases"},
                            barmode="group",  # **Grouped Bar Chart for better visibility**
                        )

                        # 🔹 **Graph Aesthetic Improvements**
                        fig.update_traces(
                            textposition="outside",  # Show count values on bars
                            marker_line_color='black',  # Add subtle border to bars
                            marker_line_width=1.2
                        )

                        fig.update_layout(
                            xaxis_title="Build Version",
                            yaxis_title="Number of Test Cases",
                            font=dict(family="Arial, sans-serif", size=14, color="black"),  # Professional Font
                            plot_bgcolor="#f8f9fa",  # Light grey background for a clean look
                            paper_bgcolor="#ffffff",  # White paper background
                            xaxis=dict(showgrid=True, gridcolor='lightgrey'),  # Subtle gridlines
                            yaxis=dict(showgrid=True, gridcolor='lightgrey'),
                            legend=dict(title="", orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)  # Move legend below chart
                        )

                        st.plotly_chart(fig)
                    else:
                        st.warning(f"⚠️ No test cases found for {selected_project} in selected builds.")
                else:
                    st.warning("⚠️ Please select at least one build version.")
            else:
                st.warning("⚠️ No build versions available for the selected project.")



def add_country_form():
    st.subheader("Add Country")

    # Input fields
    code = st.text_input("Country Code", placeholder="Enter a unique country code")
    name = st.text_input("Country Name", placeholder="Enter the country name")
    description = st.text_input("Description", placeholder="Enter a description")
    created_by = st.session_state.username  # Get the logged-in user

    if st.button("✅ Add Country"):
        # Validation
        if not code.strip():
            st.error("🚨 Country Code is required!")
            return
        if not name.strip():
            st.error("🚨 Country Name is required!")
            return
        if not description.strip():
            st.error("🚨 Description is required!")
            return

        # Check if country code or name already exists
        if db_session.query(countryIT).filter_by(code=code).first():
            st.error("🚨 Country Code already exists!")
            return
        if db_session.query(countryIT).filter_by(name=name).first():
            st.error("🚨 Country Name already exists!")
            return

        # Create new country
        new_country = countryIT(
            code=code,
            name=name,
            description=description,
            created_by=created_by,
        )

        try:
            db_session.add(new_country)
            db_session.commit()
            st.success(f"✅ Country '{name}' added successfully!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            db_session.rollback()
            st.error(f"❌ Error adding country: {e}")
        finally:
            db_session.close()
            
            
def add_city_form():
    st.subheader("Add City")

    # Input fields
    code = st.text_input("City Code", placeholder="Enter a unique city code")
    name = st.text_input("City Name", placeholder="Enter the city name")
    description = st.text_input("Description", placeholder="Enter a description")
    created_by = st.session_state.username  # Get the logged-in user

    # Fetch countries for dropdown
    countries = db_session.query(countryIT).all()
    country_id = st.selectbox("Country", options=[""] + [country.name for country in countries])

    if st.button("✅ Add City"):
        # Validation
        if not code.strip():
            st.error("🚨 City Code is required!")
            return
        if not name.strip():
            st.error("🚨 City Name is required!")
            return
        if not description.strip():
            st.error("🚨 Description is required!")
            return
        if not country_id:
            st.error("🚨 Country is required!")
            return

        # Check if city code or name already exists
        if db_session.query(cityIT).filter_by(code=code).first():
            st.error("🚨 City Code already exists!")
            return
        if db_session.query(cityIT).filter_by(name=name).first():
            st.error("🚨 City Name already exists!")
            return

        # Fetch the selected country
        selected_country = db_session.query(countryIT).filter_by(name=country_id).first()
        if not selected_country:
            st.error("🚨 Invalid country selection!")
            return

        # Create new city
        new_city = cityIT(
            code=code,
            name=name,
            description=description,
            country_id=selected_country.id,
            created_by=created_by,
        )

        try:
            db_session.add(new_city)
            db_session.commit()
            st.success(f"✅ City '{name}' added successfully!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            db_session.rollback()
            st.error(f"❌ Error adding city: {e}")
        finally:
            db_session.close()
            
            
            
            
            
            
def add_project_form():
    st.subheader("Add Project")

    # Input fields
    code = st.text_input("Project Code", placeholder="Enter a unique project code")
    name = st.text_input("Project Name", placeholder="Enter the project name")
    description = st.text_input("Description", placeholder="Enter a description")
    created_by = st.session_state.username  # Get the logged-in user

    # Fetch cities for dropdown
    cities = db_session.query(cityIT).all()
    city_id = st.selectbox("City", options=[""] + [city.name for city in cities])

    if st.button("✅ Add Project"):
        # Validation
        if not code.strip():
            st.error("🚨 Project Code is required!")
            return
        if not name.strip():
            st.error("🚨 Project Name is required!")
            return
        if not description.strip():
            st.error("🚨 Description is required!")
            return
        if not city_id:
            st.error("🚨 City is required!")
            return

        # Check if project code or name already exists
        if db_session.query(projectIT).filter_by(code=code).first():
            st.error("🚨 Project Code already exists!")
            return
        if db_session.query(projectIT).filter_by(name=name).first():
            st.error("🚨 Project Name already exists!")
            return

        # Fetch the selected city
        selected_city = db_session.query(cityIT).filter_by(name=city_id).first()
        if not selected_city:
            st.error("🚨 Invalid city selection!")
            return

        # Create new project
        new_project = projectIT(
            code=code,
            name=name,
            description=description,
            city_id=selected_city.id,
            created_by=created_by,
        )

        try:
            db_session.add(new_project)
            db_session.commit()
            st.success(f"✅ Project '{name}' added successfully!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            db_session.rollback()
            st.error(f"❌ Error adding project: {e}")
        finally:
            db_session.close()            
            
            
            
            
def add_plan_form():
    st.subheader("Add Plan")

    # Input fields
    code = st.text_input("Plan Code", placeholder="Enter a unique plan code")
    name = st.text_input("Plan Name", placeholder="Enter the plan name")
    description = st.text_input("Description", placeholder="Enter a description")
    created_by = st.session_state.username  # Get the logged-in user

    # Fetch projects for dropdown
    projects = db_session.query(projectIT).all()
    project_id = st.selectbox("Project", options=[""] + [project.name for project in projects])

    if st.button("✅ Add Plan"):
        # Validation
        if not code.strip():
            st.error("🚨 Plan Code is required!")
            return
        if not name.strip():
            st.error("🚨 Plan Name is required!")
            return
        if not description.strip():
            st.error("🚨 Description is required!")
            return
        if not project_id:
            st.error("🚨 Project is required!")
            return

        # Check if plan code or name already exists
        if db_session.query(planIT).filter_by(code=code).first():
            st.error("🚨 Plan Code already exists!")
            return
        if db_session.query(planIT).filter_by(name=name).first():
            st.error("🚨 Plan Name already exists!")
            return

        # Fetch the selected project
        selected_project = db_session.query(projectIT).filter_by(name=project_id).first()
        if not selected_project:
            st.error("🚨 Invalid project selection!")
            return

        # Create new plan
        new_plan = planIT(
            code=code,
            name=name,
            description=description,
            project_id=selected_project.id,
            created_by=created_by,
        )

        try:
            db_session.add(new_plan)
            db_session.commit()
            st.success(f"✅ Plan '{name}' added successfully!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            db_session.rollback()
            st.error(f"❌ Error adding plan: {e}")
        finally:
            db_session.close()





def add_role_form():
    st.subheader("Add Role")

    # Input fields
    code = st.text_input("Role Code", placeholder="Enter a unique role code")
    name = st.text_input("Role Name", placeholder="Enter the role name")
    description = st.text_input("Description", placeholder="Enter a description")
    created_by = st.session_state.username  # Get the logged-in user

    if st.button("✅ Add Role"):
        # Validation
        if not code.strip():
            st.error("🚨 Role Code is required!")
            return
        if not name.strip():
            st.error("🚨 Role Name is required!")
            return
        if not description.strip():
            st.error("🚨 Description is required!")
            return

        # Check if role code or name already exists
        if db_session.query(Role).filter_by(code=code).first():
            st.error("🚨 Role Code already exists!")
            return
        if db_session.query(Role).filter_by(name=name).first():
            st.error("🚨 Role Name already exists!")
            return

        # Create new role
        new_role = Role(
            code=code,
            name=name,
            description=description,
            created_by=created_by,
        )

        try:
            db_session.add(new_role)
            db_session.commit()
            st.success(f"✅ Role '{name}' added successfully!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            db_session.rollback()
            st.error(f"❌ Error adding role: {e}")
        finally:
            db_session.close()            