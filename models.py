from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError, OperationalError
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from functools import wraps
from flask import session, flash, redirect, url_for, render_template

defaultCode = "00001"
defaultId = 1


DATABASE_URL = 'sqlite:///dataQatables.db'
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(bind=engine))
db_session = SessionLocal()
Base = declarative_base()



# Define your models (TestCodeGeneration, Counter, User, etc.)
class TestCodeGeneration(Base):
    __tablename__ = "test_code_generation"
    
    id = Column(Integer, primary_key=True)
    created_by = Column(String, ForeignKey("user.username"), nullable=False)
    code_number = Column(String(6), nullable=False)
    qa_status = Column(String(10), nullable=False, default="Pending")

    user = relationship("User", back_populates="test_codes")

class Counter(Base):
    __tablename__ = "counter"
    
    id = Column(Integer, primary_key=True)
    last_code = Column(String(6), nullable=False, default="000000")


def validate_sequence(db_session, code_id: int):
    """
    Validates the sequence of codes in the TestCodeGeneration table and updates qa_status.
    
    Args:
        db_session: SQLAlchemy database session.
        code_id (int): ID of the newly inserted code.
    """
    # Fetch all codes from the TestCodeGeneration table
    codes = db_session.query(TestCodeGeneration.code_number).order_by(TestCodeGeneration.code_number).all()
    code_list = [int(code[0]) for code in codes]
    
    # Check for duplicates
    has_duplicates = len(code_list) != len(set(code_list))
    
    # Check for missing codes
    expected_codes = set(range(1, max(code_list) + 1)) if code_list else set()
    missing_codes = expected_codes - set(code_list)
    
    # Determine qa_status
    if has_duplicates or missing_codes:
        qa_status = "False"
    else:
        qa_status = "True"
    
    # Update the qa_status for the newly inserted code
    db_session.query(TestCodeGeneration).filter(TestCodeGeneration.id == code_id).update({"qa_status": qa_status})
    db_session.commit()

# Modify the generate_sequential_code function
def generate_sequential_code(db_session, created_by: str, max_retries: int = 5) -> str:
    """
    Generates a sequential 6-digit numeric code, logs it in TestCodeGeneration table,
    and validates the sequence.
    
    Args:
        db_session: SQLAlchemy database session.
        created_by (str): Username of the user generating the code.
        max_retries (int): Maximum number of retries if the database is locked.
    
    Returns:
        str: A 6-digit code as a string (e.g., "000001", "000002").
    """
    retries = 0
    while retries < max_retries:
        try:
            # Fetch or create the counter record
            counter = db_session.query(Counter).first()
            if not counter:
                counter = Counter(last_code="000000")
                db_session.add(counter)
                db_session.commit()
            
            # Increment the last code
            next_code = int(counter.last_code) + 1
            
            # Format the code as a 6-digit string with leading zeros
            next_code_str = f"{next_code:06}"
            
            # Log the generated code in TestCodeGeneration table
            test_code = TestCodeGeneration(
                created_by=created_by,
                code_number=next_code_str,
                qa_status="Pending"  # Default status
            )
            db_session.add(test_code)
            db_session.commit()
            
            # Update the counter
            counter.last_code = next_code_str
            db_session.commit()
            
            # Validate the sequence and update qa_status
            validate_sequence(db_session, test_code.id)
            
            return next_code_str
        except OperationalError as e:
            retries += 1
            print(f"Database is locked. Retrying ({retries}/{max_retries})...")
            time.sleep(0.1)  # Wait for 100ms before retrying
        except Exception as e:
            print(f"Error generating code: {e}")
            raise
    raise OperationalError("Failed to generate code after maximum retries.")


