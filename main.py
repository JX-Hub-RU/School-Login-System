from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

# Create the FastAPI app
app = FastAPI()

# Define the SQLAlchemy database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./school.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for our SQLAlchemy models
Base = declarative_base()

# Define the Student model
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models for input validation
class StudentCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class StudentInDB(StudentCreate):
    hashed_password: str

# API endpoint for student registration
@app.post("/students/", response_model=StudentInDB)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.username == student.username).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_student = db.query(Student).filter(Student.email == student.email).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(student.password)
    db_student = Student(username=student.username, email=student.email, hashed_password=hashed_password)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# API endpoint for student login
@app.post("/login/")
def login(username: str, password: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.username == username).first()
    if not student or not pwd_context.verify(password, student.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    return {"message": "Login successful"}
