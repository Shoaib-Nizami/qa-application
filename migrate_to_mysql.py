import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
import pymysql  

# ✅ Use Railway MySQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:qnigrFgytUVoIaHtjBsoyMpEOLsuEJTJ@interchange.proxy.rlwy.net:35251/railway"
)

# ✅ Create MySQL Engine
engine = create_engine(DATABASE_URL, echo=True)

# ✅ Session Management
SessionLocal = scoped_session(sessionmaker(bind=engine))
db_session = SessionLocal()

# ✅ Define Base for SQLAlchemy Models
Base = declarative_base()