def update_counter(next_code_str):
    """
    Updates the counter only when the form submission is successful.
    """
    counter = db_session.query(Counter).first()
    if counter:
        counter.last_code = next_code_str
        db_session.commit()


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(300), nullable=False)
    code = Column(String(6), unique=True, nullable=False)
    full_name = Column(String(100), unique=True, nullable=False, default=defaultCode)
    email_id = Column(String(100), unique=True, nullable=False, default=defaultCode)
    
    country_id = Column(Integer, ForeignKey('country_it.id'), nullable=False, default=defaultId)
    city_id = Column(Integer, ForeignKey('city_it.id'), nullable=False, default=defaultId)
    project_id = Column(Integer, ForeignKey('project_it.id'), nullable=True, default=defaultId)
    plan_id = Column(Integer, ForeignKey('plan_it.id'), nullable=True, default=defaultId)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=False, default=defaultId)

    # ✅ Explicitly define the foreign key used in the relationship
    role = relationship("Role", foreign_keys=[role_id])  
    
    # Relationship with TestCodeGeneration
    test_codes = relationship("TestCodeGeneration", back_populates="user")  
    
    
    

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    
class countryIT(Base):
    __tablename__ = 'country_it'
    id = Column(Integer, primary_key=True)
    code = Column(String(6), unique=True, nullable=False)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(100), unique=True, nullable=False)
    created_by = Column(String, ForeignKey("user.username"), nullable=False)
    
    
class cityIT(Base):
    __tablename__ = 'city_it'
    id = Column(Integer, primary_key=True)
    code = Column(String(6), unique=True, nullable=False)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(100), unique=True, nullable=False)
    country_id = Column(Integer, ForeignKey('country_it.id'), nullable=False)
    created_by = Column(String, ForeignKey("user.username"), nullable=False)

class projectIT(Base):
    __tablename__ = 'project_it'
    id = Column(Integer, primary_key=True)
    code = Column(String(6), unique=True, nullable=False)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(100), unique=True, nullable=False)
    city_id = Column(Integer, ForeignKey('city_it.id'), nullable=False)
    created_by = Column(String, ForeignKey("user.username"), nullable=False)

class planIT(Base):
    __tablename__ = 'plan_it'
    id = Column(Integer, primary_key=True)
    code = Column(String(6), unique=True, nullable=False)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(100), unique=True, nullable=False)
    project_id = Column(Integer, ForeignKey('project_it.id'), nullable=False)
    created_by = Column(String, ForeignKey("user.username"), nullable=False)

class Role(Base):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True)
    code = Column(String(6), unique=True, nullable=False)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(100), unique=True, nullable=False)
    created_by = Column(String, ForeignKey("user.username"), nullable=False)

class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True)
    code = Column(String(6), unique=True, nullable=False)
    comment_text = Column(String(500), nullable=False)
    username = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Chat(Base):
    __tablename__ = 'chat'
    id = Column(Integer, primary_key=True)
    code = Column(String(6), unique=True, nullable=False)
    sender_id = Column(Integer, nullable=False)
    receiver_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)

class StatusCount(Base):
    __tablename__ = 'status_count'
    id = Column(Integer, primary_key=True)
    code = Column(String(6), unique=True, nullable=False)
    task_assigned = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    count = Column(Integer, default=0)

class CreationLog(Base):
    __tablename__ = 'creation_log'
    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False, index=True)  # Added index
    tasks_assigned = Column(String(100), nullable=False)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # Added index
    changes = Column(Text, nullable=False)

class ModifiedLog(Base):
    __tablename__ = 'modified_log'
    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False, index=True)  # Added index
    tasks_assigned = Column(String(100), nullable=False)
    modified_by = Column(String(100), nullable=False)
    modified_at = Column(DateTime, default=datetime.utcnow, index=True)  # Added default and index
    changes = Column(Text, nullable=False)

class DeletedLog(Base):
    __tablename__ = 'deleted_log'
    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False, index=True)  # Added index
    tasks_assigned = Column(String(100), nullable=False)
    deleted_by = Column(String(100), nullable=False)
    deleted_at = Column(DateTime, default=datetime.utcnow, index=True)  # Added index
    changes = Column(Text, nullable=False)

class ToDoList(Base):
    __tablename__ = 'to_do_list'
    
    id = Column(Integer, primary_key=True)
    project = Column(String(100), nullable=False)
    tasks_assigned = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    build_version = Column(String(50), nullable=False)
    priority = Column(String(50), nullable=False)
    severity = Column(String(50), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)
    time_spent_min = Column(Integer, nullable=False)
    test_cases = Column(Integer, nullable=False)
    defects_count = Column(Integer, nullable=False)
    fixed = Column(Integer, nullable=False)
    need_to_fix_remaining = Column(Integer, nullable=False)
    pass_count = Column(Integer, nullable=False)
    ongoing = Column(Integer, nullable=False)
    time_spent_per_case_min = Column(Float, nullable=False)
    is_modified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_by = Column(String, ForeignKey("user.username"), nullable=False)
    
    # Rename relationship to avoid conflict
    test_case_list = relationship("TestCase", back_populates="task", cascade="all, delete")



