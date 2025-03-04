from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from pydantic import BaseModel, Field
from typing import List
from fastapi import FastAPI, HTTPException

Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    tests_taken = relationship("TestResult", back_populates="student")

class Test(Base):
    __tablename__ = 'tests'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    max_score = Column(Integer)

class TestResult(Base):
    __tablename__ = 'test_results'
    
    id = Column(Integer, primary_key=True, index=True)
    student_name = Test.name
    student_id = Column(Integer, ForeignKey('students.id'))
    test_id = Column(Integer, ForeignKey('tests.id'))
    score = Column(Integer)
    
    student = relationship("Student", back_populates="tests_taken")

class StudentCreate(BaseModel):
    id: int = Field(..., description="Student's ID", unique=True)
    name: str = Field(..., min_length=2, max_length=50, description="Student's full name")
    email: str = Field(..., description="Student's email address", unique=True)

class TestCreate(BaseModel):
    id: int = Field(..., description="ID of the test")
    name: str = Field(..., min_length=2, max_length=100, description="Name of the test")
    max_score: int = Field(..., description="Maximum possible score")

class TestResultCreate(BaseModel):
    student_id: int = Field(..., description="ID of the student taking the test")
    test_id: int = Field(..., description="ID of the test taken")
    score: int = Field(..., description="Score obtained in the test")

class ResponseMessage(BaseModel):
    message: str

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/students/", response_model=ResponseMessage)
def create_student(new_student: StudentCreate): 
    db = SessionLocal()
    db_student = Student(id=new_student.id ,name=new_student.name, email=new_student.email)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    db.close()
    return ResponseMessage(message="Student created successfully")

@app.get("/students/{student_id}", response_model=StudentCreate)
def get_student(student_id: int):
    db = SessionLocal()
    student = db.query(Student).filter(Student.id == student_id).first()
    db.close()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.get("/students/", response_model=List[StudentCreate])
def get_students():
    db = SessionLocal()
    students = db.query(Student).all()
    db.close()
    return students

@app.post("/tests/", response_model=ResponseMessage)
def create_test(new_test: TestCreate):
    db = SessionLocal()
    db_test = Test(id=new_test.id, name=new_test.name, max_score=new_test.max_score)
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    db.close()
    return ResponseMessage(message="Test created successfully")

@app.get("/tests/", response_model=List[TestCreate])
def get_all_tests():
    db = SessionLocal()
    tests = db.query(Test).all()
    db.close()
    return tests

@app.get("/tests/{test_id}", response_model=TestCreate)
def get_test(test_id: int):
    db = SessionLocal()
    test = db.query(Test).filter(Test.id == test_id).first()
    db.close()
    if test is None:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

@app.post("/test_results/", response_model=ResponseMessage)
def submit_test_results(new_test_result: TestResultCreate):
    db = SessionLocal()
    db_test_result = TestResult(student_id=new_test_result.student_id,
                                 test_id=new_test_result.test_id,
                                 score=new_test_result.score)
    db.add(db_test_result)
    db.commit()
    db.refresh(db_test_result)
    db.close()
    return ResponseMessage(message="Test result created successfully")

@app.get("/get_results/{test_id}", response_model=List[TestResultCreate])
def get_test_results(test_id: int):
    db = SessionLocal()
    test_results = db.query(TestResult).filter(TestResult.test_id == test_id).all()
    db.close()
    return test_results

@app.get("/students/{student_id}/test_results", response_model=List[TestResultCreate])
def get_student_test_results(student_id: int):
    db = SessionLocal()
    test_results = db.query(TestResult).filter(TestResult.student_id == student_id).all()
    db.close()
    return test_results

@app.get("/students/{test_id}/average_score", response_model=ResponseMessage)
def get_average_score(test_id: int):
    db = SessionLocal()
    test_results = db.query(TestResult).filter(TestResult.test_id == test_id).all()
    total_score = 0
    for test_result in test_results:
        total_score += test_result.score
    average_score = total_score / len(test_results)
    db.close()
    return ResponseMessage(message=f"Average score for test ID {test_id} is {average_score}")


@app.get("/highest_scorer{test_id}", response_model=StudentCreate)
def get_highest_scorer(test_id: int):
    db = SessionLocal()
    test_results = db.query(TestResult).filter(TestResult.test_id == test_id).all()
    highest_score = 0
    highest_scorer = None
    for test_result in test_results:
        if test_result.score > highest_score:
            highest_score = test_result.score
            highest_scorer = test_result.student
    db.close()
    return highest_scorer

@app.delete("/students/{student_id}", response_model=ResponseMessage)
def delete_student(student_id: int):
    db = SessionLocal()
    student = db.query(Student).filter(Student.id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    db.close()
    return ResponseMessage(message="Student deleted successfully")



