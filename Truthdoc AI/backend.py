import os
import re
from urllib.parse import urlparse
from typing import List, Tuple

import docx
import pytesseract
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    import fitz
except Exception:
    fitz = None

try:
    from pdf2image import convert_from_path
except Exception:
    convert_from_path = None

# Set tesseract path on Windows when available.
DEFAULT_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(DEFAULT_TESSERACT):
    pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT

app = FastAPI(title="TruthDoc AI", description="Smart Document Fraud Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_text_from_image(file: UploadFile) -> str:
    try:
        image = Image.open(file.file)
        return pytesseract.image_to_string(image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing failed: {e}")


def extract_text_from_pdf(file: UploadFile) -> str:
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as f:
            f.write(file.file.read())

        # Try direct PDF text extraction first (no Poppler required).
        if PdfReader is not None:
            reader = PdfReader(temp_path)
            direct_text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
            if direct_text:
                return direct_text

        # Fallback to OCR using PyMuPDF rendering (does not require Poppler).
        if fitz is not None:
            doc = fitz.open(temp_path)

            # Try native text extraction from rendered document structure.
            fitz_text = "\n".join(page.get_text("text") for page in doc).strip()
            if fitz_text:
                doc.close()
                return fitz_text

            ocr_text = ""
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                mode = "RGB" if pix.n < 4 else "RGBA"
                image = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                ocr_text += pytesseract.image_to_string(image)
            doc.close()
            if ocr_text.strip():
                return ocr_text

        # Fallback to OCR for scanned/image-only PDFs when pdf2image is available.
        if convert_from_path is not None:
            try:
                pages = convert_from_path(temp_path)
                ocr_text = ""
                for page in pages:
                    ocr_text += pytesseract.image_to_string(page)
                if ocr_text.strip():
                    return ocr_text
            except Exception:
                pass

        raise HTTPException(
            status_code=400,
            detail=(
                "Could not extract readable text from this PDF. "
                "Try a clearer scan, a text-based PDF, or convert the file to image/DOCX and retry."
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF processing failed: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def extract_text_from_docx(file: UploadFile) -> str:
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as f:
            f.write(file.file.read())
        doc = docx.Document(temp_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DOCX processing failed: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def analyze_document(text: str) -> Tuple[str, int, List[str]]:
    flags: List[str] = []
    risk_score = 0

    if not re.search(r"(Dr\\.|Doctor|Company|Inc|Ltd|Registration\\s*No)", text, re.IGNORECASE):
        flags.append("Missing entity details (Doctor/Company/Registration Number)")
        risk_score += 20

    if re.search(r"common cold", text, re.IGNORECASE):
        match = re.search(r"(\\d+)\\s*days", text)
        if match and int(match.group(1)) > 5:
            flags.append("Unrealistic leave duration for minor illness")
            risk_score += 30

    suspicious_keywords = ["Sample", "Draft", "Specimen", "Confidential"]
    for keyword in suspicious_keywords:
        if re.search(keyword, text, re.IGNORECASE):
            flags.append(f"Contains suspicious keyword: {keyword}")
            risk_score += 25

    status = "Suspicious" if risk_score > 40 else "Genuine"
    return status, min(risk_score, 100), flags


def analyze_sms(text: str) -> Tuple[str, int, List[str]]:
    flags: List[str] = []
    risk_score = 0

    urgency_flags = ["Hurry up", "slots open", "limited time", "immediate joining"]
    platform_flags = ["Google Form", "WhatsApp only"]
    fraud_flags = ["Security deposit", "Pay for training", "No interview"]

    for keyword in urgency_flags + platform_flags:
        if re.search(keyword, text, re.IGNORECASE):
            flags.append(f"Urgency/Platform flag: {keyword}")
            risk_score += 25

    for keyword in fraud_flags:
        if re.search(keyword, text, re.IGNORECASE):
            flags.append(f"Fraud flag: {keyword}")
            risk_score += 30

    if re.search(r"https?://", text):
        flags.append("Contains suspicious URL")
        risk_score += 30

    status = "Suspicious" if risk_score > 40 else "Genuine"
    return status, min(risk_score, 100), flags


def analyze_link(raw_link: str) -> Tuple[str, int, List[str]]:
    flags: List[str] = []
    risk_score = 0

    parsed = urlparse(raw_link.strip())
    host = parsed.netloc.lower()
    path_and_query = f"{parsed.path} {parsed.query}".lower()

    if parsed.scheme not in {"http", "https"}:
        flags.append("Invalid URL scheme (must be http/https)")
        risk_score += 40

    if parsed.scheme == "http":
        flags.append("Insecure protocol: HTTP")
        risk_score += 20

    if re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", host):
        flags.append("Uses raw IP address instead of domain")
        risk_score += 25

    shorteners = ["bit.ly", "tinyurl.com", "t.co", "rb.gy", "goo.gl"]
    if any(s in host for s in shorteners):
        flags.append("Uses URL shortener")
        risk_score += 30

    risky_terms = ["login", "verify", "bank", "otp", "kyc", "password", "gift", "urgent"]
    for term in risky_terms:
        if term in path_and_query:
            flags.append(f"Suspicious keyword in URL: {term}")
            risk_score += 10

    if host.endswith((".xyz", ".top", ".click", ".work", ".gq")):
        flags.append("Potentially risky TLD")
        risk_score += 20

    if not host:
        flags.append("Missing domain in URL")
        risk_score += 40

    status = "Suspicious" if risk_score > 40 else "Genuine"
    return status, min(risk_score, 100), flags


class SMSInput(BaseModel):
    raw_text: str


class LinkInput(BaseModel):
    url: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/verify-document/")
async def verify_document(file: UploadFile = File(...)):
    try:
        filename_lower = file.filename.lower()
        if filename_lower.endswith((".png", ".jpg", ".jpeg")):
            text = extract_text_from_image(file)
        elif filename_lower.endswith(".pdf"):
            text = extract_text_from_pdf(file)
        elif filename_lower.endswith(".docx"):
            text = extract_text_from_docx(file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        status, risk_score, flags = analyze_document(text)
        return JSONResponse(
            content={
                "filename": file.filename,
                "status": status,
                "risk_score": risk_score,
                "reason_for_flag": flags,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {e}")


@app.post("/verify-sms/")
async def verify_sms(input_data: SMSInput):
    try:
        status, risk_score, flags = analyze_sms(input_data.raw_text)
        return JSONResponse(
            content={
                "filename": "raw_text_input",
                "status": status,
                "risk_score": risk_score,
                "reason_for_flag": flags,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMS verification failed: {e}")


@app.post("/verify-link/")
async def verify_link(input_data: LinkInput):
    try:
        status, risk_score, flags = analyze_link(input_data.url)
        return JSONResponse(
            content={
                "filename": "url_input",
                "status": status,
                "risk_score": risk_score,
                "reason_for_flag": flags,
                "url": input_data.url,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Link verification failed: {e}")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run("backend:app", host=host, port=port, reload=False)
