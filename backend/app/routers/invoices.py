from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json
import io
import csv
from datetime import datetime
from .. import models, database, auth
from ..schemas import InvoiceResponse, InvoiceListResponse, ExtractedData

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff"}

def allowed_file(filename: str):
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

@router.post("/upload")
async def upload_invoices(
    files: List[UploadFile] = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    results = []
    for file in files:
        if not allowed_file(file.filename):
            results.append({"filename": file.filename, "status": "failed", "error": "Invalid file type"})
            continue
        
        filepath = f"backend/uploads/{current_user.id}_{datetime.now().timestamp()}_{file.filename}"
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        
        invoice = models.Invoice(
            filename=file.filename,
            filepath=filepath,
            owner_id=current_user.id,
            status="processing"
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        results.append({"id": invoice.id, "filename": file.filename, "status": "uploaded"})
    
    return {"results": results}

@router.get("", response_model=List[InvoiceListResponse])
def get_invoices(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    invoices = db.query(models.Invoice).filter(models.Invoice.owner_id == current_user.id).order_by(models.Invoice.created_at.desc()).all()
    results = []
    for inv in invoices:
        data = json.loads(inv.extracted_data) if inv.extracted_data else {}
        results.append(InvoiceListResponse(
            id=inv.id,
            filename=inv.filename,
            status=inv.status,
            confidence=inv.confidence,
            invoice_number=data.get("invoice_number"),
            customer_name=data.get("customer_name"),
            created_at=inv.created_at
        ))
    return results

@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id,
        models.Invoice.owner_id == current_user.id
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    extracted_data = None
    if invoice.extracted_data:
        extracted_data = json.loads(invoice.extracted_data)
        extracted_data = ExtractedData(**extracted_data)
    
    return InvoiceResponse(
        id=invoice.id,
        filename=invoice.filename,
        extracted_data=extracted_data,
        status=invoice.status,
        confidence=invoice.confidence,
        error_message=invoice.error_message,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at
    )

@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id,
        models.Invoice.owner_id == current_user.id
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted"}

@router.get("/export/csv")
def export_csv(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    invoices = db.query(models.Invoice).filter(
        models.Invoice.owner_id == current_user.id,
        models.Invoice.status == "completed"
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Customer Name", "Customer TIN", "Invoice Number", "Date", 
                     "Untaxed Amount", "Total Tax", "Total", "Company Name", 
                     "Company Address", "Company TIN", "Confidence", "Filename"])
    
    for inv in invoices:
        data = json.loads(inv.extracted_data) if inv.extracted_data else {}
        writer.writerow([
            data.get("customer_name", ""),
            data.get("customer_tin", ""),
            data.get("invoice_number", ""),
            data.get("invoice_date", ""),
            data.get("untaxed_amount", ""),
            data.get("total_tax", ""),
            data.get("invoice_total", ""),
            data.get("company_name", ""),
            data.get("company_address", ""),
            data.get("company_tin", ""),
            f"{inv.confidence * 100:.1f}%",
            inv.filename
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoices.csv"}
    )

@router.post("/process/{invoice_id}")
async def process_invoice(
    invoice_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    from ..services.extractor import extract_invoice_data
    
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id,
        models.Invoice.owner_id == current_user.id
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    try:
        result = await extract_invoice_data(invoice.filepath)
        invoice.extracted_data = json.dumps(result["data"])
        invoice.status = "completed"
        invoice.confidence = result["confidence"]
        invoice.updated_at = datetime.utcnow()
        db.commit()
        return {"status": "completed", "data": result["data"], "confidence": result["confidence"]}
    except Exception as e:
        invoice.status = "failed"
        invoice.error_message = str(e)
        db.commit()
        return {"status": "failed", "error": str(e)}
