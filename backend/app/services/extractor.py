import base64
import json
import os
from typing import Optional

def get_client():
    provider = os.getenv("AI_PROVIDER", "deepseek").lower()
    
    if provider == "deepseek":
        from openai import OpenAI
        return OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        ), "deepseek-chat"
    else:
        from openai import OpenAI
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY")), "gpt-4o"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

async def extract_invoice_data(filepath: str):
    try:
        with open(filepath, "rb") as f:
            file_content = f.read()
        
        if filepath.lower().endswith(".pdf"):
            import PyPDF2
            from io import BytesIO
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = "\n".join([page.extract_text() for page in pdf_reader.pages])
        else:
            base64_image = base64.b64encode(file_content).decode("utf-8")
            text = None
        
        prompt = """Extract the following fields from this invoice. Return ONLY a valid JSON object with these exact fields:
- customer_name: The customer's name
- customer_tin: The customer's Tax Identification Number
- invoice_number: The invoice number
- invoice_date: The invoice date
- untaxed_amount: The subtotal/untaxed amount (just the number)
- total_tax: The total tax amount (just the number)
- invoice_total: The total amount including tax (just the number)
- company_name: The company/seller name from the header
- company_address: The company address
- company_tin: The company's Tax Identification Number

If a field is not found, use null. Return ONLY valid JSON, no other text."""

        client, model = get_client()

        if filepath.lower().endswith(".pdf"):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting data from invoices."},
                    {"role": "user", "content": f"{prompt}\n\nInvoice text:\n{text[:8000]}"}
                ],
                temperature=0,
                max_tokens=2000
            )
        else:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting data from invoices."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}
                ],
                temperature=0,
                max_tokens=2000
            )
        
        content = response.choices[0].message.content
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        data = json.loads(content)
        
        confidence = 0.85
        
        return {
            "data": data,
            "confidence": confidence
        }
    except json.JSONDecodeError as e:
        return {
            "data": {},
            "confidence": 0.0
        }
    except Exception as e:
        raise Exception(f"Extraction failed: {str(e)}")