class TestCase(Base):
    __tablename__ = "test_management"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_case_id = Column(String, unique=True, nullable=False)
    test_scenario = Column(String, nullable=True)
    field_parent = Column(String, nullable=True)
    field_child = Column(String, nullable=True)
    detailed_input = Column(Text, nullable=True)
    test_cases = Column(Text, nullable=True)
    pre_condition = Column(Text, nullable=True)
    test_steps = Column(Text, nullable=True)
    test_data = Column(Text, nullable=True)
    post_condition = Column(Text, nullable=True)
    expected_result = Column(Text, nullable=True)
    actual_result = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="Pending")
    
    task_id = Column(Integer, ForeignKey("to_do_list.id", ondelete="CASCADE"), nullable=False)
    build_version = Column(String, nullable=True)

    created_by = Column(String, ForeignKey("user.username", ondelete="SET NULL"), nullable=False)

    # Relationships
    attachments = relationship("Attachments", back_populates="test_case_rel", cascade="all, delete-orphan")
    task = relationship("ToDoList", back_populates="test_case_list")



class TaskHistory(Base):
    __tablename__ = 'task_history'
    id = Column(Integer, primary_key=True)
    code = Column(String(6), unique=True, nullable=False)
    tasks_assigned = Column(String(100), ForeignKey('to_do_list.tasks_assigned'), nullable=False)
    status = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Attachments(Base):
    __tablename__ = 'attachments'
    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False)  # Path to the uploaded file
    project = Column(String, nullable=False)  # Project name
    task_assigned = Column(String, nullable=False)  # Task assigned
    test_case_id = Column(Integer, ForeignKey('test_management.id'))  # Foreign key to TestCase
    test_case = Column(String, nullable=False)  # Test case name
    status = Column(String, nullable=False)  # Status of the task/test case
    build_version = Column(String, nullable=False)  # Build version
    timestamp = Column(DateTime, default=datetime.utcnow)  # Timestamp of upload
    created_by = Column(String, ForeignKey("user.username"), nullable=False)

    # Relationships
    test_case_rel = relationship("TestCase", back_populates="attachments")



def create_superadmin():
    """Creates a Superadmin user, ensuring first values from each table are used."""
    db = SessionLocal()
    
    try:
        if not db.query(User).filter_by(username="superadmin").first():
            # ✅ Ensure first available values or create new ones
            default_country = db.query(countryIT).first()
            if not default_country:
                default_country = countryIT(code="00001", name="Pakistan", description="Auto-generated", created_by="superadmin")
                db.add(default_country)
                db.commit()  # Commit to get ID

            default_city = db.query(cityIT).first()
            if not default_city:
                default_city = cityIT(code="00001", name="Karachi", description="Auto-generated", country_id=default_country.id, created_by="superadmin")
                db.add(default_city)
                db.commit()

            default_project = db.query(projectIT).first()
            if not default_project:
                default_project = projectIT(code="00001", name="IT", description="Auto-generated", city_id=default_city.id, created_by="superadmin")
                db.add(default_project)
                db.commit()

            default_plan = db.query(planIT).first()
            if not default_plan:
                default_plan = planIT(code="00001", name="QA", description="Auto-generated", project_id=default_project.id, created_by="superadmin")
                db.add(default_plan)
                db.commit()

            default_role = db.query(Role).first()
            if not default_role:
                default_role = Role(code="00001", name="SQA Engineer", description="Auto-generated", created_by="superadmin")
                db.add(default_role)
                db.commit()

            # ✅ Create Superadmin
            superadmin = User(
                username="superadmin",
                password=generate_password_hash("Welcome"),  
                code="00001",
                country_id=default_country.id,
                city_id=default_city.id,
                project_id=default_project.id,
                plan_id=default_plan.id,
                role_id=default_role.id
            )
            db.add(superadmin)
            db.commit()
            print("✅ Superadmin created successfully!")

    except IntegrityError as e:
        db.rollback()
        print(f"❌ Integrity Error: {e}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating superadmin: {e}")

    finally:
        db.close()


# --- Initialize Database ---
Base.metadata.create_all(engine)

# --- Run Superadmin Creation ---
create_superadmin()
