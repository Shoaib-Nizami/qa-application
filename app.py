

import plotly.express as px
import time
from sqlalchemy.orm import joinedload
from sqlalchemy.dialects.sqlite import dialect  # Change dialect if needed
import uuid
from deep_translator import GoogleTranslator
import random
import openai
import os
import streamlit as st
from streamlit_option_menu import option_menu
from sqlalchemy import create_engine, Column, Integer, String, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import pandas as pd
from dateutil import parser
from datetime import datetime, timedelta
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_extras.stylable_container import stylable_container
#from pages import add_country_form, add_city_form, add_project_form, add_plan_form, add_role_form
from pages import dashboard
import re

st.set_page_config(page_title="QA", page_icon="person-plus", layout="wide")


import jwt
import secrets
from dotenv import load_dotenv
from passlib.hash import pbkdf2_sha256 as sha256
from streamlit_cookies_manager import EncryptedCookieManager
from models import (
    User, countryIT, cityIT, projectIT, planIT, Role, Comment, Chat, Attachments, 
    StatusCount, ModifiedLog, DeletedLog, ToDoList, TaskHistory, TestCase,
    create_superadmin, generate_password_hash, check_password_hash, generate_sequential_code
)


from _qa_automation_ import qa_automation_page


# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
#print(SECRET_KEY)
if not SECRET_KEY:
    raise ValueError("❌ SECRET_KEY is not set! Please check your .env file.")

secure_password = os.getenv("COOKIE_PASSWORD", secrets.token_urlsafe(32))


# Hide "Deploy this app" footer
hide_streamlit_style = """
    <style>
        header {visibility: hidden;}  /* Hides Streamlit menu */
        footer {visibility: hidden;}  /* Hides Streamlit footer */
        .stDeployButton {display: none !important;}  /* Hides the Deploy button */
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)



# Add custom CSS for a compact and professional layout
st.markdown("""
    <style>
        /* Form container styling */
        .stForm {
            max-width: 100%; /* Full width for the form */
            margin: 0 auto; /* Center the form */
            padding: 10px; /* Reduced padding */
            background-color: #f9f9f9; /* Light background */
            border-radius: 8px; /* Rounded corners */
        }

        /* Creating a 2-column layout */
        .stForm div {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            margin-bottom: 5px; /* Reduced margin between rows */
        }

        /* Adjusting for 2 fields per row */
        .stTextInput, .stTextArea, .stSelectbox {
            flex: 1 1 48%; /* Flex for 2 columns */
            margin-right: 10px; /* Margin between columns */
            margin-bottom: 5px; /* Reduced margin between fields */
        }

        /* Remove margin on the last field in a row */
        .stForm .stTextInput:nth-child(2n), 
        .stForm .stTextArea:nth-child(2n), 
        .stForm .stSelectbox:nth-child(2n) {
            margin-right: 0;
        }

        /* Title styling */
        .css-1d391kg {
            text-align: center; /* Center title */
            margin-bottom: 5px; /* Reduced space below title */
        }

        /* Styling for error and success messages */
        .stErrorMessage, .stSuccessMessage {
            width: 100%;
            margin: 3px auto;
            font-size: 12px;
            padding: 4px;
            border-radius: 5px;
            background-color: #F8D7DA;
            color: #721C24;
        }

        /* Save button styling */
        .stButton {
            width: 100%;
            font-size: 14px;
            background-color: white;
            color: black;
            border-radius: 8px;
            padding: 8px;
            margin-top: 10px;
        }

        /* Adjust margin between form elements */
        .stForm input, .stForm textarea, .stForm select {
            margin-bottom: 5px; /* Reduced margin */
        }

        /* Aligning form labels and fields together */
        .stTextInput label, .stTextArea label, .stSelectbox label {
            font-size: 13px;
            margin-bottom: 2px; /* Reduced margin */
        }

        /* Add some custom spacing to the fields and make labels align properly */
        .stForm div {
            display: flex;
            flex-wrap: wrap;
        }

        /* Adjust fields layout for smaller screens */
        @media (max-width: 768px) {
            .stTextInput, .stTextArea, .stSelectbox {
                flex: 1 1 100%; /* Stack the fields in one column on smaller screens */
            }
        }
    </style>
