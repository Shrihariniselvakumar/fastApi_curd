from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from bson import ObjectId
from typing import Literal
from pymongo.errors import DuplicateKeyError

app = FastAPI()
client = MongoClient("mongodb://localhost:27017/")
db = client["college_db"]

students = db["students"]
students.create_index("rollno",unique=True)

class Student(BaseModel):
    name: str
    rollno: int
    age: int
    course: str
    status: Literal["active", "in-active"] = "active"

@app.get("/")
def home():
    client.admin.command("ping")
    return {"message": "MongoDB connected successfully!"}

@app.get("/students")
def get_students():
    student_list = []

    for student in students.find():
        student["_id"] = str(student["_id"])
        student_list.append(student)

    return student_list

@app.get("/students/{student_id}")
def get_student(student_id: str):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid student ID")

    student = students.find_one({"_id": ObjectId(student_id)})

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    student["_id"] = str(student["_id"])
    return student

@app.post("/students")
def create_student(student: Student):
    student_data = student.model_dump()

    try:
        result = students.insert_one(student_data)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Roll number already exists"
        )

    return {
        "message": "Student added successfully",
        "id": str(result.inserted_id)
    }
class StudentUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    course: str | None = None
    status: Literal["active", "in-active"] | None = None
    email:str | None = None

@app.put("/students/{rollno}")
def update_student(rollno: int, student: Student):
    existing_student = students.find_one({"rollno": rollno})

    if existing_student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
       )

    update_data = student.model_dump(exclude={"rollno"})

    students.update_one(
        {"rollno": rollno},
        {"$set": update_data}
    )

    return {"message": "Student updated successfully"}

@app.patch("/students/{rollno}")
def partial_update_student(rollno: int, student: StudentUpdate):
    existing_student = students.find_one({"rollno": rollno})

    if existing_student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    update_data = student.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one field to update"
        )

    students.update_one(
        {"rollno": rollno},
        {"$set": update_data}
    )

    return {
        "message": "Student updated successfully",
        "updated_fields": update_data
    }

@app.delete("/students/{rollno}")
def delete_student(rollno: int):
    student = students.find_one({"rollno": rollno})

    if student is None:
        raise HTTPException(
            status_code=404,
            detail=f"Student with roll number {rollno} not found"
        )

    students.update_one(
        {"rollno": rollno},
        {"$set": {"status": "in-active"}}
    )

    return {
        "message": "Student deactivated successfully",
        "rollno": rollno,
        "status": "in-active"
    }
    

    

