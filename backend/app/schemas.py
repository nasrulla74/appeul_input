from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class InvoiceBase(BaseModel):
    filename: str

class InvoiceCreate(InvoiceBase):
    pass

class ExtractedData(BaseModel):
    customer_name: Optional[str] = None
    customer_tin: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    untaxed_amount: Optional[float] = None
    total_tax: Optional[float] = None
    invoice_total: Optional[float] = None
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_tin: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: int
    filename: str
    extracted_data: Optional[ExtractedData] = None
    status: str
    confidence: float
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class InvoiceListResponse(BaseModel):
    id: int
    filename: str
    status: str
    confidence: float
    invoice_number: Optional[str] = None
    customer_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    total_invoices: int
    completed_invoices: int
    failed_invoices: int
    average_confidence: float
    success_rate: float
    monthly_data: list
