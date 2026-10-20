from pydantic import BaseModel

class StudentSchema(BaseModel):
    roll_no: int
    name: str
    aadhaar_status: str
    bank_details: str
    income_cert: str
    overall_status: str
    pending_item: str

    class Config:
        from_attributes = True