""", unsafe_allow_html=True)


DATABASE_URL = 'sqlite:///dataQatables.db'
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(bind=engine))
db_session = SessionLocal()



def add_user_form():
    st.subheader("Add User")

    # Input fields
    username = st.text_input("Username", placeholder="Enter a unique username")
    password = st.text_input("Password", type="password", placeholder="Enter a strong password")
    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter the password")
    full_name = st.text_input("Full Name", placeholder="Enter the user's full name")
    email_id = st.text_input("Email", placeholder="Enter the user's email address")

    # Fetch options for dropdowns
    countries = db_session.query(countryIT).all()
    cities = db_session.query(cityIT).all()
    projects = db_session.query(projectIT).all()
    plans = db_session.query(planIT).all()
    roles = db_session.query(Role).all()

    # Dropdowns for foreign key fields
    country_id = st.selectbox("Country", options=[""] + [country.name for country in countries])
    city_id = st.selectbox("City", options=[""] + [city.name for city in cities])
    project_id = st.selectbox("Project", options=[""] + [project.name for project in projects])
    plan_id = st.selectbox("Plan", options=[""] + [plan.name for plan in plans])
    role_id = st.selectbox("Role", options=[""] + [role.name for role in roles])

    if st.button("✅ Add User"):
        # Validation
        if not username.strip():
            st.error("🚨 Username is required!")
            return
        if not password.strip():
            st.error("🚨 Password is required!")
            return
        if password != confirm_password:
            st.error("🚨 Passwords do not match!")
            return
        if not full_name.strip():
            st.error("🚨 Full Name is required!")
            return
        if not email_id.strip():
            st.error("🚨 Email is required!")
            return
        if not country_id or not city_id or not role_id:
            st.error("🚨 Country, City, and Role are required!")
            return

        # Check if username or email already exists
        if db_session.query(User).filter_by(username=username).first():
            st.error("🚨 Username already exists!")
            return
        if db_session.query(User).filter_by(email_id=email_id).first():
            st.error("🚨 Email already exists!")
            return

        # Fetch IDs for foreign key fields
        selected_country = db_session.query(countryIT).filter_by(name=country_id).first()
        selected_city = db_session.query(cityIT).filter_by(name=city_id).first()
        selected_project = db_session.query(projectIT).filter_by(name=project_id).first() if project_id else None
        selected_plan = db_session.query(planIT).filter_by(name=plan_id).first() if plan_id else None
        selected_role = db_session.query(Role).filter_by(name=role_id).first()

        if not selected_country or not selected_city or not selected_role:
            st.error("🚨 Invalid selection!")
            return
        
        created_by=st.session_state.username

        # 🔥 Generate Sequential Code AFTER Validation 🔥
        user_code = generate_sequential_code(db_session, created_by)

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create new user
        new_user = User(
            code=user_code,  # Assign generated code
            username=username,
            password=hashed_password,
            full_name=full_name,
            email_id=email_id,
            country_id=selected_country.id,
            city_id=selected_city.id,
            project_id=selected_project.id if selected_project else None,
            plan_id=selected_plan.id if selected_plan else None,
            role_id=selected_role.id,
        )

        try:
            db_session.add(new_user)
            db_session.commit()
            st.success(f"✅ User '{username}' added successfully! Code: {user_code}")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            db_session.rollback()
            st.error(f"❌ Error adding user: {e}")
        finally:
            db_session.close()


# Initialize cookie manager
cookies = EncryptedCookieManager(prefix="auth_session_", password=SECRET_KEY)
if not cookies.ready():
    st.stop()


# --- Read Cookies Before Session Reset ---
auth_token = cookies.get("auth_token")


# Ensure session state variables exist
if "username" not in st.session_state:
    st.session_state.username = None
if "password" not in st.session_state:
    st.session_state.password = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Function to update session state when autofill occurs
def update_username():
    st.session_state.username = st.session_state.input_username

def update_password():
    st.session_state.password = st.session_state.input_password


# Restore authentication from cookies if available
if auth_token and not st.session_state.logged_in:
    try:
        payload = jwt.decode(auth_token, SECRET_KEY, algorithms=["HS256"])
        st.session_state.logged_in = True
        st.session_state.username = payload["username"]
        st.session_state.role = payload["role"]
    except jwt.ExpiredSignatureError:
        cookies.delete("auth_token")  # Remove expired token
        st.session_state.logged_in = False
    except jwt.InvalidTokenError:
        st.session_state.logged_in = False




def generate_token(username, role):
    """Generate a secure JWT token."""
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=1)  # Token expires in 24 hours
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# --- Function to Decode Token ---
def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["username"], payload["role"], None
    except jwt.ExpiredSignatureError:
        return None, None, "⚠️ Session expired. Please log in again."
    except jwt.InvalidTokenError:
        return None, None, "⚠️ Invalid session. Please log in again."

    return None, None, None





# Function to authenticate user
def authenticate_user(username, password):
    """Authenticate user and return role if valid."""
    try:
        user = db_session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            return user.role.name  # Return role name if password is correct
        else:
            st.sidebar.error("❌ Invalid username or password")
    except Exception as e:
        st.sidebar.error(f"❌ Error during authentication: {e}")
    finally:
        db_session.close()
    return None

# --- Login Function ---
def login():
    st.sidebar.subheader("🔐 Login")

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")

    if login_button:

        role = authenticate_user(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role

            auth_token = generate_token(username, role)
            cookies["auth_token"] = auth_token
            cookies.save()

            st.sidebar.success(f"Logged in successfully!")
            time.sleep(1)
            st.rerun()




# --- Logout Function ---
def logout():
    # Clear the authentication token from cookies
    cookies["auth_token"] = ""  # Set to empty string
    cookies.save()  # Save changes

    # Reset session state
    st.session_state.clear()

    time.sleep(1)
    st.rerun()




def show_loader(duration=3, message="⏳ Loading..."):
    """
    Display a persistent loading spinner with a custom message.

    Parameters:
    - duration (int): Time in seconds to show the loading message.
    - message (str): The message to display during loading.
    """
    loading_html = f"""
    <style>
        .loading-spinner {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 24px;
            font-weight: bold;
            color: Black;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
            z-index: 9999;
        }}
    </style>
    <div class="loading-spinner">{message}</div>
    """

    # Display the loading spinner
    spinner_container = st.empty()
    spinner_container.markdown(loading_html, unsafe_allow_html=True)

    # Simulate loading time
    time.sleep(duration)

    # Remove spinner after loading is done
    spinner_container.empty()




def get_user_data(username):
    with SessionLocal() as session:
        return {
            "test_cases": session.query(TestCase).filter_by(created_by=username).all(),
            "tasks": session.query(ToDoList).filter_by(created_by=username).all(),
            "privileges": session.query(User).filter_by(username=username).all(),
            "attachments": session.query(Attachments).filter_by(created_by=username).all(),
            "plans": session.query(planIT).filter_by(created_by=username).all(),
            "projects": session.query(projectIT).filter_by(created_by=username).all(),
        }

# Store user data in session state to prevent multiple DB queries
if "user_data" not in st.session_state:
    st.session_state.user_data = get_user_data(st.session_state.username)



# Function to load tasks from DB
def load_tasks():
    return pd.DataFrame([task.__dict__ for task in db_session.query(ToDoList).all()])


# Function to delete tasks
def delete_task(task_ids):
    db_session.query(ToDoList).filter(ToDoList.id.in_(task_ids)).delete(synchronize_session=False)
    db_session.commit()


# Function to display task list in a professional table with checkboxes and save edits
def display_task_list():
    st.subheader("Tasks List")


    # Fetch only the logged-in user's tasks
    user_tasks = get_user_data(st.session_state.username)["tasks"]

    if user_tasks:
        # Convert to DataFrame
        tasks_df = pd.DataFrame([t.__dict__ for t in user_tasks])
        tasks_df.drop(columns=['_sa_instance_state'], inplace=True)  # Remove SQLAlchemy metadata



    if not tasks_df.empty:
        # Convert 'Start Date' & 'End Date' to readable format
        tasks_df["start_date"] = tasks_df["start_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        tasks_df["end_date"] = tasks_df["end_date"].apply(lambda x: x.strftime("%Y-%m-%d"))

        # Convert 'Ongoing' column to integer (avoid checkbox rendering)
        tasks_df["ongoing"] = tasks_df["ongoing"].astype(int)

        # Add checkbox column for selection
        tasks_df["Select"] = False  # Default to unchecked

        # Create "Select All" checkbox
        select_all = st.checkbox("Select All Tasks", key="select_all")

        # Update all checkboxes based on "Select All"
        if select_all:
            tasks_df["Select"] = True  # Mark all as selected

        # Display the table with editable fields
        edited_df = st.data_editor(
            tasks_df[
                [
                    "Select",
                    "id",  # Hidden in UI but required for database updates
                    "project",
                    "tasks_assigned",
                    "description",
                    "build_version",
                    "priority",
                    "severity",
                    "start_date",
                    "end_date",
                    "status",
                    "time_spent_min",
                    "test_cases",
                    "defects_count",
                    "fixed",
                    "need_to_fix_remaining",
                    "pass_count",
                    "ongoing",
                    "time_spent_per_case_min",
                ]
            ],
            column_config={
                "Select": st.column_config.CheckboxColumn("✔️ Select"),
                "ongoing": st.column_config.NumberColumn("Ongoing", help="Number of ongoing tasks"),
            },
            disabled=["id", "start_date", "end_date"],  # Prevent edits for specific columns
            num_rows="fixed",
            height=400,
        )

        # Extract selected task IDs for deletion
        selected_task_ids = edited_df.loc[edited_df["Select"], "id"].tolist()

        # Button to save changes
        if st.button("💾 Save Changes"):
            for index, row in edited_df.iterrows():
                update_task(
                    row["id"],  # Primary Key
                    {
                        "project": row["project"],
                        "tasks_assigned": row["tasks_assigned"],
                        "description": row["description"],
                        "build_version": row["build_version"],
                        "priority": row["priority"],
                        "severity": row["severity"],
                        "status": row["status"],
                        "time_spent_min": row["time_spent_min"],
                        "test_cases": row["test_cases"],
                        "defects_count": row["defects_count"],
                        "fixed": row["fixed"],
                        "need_to_fix_remaining": row["need_to_fix_remaining"],
                        "pass_count": row["pass_count"],
                        "ongoing": row["ongoing"],
                        "time_spent_per_case_min": row["time_spent_per_case_min"],
                    }
                )
            st.success("✅ Changes saved successfully!")
            time.sleep(1)
            st.rerun()  # Refresh page to reflect updates

        # Delete Button
        if selected_task_ids:
            if st.button("🗑️ Delete Selected Tasks"):
                delete_task(selected_task_ids)
                st.warning("🚨 Selected tasks deleted!")
                st.rerun()

    else:
        st.info("No tasks uploaded yet.")



# Function to update a task
def update_task(task_id, updates):
    task = db_session.query(ToDoList).filter_by(id=task_id).first()
    if task:
        for field, value in updates.items():
            setattr(task, field, value)  # Dynamically update fields
        db_session.commit()
        st.success(f"✅ Task {task_id} updated successfully!")

# Function to update a task
def update_test_case(task_id, updates):
    task = db_session.query(TestCase).filter_by(id=task_id).first()
    if task:
        for field, value in updates.items():
            setattr(task, field, value)  # Dynamically update fields
        db_session.commit()
        st.success(f"✅ Task {task_id} updated successfully!")



# Function to process and store data
def process_uploaded_file(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)

        # ✅ Fill missing values
        df.fillna({
            'Build Version': 'N/A',
            'Priority': '-',
            'Severity': '-',
            'Start Date': datetime.today().date(),
            'End Date': datetime.today().date(),
            'Time Spent (Min)': 0,
            'Test Cases': 0,
            'Defects Count': 0,
            'Fixed': 0,
            'Need to Fix (Remaining)': 0,
            'Pass Count': 0,
            'Ongoing': 0,
            'Time Spent Per Case (Min)': 0.00
        }, inplace=True)

        # ✅ Convert date columns
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce').dt.date
        df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce').dt.date

        # Database session
        Session = sessionmaker(bind=engine)
        db_session = Session()

        # ✅ Insert data into the database
        for _, row in df.iterrows():
            db_session.add(ToDoList(
                project=row.get('Project', "N/A"),
                tasks_assigned=row.get('Tasks Assigned', "N/A"),
                description=row.get('Description', "N/A"),
                build_version=row.get('Build Version', "N/A"),
                priority=row.get('Priority', "N/A"),
                severity=row.get('Severity', "N/A"),
                start_date=row['Start Date'] if pd.notna(row['Start Date']) else datetime.today().date(),
                end_date=row['End Date'] if pd.notna(row['End Date']) else datetime.today().date(),
                status=row.get('Status', "N/A"),
                time_spent_min=int(row.get('Time Spent (Min)', 0)),
                test_cases=int(row.get('Test Cases', 0)),
                defects_count=int(row.get('Defects Count', 0)),
                fixed=int(row.get('Fixed', 0)),
                need_to_fix_remaining=int(row.get('Need to Fix (Remaining)', 0)),
                pass_count=int(row.get('Pass Count', 0)),
                ongoing=str(row.get('Ongoing', "False")).strip().lower() in ['yes', 'true', '1'],
                time_spent_per_case_min=float(row.get('Time Spent Per Case (Min)', 0.00)),
                created_by=st.session_state.username  
            ))

        db_session.commit()
        db_session.close()

        # ✅ Show success message and refresh page automatically
        st.success("✅ Tasks uploaded successfully!")
        #time.sleep(2)
        #st.rerun()

    except Exception as e:
        db_session.rollback()
        st.error(f"❌ Error processing file: {str(e)}")

# Function to handle file uploads
def upload_sheet():
    st.subheader("📂 Upload CSV or Excel")
    
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    
    if uploaded_file:
        process_uploaded_file(uploaded_file)  # Process the file immediately





# Initialize session state for modal control
if "show_add_test_case" not in st.session_state:
    st.session_state.show_add_test_case = False

def toggle_modal():
    """Toggles the test case form visibility."""
    st.session_state.show_add_test_case = not st.session_state.show_add_test_case




def generate_test_case_sentence(test_scenario, field_parent, field_child, detailed_input, add_urdu=False):
    """Generates a structured sentence with auto-prepositions and optional Urdu translation."""
    
    prepositions = ["using", "in", "on", "with", "for", "by"]
    preposition1 = random.choice(prepositions)  
    preposition2 = random.choice(prepositions)  

    sentence = f"{test_scenario} {preposition1} {field_parent} {preposition2} {field_child}. {detailed_input}."
    
    if add_urdu:
        try:
            urdu_translation = GoogleTranslator(source="auto", target="ur").translate(sentence)
            return f"{sentence}\n\n {urdu_translation}"
        except Exception as e:
            return f"{sentence}\n\n Urdu translation not available."
    else:
        return sentence





def add_test_case():
    st.session_state.show_add_test_case = True
    st.subheader("📤 Add Test Case")


    # Initialize session state for test_case_id
    if "test_case_id" not in st.session_state:
        st.session_state.test_case_id = None

    # Fetch tasks from the database
    tasks = db_session.query(ToDoList).all()
    task_options = {task.description: task for task in tasks}

    if not task_options:
        st.error("⚠️ No tasks available. Add tasks before creating test cases.")
        return

    # Create columns for layout
    col1, col2 = st.columns([3, 2])

    # Task Selection Dropdown
    with col1:
        selected_task_name = st.selectbox("Select Task", options=[""] + list(task_options.keys()))

    if not selected_task_name:
        st.error("⚠️ Please select a task.")
        return

    # Fetch selected task details
    selected_task = task_options[selected_task_name]
    task_id = selected_task.tasks_assigned
    build_version = selected_task.build_version
    project = selected_task.project

    # Fetch existing scenarios for the selected task
    existing_cases = (
        db_session.query(TestCase.test_scenario, TestCase.expected_result, TestCase.test_case_id)
        .filter(TestCase.task_id == task_id)
        .order_by(TestCase.test_case_id)
        .all()
    )

    # Prepare scenario options
    scenario_options = []
    seen = set()

    for scenario, expected_result, case_id in existing_cases:
        sanitized_scenario = scenario.strip() if scenario else ""
        sanitized_expected_result = expected_result.strip() if expected_result else ""
        option_value = f"{case_id} | {sanitized_scenario} | {sanitized_expected_result}"

        if option_value not in seen:
            seen.add(option_value)
            scenario_options.append(option_value)

    # Scenario Selection Dropdown
    with col1:
        selected_scenario = st.selectbox("Select Test Scenario", options=[""] + scenario_options)

    if selected_scenario:
        selected_scenario_parts = selected_scenario.split(" | ")
        test_case_id = selected_scenario_parts[0] if len(selected_scenario_parts) > 0 else ""
        selected_scenario_clean = selected_scenario_parts[1] if len(selected_scenario_parts) > 1 else ""
        expected_result = selected_scenario_parts[2] if len(selected_scenario_parts) > 2 else ""
    else:
        test_case_id = ""
        selected_scenario_clean = ""
        expected_result = ""

    if not selected_scenario_clean:
        st.error("🚨 Test Scenario is required to proceed!")
        return

    # Store test_case_id in session state
    st.session_state.test_case_id = test_case_id

    # TS# and TC# logic
    ts_number = 1
    tc_number = 1
    scenario_exists = False
    expectation_exists = False
    duplicated_case_found = False

    for case in existing_cases:
        match = re.search(r"-TS# (\d+)-TC# (\d+)", case.test_case_id)
        if match:
            existing_ts = int(match.group(1))
            existing_tc = int(match.group(2))

            if case.test_scenario == selected_scenario_clean:
                scenario_exists = True
                ts_number = existing_ts

                if case.expected_result == expected_result:
                    expectation_exists = True
                    tc_number = existing_tc
                else:
                    tc_number = existing_tc + 1

                if existing_ts == ts_number and existing_tc == tc_number:
                    duplicated_case_found = True
                    break

    if not scenario_exists:
        last_ts = int(existing_cases[-1].test_case_id.split("-TS# ")[1].split("-")[0]) if existing_cases else 0
        ts_number = last_ts + 1
        tc_number = 1


    # Generate Test Case ID
    timestamp = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
    test_case_id = f"{task_id}-{build_version}-{project}-TS# {ts_number}-TC# {tc_number}-{timestamp}"

    # Input Fields
    with col2:
        field_parent = st.text_input("Field Name / Parent", value="")
        field_child = st.text_input("Field Name / Child", value="")
        detailed_input = st.text_area("Detailed Input", value="")
        add_urdu_translation = st.checkbox("Include Urdu Translation", value=False)
        
    # Auto-fill Test Cases Field (English + Optional Urdu)
    with col1:
        test_cases = generate_test_case_sentence(selected_scenario_clean, field_parent, field_child, detailed_input, add_urdu_translation)
        test_cases_field = st.text_area("Test Cases (Auto-generated)", value=test_cases, disabled=True)        

    with col1:
        show_advanced_fields = st.checkbox("Show Additional Fields", value=False)

    if show_advanced_fields:
        with col1:
            pre_condition = st.text_area("Pre-Condition")
            test_steps = st.text_area("Test Steps")
            test_data = st.text_area("Test Data")
            post_condition = st.text_area("Post Condition")
    else:
        pre_condition = test_steps = test_data = post_condition = ""

    # Actual Result and Status Logic
    actual_result_options = {
        "Positive": "Positive. The result is found as was expected.",
        "Positive Now": "Positive Now. Issue was fixed successfully.",
        "Negative": "Negative. The result is not as expected.",
        "Not Fixed": "Not Fixed. The issue still exists after re-testing.",
        "Ongoing": "Ongoing. The testing process is still in progress.",
        "Ignored": "Ignored. The issue was discussed but not fixed."
    }

    def determine_status(actual_result_key):
        status_map = {
            "Positive Now": "Pass (fixed)",
            "Negative": "Fail",
            "Positive": "Pass",
            "Not Fixed": "Fail (Re-tested)",
            "Ongoing": "Test Ongoing...",
            "Ignored": "Pass (discussed not fixed)"
        }
        return status_map.get(actual_result_key, "Need to Fix")

    with col1:
        actual_result_key = st.selectbox("Actual Result", [""] + list(actual_result_options.keys()))

    actual_result_description = actual_result_options.get(actual_result_key, "")
    status = determine_status(actual_result_key)

    with col1:
        status = st.selectbox("Status", [
            "Pass", "Fail", "Pass (fixed)", "Fail (Re-tested)",
            "Test Ongoing...", "Pass (discussed not fixed)", "Need to Fix"
        ], index=["Pass", "Fail", "Pass (fixed)", "Fail (Re-tested)", 
                  "Test Ongoing...", "Pass (discussed not fixed)", "Need to Fix"].index(status))

    # Save Test Case Button
    with col2:
        if st.button("✅ Save Test Case"):
            if not test_case_id.strip():
                st.error("🚨 Test Case ID cannot be empty!")
                return

            # Generate Test Cases
            test_cases = generate_test_case_sentence(
                selected_scenario_clean, field_parent, field_child, detailed_input, add_urdu_translation
            )

            # Create new TestCase entry
            new_test_case = TestCase(
                test_case_id=test_case_id,
                test_scenario=selected_scenario_clean,
                field_parent=field_parent,
                field_child=field_child,
                detailed_input=detailed_input,
                test_cases=f"{test_cases} | Test executed at: {timestamp}",
                pre_condition=pre_condition,
                test_steps=test_steps,
                test_data=test_data,
                post_condition=post_condition,
                expected_result=expected_result,
                actual_result=actual_result_description,
                status=status,
                task_id=task_id,
                build_version=build_version,
                created_by=st.session_state.username
            )

            try:
                db_session.add(new_test_case)
                db_session.commit()
                st.success(f"✅ Test case saved successfully with ID: {test_case_id}")
                time.sleep(1)
                st.session_state.show_add_test_case = False
                st.rerun()
            except Exception as e:
                db_session.rollback()
                st.error(f"❌ Error saving test case: {e}")



# Function to generate test case log ID
def generate_test_case_log(task_id, build_version, project, timestamp):
    # Log for test case creation/modification
    log_code = f"{task_id}-{build_version}-{project}-{timestamp}"
    return log_code

# Function to log modifications
def log_changes(test_case_id, task_assigned, action, modified_by="admin"):
    changes = f"Test case {test_case_id} {action}."
    new_log = ModifiedLog(
        code=test_case_id,
        tasks_assigned=task_assigned,
        modified_by=modified_by,
        modified_at=datetime.now(),
        changes=changes
    )
    db_session.add(new_log)
    db_session.commit()
    
    
    # Optional: Log the deletion event if needed
    # new_deletion_log = DeletedLog(
    #     code=test_case_id,
    #     tasks_assigned=task_assigned,
    #     deleted_by=modified_by,
    #     deleted_at=datetime.now()
    # )
    # db_session.add(new_deletion_log)
    # db_session.commit()



def upload_test_cases():
    st.subheader("📤 Upload Test Cases")
    
    # Fetch only the logged-in user's test cases
    user_cases = get_user_data(st.session_state.username)["test_cases"]

    if user_cases:
        # Convert to DataFrame
        test_cases = pd.DataFrame([t.__dict__ for t in user_cases])
        test_cases.drop(columns=['_sa_instance_state'], inplace=True)  # Remove SQLAlchemy metadata
    else:
        test_cases = pd.DataFrame()  # ✅ Always initialize as a DataFrame

    if test_cases.empty:  # ✅ Correct way to check for empty DataFrame
        st.info("No test cases uploaded yet.")

    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            # Load file based on format
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)

            # Fetch all tasks from DB for mapping
            tasks = {task.id: task for task in db_session.query(ToDoList).all()}

            new_test_cases = []  # Store valid cases for bulk insert

            for _, row in df.iterrows():
                test_case_id = str(row.get("Test Case ID", "")).strip()

                if not test_case_id:
                    st.warning("⚠️ Skipping row with empty Test Case ID.")
                    continue

                task_id = int(row["Task ID"]) if "Task ID" in row and not pd.isna(row["Task ID"]) else None

                if task_id not in tasks:
                    st.error(f"❌ Task ID {task_id} not found. Skipping row.")
                    continue

                # Auto-fill missing fields
                selected_task = tasks[task_id]
                build_version, project = selected_task.build_version, selected_task.project

                # Generate unique Test Case ID if missing
                if not test_case_id or test_case_id == "nan":
                    timestamp = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
                    test_case_id = f"{task_id}-{build_version}-{project}-{timestamp}"

                # Check for duplicate Test Case ID
                if db_session.query(TestCase).filter_by(test_case_id=test_case_id).first():
                    st.warning(f"⚠️ Skipping duplicate Test Case ID: {test_case_id}")
                    continue

                # Create new TestCase object
                new_case = TestCase(
                    test_case_id=test_case_id,
                    test_scenario=row.get("Test Scenario", ""),
                    field_parent=row.get("Field Name / Parent", ""),
                    field_child=row.get("Field Name / Child", ""),
                    detailed_input=row.get("Detailed Input", ""),
                    test_cases=row.get("Test Cases", ""),
                    pre_condition=row.get("Pre-Condition", ""),
                    test_steps=row.get("Test Steps", ""),
                    test_data=row.get("Test Data", ""),
                    post_condition=row.get("Post Condition", ""),
                    expected_result=row.get("Expected Result", ""),
                    actual_result=row.get("Actual Result", ""),
                    status=row.get("Status (Pass/Fail)", "Pending"),
                    task_id=task_id,
                    build_version=build_version,
                    created_by=st.session_state.username,
                )
                new_test_cases.append(new_case)

            if new_test_cases:
                db_session.bulk_save_objects(new_test_cases)  # ✅ Bulk insert for efficiency
                db_session.commit()
                st.success(f"✅ {len(new_test_cases)} test cases uploaded successfully!")
                st.rerun()
            else:
                st.warning("⚠️ No valid test cases found to upload.")

        except Exception as e:
            st.error(f"❌ Error processing file: {e}")






def test_cases_page():
    st.subheader("📝 Test Cases List")
    add_test_case()
    
def display_task_list():
    st.subheader("Tasks List")
    tasks_df = load_tasks()  # Fetch tasks from DB

    # ✅ Ensure tasks_df is always a DataFrame
    if tasks_df is None or tasks_df.empty:
        st.info("No tasks uploaded yet.")
        return  

    # Convert 'Start Date' & 'End Date' to readable format
    tasks_df["start_date"] = tasks_df["start_date"].apply(lambda x: x.strftime("%Y-%m-%d"))
    tasks_df["end_date"] = tasks_df["end_date"].apply(lambda x: x.strftime("%Y-%m-%d"))

    # Convert 'Ongoing' column to integer (avoid checkbox rendering)
    tasks_df["ongoing"] = tasks_df["ongoing"].astype(int)

    # Add checkbox column for selection
    tasks_df["Select"] = False  # Default to unchecked

    # Create "Select All" checkbox
    select_all = st.checkbox("Select All Tasks", key="select_all")

    # Update all checkboxes based on "Select All"
    if select_all:
        tasks_df["Select"] = True  # Mark all as selected

    # Display the table with editable fields
    edited_df = st.data_editor(
        tasks_df[
            [
                "Select",
                "id",  # Hidden in UI but required for database updates
                "project",
                "tasks_assigned",
                "description",
                "build_version",
                "priority",
                "severity",
                "start_date",
                "end_date",
                "status",
                "time_spent_min",
                "test_cases",
                "defects_count",
                "fixed",
                "need_to_fix_remaining",
                "pass_count",
                "ongoing",
                "time_spent_per_case_min",
            ]
        ],
        column_config={
            "Select": st.column_config.CheckboxColumn("✔️ Select"),
            "ongoing": st.column_config.NumberColumn("Ongoing", help="Number of ongoing tasks"),
        },
        disabled=["id", "start_date", "end_date"],  # Prevent edits for specific columns
        num_rows="fixed",
        height=400,
    )

    # Extract selected task IDs for deletion
    selected_task_ids = edited_df.loc[edited_df["Select"], "id"].tolist()

    # Button to save changes
    if st.button("💾 Save Changes"):
        for index, row in edited_df.iterrows():
            update_task(
                row["id"],  # Primary Key
                {
                    "project": row["project"],
                    "tasks_assigned": row["tasks_assigned"],
                    "description": row["description"],
                    "build_version": row["build_version"],
                    "priority": row["priority"],
                    "severity": row["severity"],
                    "status": row["status"],
                    "time_spent_min": row["time_spent_min"],
                    "test_cases": row["test_cases"],
                    "defects_count": row["defects_count"],
                    "fixed": row["fixed"],
                    "need_to_fix_remaining": row["need_to_fix_remaining"],
                    "pass_count": row["pass_count"],
                    "ongoing": row["ongoing"],
                    "time_spent_per_case_min": row["time_spent_per_case_min"],
                }
            )
        st.success("✅ Changes saved successfully!")
        time.sleep(1)
        st.rerun()  # Refresh page to reflect updates

    # Delete Button
    if selected_task_ids:
        if st.button("🗑️ Delete Selected Tasks"):
            delete_task(selected_task_ids)
            st.warning("🚨 Selected tasks deleted!")
            st.rerun()





def delete_test_cases(test_case_ids):
    db_session.query(TestCase).filter(TestCase.test_case_id.in_(test_case_ids)).delete(synchronize_session=False)
    db_session.commit()




def display_scenario_list():
    st.subheader("Test Scenarios")
    # Fetch distinct Task Assigned and Descriptions
    task_list = db_session.query(ToDoList.tasks_assigned.distinct()).all()
    desc_list = db_session.query(ToDoList.description.distinct()).all()

    # Convert to list of values
    task_options = [task[0] for task in task_list if task[0]]
    desc_options = [desc[0] for desc in desc_list if desc[0]]

    # Dropdowns for filtering
    selected_task = st.selectbox("Select Task", [""] + task_options)
    selected_desc = st.selectbox(" Or Select Description", [""] + desc_options)

    # Fetch only the relevant row
    query_stmt = db_session.query(
        ToDoList.tasks_assigned,
        ToDoList.project,
        ToDoList.description,
        ToDoList.build_version,
        ToDoList.status
    )

    if selected_task:
        query_stmt = query_stmt.filter(ToDoList.tasks_assigned == selected_task)
    if selected_desc:
        query_stmt = query_stmt.filter(ToDoList.description == selected_desc)

    task_data = query_stmt.first()  # Get only the first matching row

    if not task_data:
        st.warning("No matching task found.")
        return

    # Display selected task details
    df = pd.DataFrame([task_data], columns=["Task ID", "Project", "Description", "Build Version", "Task Assigned"])
    st.dataframe(df)

    # Input fields for test scenario
    test_scenario = st.text_area("Test Scenario")
    expected_result = st.text_area("Expected Result")

    if st.button("Save Test Case"):
        if not test_scenario.strip() or not expected_result.strip():
            st.error("Test Scenario and Expected Result cannot be empty!")
            return

        # Fetch existing test cases for the same task
        existing_cases = (
            db_session.query(TestCase)
            .filter(TestCase.task_id == task_data.tasks_assigned)
            .order_by(TestCase.test_case_id)
            .all()
        )

        # Initialize numbering
        ts_number = 1
        tc_number = 1
        scenario_exists = False
        expectation_exists = False
        duplicated_case_found = False

        for case in existing_cases:
            match = re.search(r"-TS# (\d+)-TC# (\d+)", case.test_case_id)  # Extract TS# & TC#
            if match:
                existing_ts = int(match.group(1))  # Extract TS#
                existing_tc = int(match.group(2))  # Extract TC#

                if case.test_scenario == test_scenario:
                    scenario_exists = True
                    ts_number = existing_ts  # Keep TS# same

                    if case.expected_result == expected_result:
                        expectation_exists = True
                        tc_number = existing_tc  # Keep TC# same
                    else:
                        tc_number = existing_tc + 1  # Increment TC# when expectation is different

                    # Check if the exact combination of TS# and TC# already exists
                    if existing_ts == ts_number and existing_tc == tc_number:
                        duplicated_case_found = True
                        break

        if not scenario_exists:
            last_ts = (
                int(existing_cases[-1].test_case_id.split("-TS# ")[1].split("-")[0])
                if existing_cases else 0
            )
            ts_number = last_ts + 1  # Increment TS# if new scenario
            tc_number = 1  # Reset TC# for a new scenario

        # If a duplicate test case is found
        if duplicated_case_found:
            st.error("Duplicated case found, Check it!")
            return

        # Generate unique Test Case ID
        timestamp = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
        test_case_id = f"{task_data.tasks_assigned}-{task_data.build_version}-{task_data.project}-TS# {ts_number}-TC# {tc_number}-{timestamp}"

        try:
            # Create and save test case
            new_test_case = TestCase(
                test_case_id=test_case_id,
                task_id=task_data.tasks_assigned,
                test_scenario=test_scenario,
                expected_result=expected_result,
                status="Pending",
                created_by=st.session_state.username 
            )

            db_session.add(new_test_case)
            db_session.commit()

            # Display success message for at least 1 second
            st.success(f"✅ Test Case {test_case_id} added successfully!")
            time.sleep(1)  # Wait for 1 second before rerunning UI

            st.rerun()
        except Exception as e:
            db_session.rollback()  # Rollback on failure
            st.error(f"Error: {str(e)}")



def display_test_cases():
    st.subheader("📌 List View")

    # Fetch only the logged-in user's test cases
    user_cases = get_user_data(st.session_state.username)["test_cases"]

    if user_cases:
        # Convert to DataFrame
        test_cases = pd.DataFrame([t.__dict__ for t in user_cases])
        test_cases.drop(columns=['_sa_instance_state'], inplace=True)  # Remove SQLAlchemy metadata
    else:
        test_cases = pd.DataFrame()  # Ensure it's always a DataFrame

    if test_cases.empty:  # ✅ Correct way to check if DataFrame is empty
        st.info("No test cases uploaded yet.")
        return

    # Convert to DataFrame for display
    df = pd.DataFrame(
        [
            {
                "id": case.id,  # Required for DB updates
                "Select": False,  # For selection
                "Test Case ID": case.test_case_id,
                "Test Scenario": case.test_scenario,
                "Field Name / Parent": case.field_parent,
                "Field Name / Child": case.field_child,
                "Detailed Input": case.detailed_input,
                "Test Cases": case.test_cases,
                "Pre-Condition": case.pre_condition,
                "Test Steps": case.test_steps,
                "Test Data": case.test_data,
                "Post Condition": case.post_condition,
                "Expected Result": case.expected_result,
                "Actual Result": case.actual_result,
                "Status": case.status,
                "Task ID": case.task_id,
                "Build Version": case.build_version,
            }
            for _, case in test_cases.iterrows()
        ]
    )

    # Session state to track changes
    if "edited_df" not in st.session_state:
        st.session_state.edited_df = df.copy()

    # Select All Checkbox
    select_all = st.checkbox("Select All")
    if select_all:
        df["Select"] = True

    # Display Editable Table
    edited_df = st.data_editor(df, 
        column_config={"Select": st.column_config.CheckboxColumn("✔️ Select")}
    )

    # Extract Selected IDs for Deletion
    selected_ids = edited_df.loc[edited_df["Select"], "id"].tolist()

    # ✅ Save Changes Button
    if st.button("💾 Save Changes"):
        update_dict = edited_df.set_index("id").to_dict(orient="index")

        for case_id, new_values in update_dict.items():
            test_case = db_session.query(TestCase).filter_by(id=case_id).first()
            if test_case:
                test_case.test_case_id = new_values["Test Case ID"]
                test_case.test_scenario = new_values["Test Scenario"]
                test_case.field_parent = new_values["Field Name / Parent"]
                test_case.field_child = new_values["Field Name / Child"]
                test_case.detailed_input = new_values["Detailed Input"]
                test_case.test_cases = new_values["Test Cases"]
                test_case.pre_condition = new_values["Pre-Condition"]
                test_case.test_steps = new_values["Test Steps"]
                test_case.test_data = new_values["Test Data"]
                test_case.post_condition = new_values["Post Condition"]
                test_case.expected_result = new_values["Expected Result"]
                test_case.actual_result = new_values["Actual Result"]
                test_case.status = new_values["Status"]
                test_case.task_id = new_values["Task ID"]
                test_case.build_version = new_values["Build Version"]

        db_session.commit()  # ✅ Save all changes at once
        st.success("✅ Changes saved successfully!")
        time.sleep(1)
        st.rerun()

    # 🗑️ Delete Button
    if selected_ids:
        if st.button("🗑️ Delete Selected"):
            db_session.query(TestCase).filter(TestCase.id.in_(selected_ids)).delete(synchronize_session=False)
            db_session.commit()
            st.warning("🚨 Selected test cases deleted!")
            st.rerun()




# Custom CSS for better UI
st.markdown(
    """
    <style>
    .stMultiSelect [data-baseweb=select] {
        min-width: 300px;  /* Adjust the width of multi-select dropdowns */
    }
    .stSelectbox [data-baseweb=select] {
        min-width: 300px;  /* Adjust the width of single-select dropdowns */
    }
    .stTextInput input {
        min-width: 300px;  /* Adjust the width of text input fields */
    }
    .stExpander {
        background-color: #f9f9f9;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 16px;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def log_modification(code, tasks_assigned, modified_by, changes):
    db_session = SessionLocal()
    try:
        log_entry = ModifiedLog(
            code=code,
            tasks_assigned=tasks_assigned,
            modified_by=modified_by,
            modified_at=datetime.utcnow(),
            changes=changes,
        )
        db_session.add(log_entry)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        st.error(f"Error logging modification: {e}")
    finally:
        db_session.close()

# Function to log deletions
def log_deletion(code, tasks_assigned, deleted_by):
    db_session = SessionLocal()
    try:
        log_entry = DeletedLog(
            code=code,
            tasks_assigned=tasks_assigned,
            modified_by=modified_by,
            modified_at=datetime.utcnow(),
            changes=changes,
        )
        db_session.add(log_entry)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        st.error(f"Error logging deletion: {e}")
    finally:
        db_session.close()


def log_creation(code, tasks_assigned, created_by, changes):
    db_session = SessionLocal()
    try:
        log_entry = CreationLog(
            code=code,
            tasks_assigned=tasks_assigned,
            created_by=created_by,
            created_at=datetime.utcnow(),
            changes=changes,
        )
        db_session.add(log_entry)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        st.error(f"Error logging creation: {e}")
    finally:
        db_session.close()


def directory_image():
    """Ensures upload directory exists and fetches dropdown options."""
    
    # Ensure directory exists
    UPLOAD_DIR = "attachments"
    os.makedirs(UPLOAD_DIR, exist_ok=True)  # ✅ Creates directory if missing

    # Fetch dropdown options
    projects = [p[0] for p in db_session.query(ToDoList.project).distinct().all()]
    tasks = [t[0] for t in db_session.query(ToDoList.description).distinct().all()]
    test_cases = db_session.query(TestCase).all()
    statuses = ["Open", "In Progress", "Closed"]  
    build_versions = [bv[0] for bv in db_session.query(TestCase.build_version).distinct().all()]

    # ✅ Handle empty test cases
    test_case_options = [tc.id for tc in test_cases] if test_cases else []
    test_case_format_func = lambda x: db_session.query(TestCase).filter_by(id=x).first().test_cases if test_cases else str(x)
    
    # Return all fetched data
    return UPLOAD_DIR, projects, tasks, test_case_options, statuses, build_versions, test_case_format_func



def handle_attachments():
    """Handles file uploads and displays existing attachments."""

    # ✅ Fetch dropdown values before using them
    UPLOAD_DIR, projects, tasks, test_case_options, statuses, build_versions, test_case_format_func = directory_image()

    # ✅ Check if upload was successful (for auto-refresh)
    if "upload_success" not in st.session_state:
        st.session_state.upload_success = False

    st.subheader("📤 Upload Files")

    # ✅ Prevent form submission if required dropdowns are empty
    if not (projects and tasks and test_case_options and build_versions):
        st.error("⚠️ Cannot upload files. Ensure projects, tasks, test cases, and build versions exist.")
        return  

    # ✅ Section 1: General Information
    project = st.selectbox("🔹 Select Project", options=projects)
    task_assigned = st.selectbox("🔹 Task Assigned", options=tasks)
    
    # ✅ Section 2: Test Case Details
    st.markdown("### Test Case Details")
    test_case_id = st.selectbox("🔹 Test Case", options=test_case_options, format_func=test_case_format_func)
    build_version = st.selectbox("🔹 Build Version", options=build_versions)
    
    # ✅ Section 3: Status Selection
    st.markdown("### Status")
    status = st.radio("Select Status", options=statuses, horizontal=True)  
    
    # ✅ Section 4: File Upload
    st.markdown("### 📂 Upload Files")
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=["jpg", "jpeg", "png", "bmp", "pdf", "mp4", "avi", "mov", "html", "rar"],
        accept_multiple_files=True,
    )


    # ✅ Submit Button
    st.markdown("---")

    # ✅ Handle file processing after form submission
    if st.button("💾 Upload"):
        if not uploaded_files:
            st.error("Please upload at least one file.")
        else:
            uploaded_file_paths = []  # Store uploaded file paths

            for index, uploaded_file in enumerate(uploaded_files):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{uploaded_file.name}")

                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                test_case_record = db_session.query(TestCase).filter_by(id=test_case_id).first()
                if not test_case_record:
                    st.error(f"Test case with ID {test_case_id} not found!")
                    return  

                test_case = test_case_record.test_cases if test_case_record.test_cases else "None"

                new_attachment = Attachments(
                    file_path=file_path,
                    project=project,
                    task_assigned=task_assigned,
                    test_case_id=test_case_id,
                    test_case=test_case,
                    status=status,
                    build_version=build_version,
                    timestamp=datetime.utcnow(),
                    created_by=st.session_state.username,
                )
                db_session.add(new_attachment)
                db_session.commit()

                uploaded_file_paths.append(file_path)  # Store file path for download

            # ✅ Update session state to trigger refresh
            st.session_state.upload_success = True
            st.rerun()


        # ✅ Reset upload success after showing downloads
        st.session_state.upload_success = False


                
    



