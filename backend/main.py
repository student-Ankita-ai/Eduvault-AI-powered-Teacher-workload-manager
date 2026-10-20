from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .database import engine, Base, get_db
from .models import StudentModel
from .schemas import StudentSchema

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EduVault AI Full-Stack Backend", version="1.0")

@app.get("/students", response_model=List[StudentSchema])
def get_all_students(db: Session = Depends(get_db)):
    students = db.query(StudentModel).all()
    if not students:
        demo_data = [
            StudentModel(roll_no=101, name="Rahul Kumar", aadhaar_status="Masked & Vaulted", bank_details="Verified", income_cert="Missing", overall_status="🟡 Action Required", pending_item="Income Certificate"),
            StudentModel(roll_no=102, name="Priya Sharma", aadhaar_status="Masked & Vaulted", bank_details="Verified", income_cert="Verified", overall_status="🟢 Fully Verified", pending_item="None"),
            StudentModel(roll_no=103, name="Amit Singh", aadhaar_status="Missing", bank_details="Missing", income_cert="Missing", overall_status="🔴 Critical Pending", pending_item="Aadhaar, Passbook, Income Cert"),
            StudentModel(roll_no=104, name="Neha Verma", aadhaar_status="Masked & Vaulted", bank_details="Verified", income_cert="Verified", overall_status="🟢 Fully Verified", pending_item="None"),
            StudentModel(roll_no=105, name="Vikas Meena", aadhaar_status="Masked & Vaulted", bank_details="Missing", income_cert="Missing", overall_status="🟡 Action Required", pending_item="Bank Passbook, Income Cert"),
        ]
        db.add_all(demo_data)
        db.commit()
        students = db.query(StudentModel).all()
    return students

@app.put("/students/{roll_no}/verify-document")
def verify_student_document(roll_no: int, doc_type: str, db: Session = Depends(get_db)):
    student = db.query(StudentModel).filter(StudentModel.roll_no == roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")
    
    if doc_type.lower() == "income":
        student.income_cert = "Verified"
    elif doc_type.lower() == "aadhaar":
        student.aadhaar_status = "Masked & Vaulted"
    elif doc_type.lower() == "bank":
        student.bank_details = "Verified"
        
    if student.aadhaar_status != "Missing" and student.bank_details == "Verified" and student.income_cert == "Verified":
        student.overall_status = "🟢 Fully Verified"
        student.pending_item = "None"
    else:
        student.overall_status = "🟡 Action Required"
        
    db.commit()
    db.refresh(student)
    return {"message": "Database record successfully updated!", "student": student}