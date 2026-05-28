import os
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, func # Added func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# For MySQL, ensure your DATABASE_URL starts with mysql+pymysql://
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    password = Column(String(255))

class SensorData(Base):
    __tablename__ = "sensordata"
    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float, nullable=True)
    status = Column(String(50),nullable=True)
    trend = Column(String(50),nullable=True)
    ai_message = Column(String(255),nullable=True)
    # Use func.now() so the MySQL server handles the timestamp automatically
    created_at = Column(DateTime, server_default=func.now())

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)