def upload_image():
    """Displays uploaded files in an expandable section."""
    
    st.subheader("📂 Uploaded Files")
    attachments = db_session.query(Attachments).all()

    if not attachments:
        st.warning("No files uploaded yet.")
    else:
        for attachment in attachments:
            with st.expander(f"📄 Attachment: {os.path.basename(attachment.file_path)}"):
                # Display metadata
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Project:** {attachment.project}")
                    st.write(f"**Task Assigned:** {attachment.task_assigned}")
                    st.write(f"**User Name:** {attachment.created_by}")
                with col2:
                    st.write(f"**Test Case:** {attachment.test_case}")
                    st.write(f"**Status:** {attachment.status}")
                    st.write(f"**Build Version:** {attachment.build_version}")
                st.write(f"**Timestamp:** {attachment.timestamp}")

                # Display image or video preview
                file_ext = os.path.splitext(attachment.file_path)[1].lower()
                if file_ext in [".jpg", ".jpeg", ".png", ".bmp"]:
                    st.image(attachment.file_path, caption=attachment.test_case)
                elif file_ext == ".pdf":
                    st.write("📄 PDF files cannot be previewed. Please download the file.")
                elif file_ext in [".mp4", ".avi", ".mov"]:
                    st.video(attachment.file_path)

                # ✅ FIX: Ensuring unique key for each download button
                with open(attachment.file_path, "rb") as f:
                    st.download_button(
                        label=f"📥 Download {os.path.basename(attachment.file_path)}",
                        data=f,
                        file_name=os.path.basename(attachment.file_path),
                        mime="application/octet-stream",
                        key=f"download_{attachment.id}"  # 🔥 Unique key to avoid duplicate ID error
                    )

                # Delete button
                if st.button(f"❌ Delete {os.path.basename(attachment.file_path)}", key=f"delete_{attachment.id}"):
                    try:
                        # Delete the attachment from the database
                        db_session.delete(attachment)
                        db_session.commit()
                        st.success(f"Attachment '{os.path.basename(attachment.file_path)}' deleted successfully!")
                        st.rerun()  # ✅ More reliable than `experimental_rerun`
                    except Exception as e:
                        db_session.rollback()
                        st.error(f"Error deleting attachment: {e}")





