from sqlalchemy import Column, Integer, String
from .database import Base

class StudentModel(Base):
    __tablename__ = "students"

    roll_no = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    aadhaar_status = Column(String, default="Missing")
    bank_details = Column(String, default="Missing")
    income_cert = Column(String, default="Missing")
    overall_status = Column(String, default="🔴 Critical Pending")
    pending_item = Column(String, default="All Documents Missing")