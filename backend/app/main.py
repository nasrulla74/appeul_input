import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, invoices, users
from app import models
from app.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Invoice Extraction API")

cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/")
def root():
    return {"message": "Invoice Extraction API"}

@app.get("/health")
def health():
    return {"status": "healthy"}