# Current Page Session:





# --- Main Application ---
def main():
    # Check if the user is logged in
    if not st.session_state.get("logged_in", False):
        login()
    else:
        show_loader(duration=0.5, message="Loading...")
        # Display logout button and user info
        st.sidebar.write(f"Logged in as {st.session_state.username} ({st.session_state.role})")
        if st.sidebar.button("Logout", key="logout_button"):
            logout()

        # Sidebar navigation
        with st.sidebar:
            selected = option_menu(
                menu_title="Navigation",  # Sidebar title
                options=[
                    "Dashboard", 
                    "Review Test Cases", 
                    "Add User", 
                    "Add Country", 
                    "Add City", 
                    "Add Project", 
                    "Add Plan", 
                    "Add Role", 
                    "QA Tasks", 
                    "Scenarios", 
                    "Test Cases", 
                    "Attachments",
                    "Daily Syncup", 
                    "Minutes of Meeting", 
                    "QA Automation", 
                    "Logout", 
                    "Check Log"
                ],
                icons=[
                    "house", 
                    "file-earmark-text", 
                    "person-plus", 
                    "globe",  # Icon for Add Country
                    "building",  # Icon for Add City
                    "folder",  # Icon for Add Project
                    "clipboard",  # Icon for Add Plan
                    "person-badge",  # Icon for Add Role
                    "clipboard-data", 
                    "list-task", 
                    "clipboard-check",
                    "paperclip", 
                    "calendar-check", 
                    "file-earmark-text", 
                    "robot", 
                    "box-arrow-right", 
                    "list-task"
                ],
                menu_icon="cast",  # Sidebar main icon
                default_index=0,  # Default selected option
            )

        # Page Routing
        if selected == "Dashboard":
            st.write(f"Welcome, {st.session_state.username}!")   
            dashboard()

        elif selected == "Review Test Cases":            
            st.write(f"### Recent Activities by: {st.session_state.username}")

            user_test_cases = st.session_state.user_data["test_cases"]

            if user_test_cases:
                df = pd.DataFrame([t.__dict__ for t in user_test_cases])
                df.drop(columns=['_sa_instance_state'], inplace=True)  # Remove SQLAlchemy metadata
                st.dataframe(df)
            else:
                st.info("No test cases found for your account.")

        elif selected == "QA Tasks":
            display_task_list()
            upload_sheet()

        elif selected == "Scenarios":
            display_scenario_list()
            display_test_cases()

        elif selected == "Test Cases":
            test_cases_page()
            display_test_cases()
            upload_test_cases()

        elif selected == "Attachments":
            handle_attachments()
            upload_image()
            
        elif selected == "Add User":
            add_user_form()
            
        elif selected == "Daily Syncup":
            st.header("📅 Daily Sync-up Meeting")
            
        elif selected == "Minutes of Meeting":
            st.header("📝 Minutes of Meeting")
            
        elif selected == "QA Automation":
            if st.session_state.get("logged_in", False):
                qa_automation_page()
                display_test_cases()
            
        elif selected == "Check Log":
            st.subheader("Modification Logs")
            db_session = SessionLocal()
            modification_logs = db_session.query(ModifiedLog).all()
            if modification_logs:
                for log in modification_logs:
                    st.write(f"**Code:** {log.code}, **Tasks Assigned:** {log.tasks_assigned}, **Modified By:** {log.modified_by}, **Changes:** {log.changes}, **Modified At:** {log.modified_at}")
            else:
                st.warning("No modification logs found.")

            st.subheader("Deletion Logs")
            deletion_logs = db_session.query(DeletedLog).all()
            if deletion_logs:
                for log in deletion_logs:
                    st.write(f"**Code:** {log.code}, **Tasks Assigned:** {log.tasks_assigned}, **Deleted By:** {log.deleted_by}, **Deleted At:** {log.deleted_at}")
            else:
                st.warning("No deletion logs found.")

            db_session.close()

        elif selected == "Logout":
            logout()
            st.rerun()

# Run the main function
if __name__ == "__main__":
    main()
