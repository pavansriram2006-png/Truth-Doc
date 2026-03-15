# TruthDoc AI

TruthDoc AI is a local-first verification app for document, SMS/text, and URL risk screening.
It includes:

- FastAPI backend APIs for analysis
- FastAPI web frontend (Jinja + static assets)
- Optional Kivy desktop/mobile UI scripts

## Project Structure

- `Truthdoc AI/backend.py` : Core API and verification logic
- `Truthdoc AI/web_frontend.py` : Web frontend server
- `Truthdoc AI/templates/index.html` : Main UI template
- `Truthdoc AI/static/styles.css` : UI styles
- `Truthdoc AI/static/scripts.js` : Frontend behavior
- `Truthdoc AI/frontend.py` : Kivy desktop client
- `Truthdoc AI/mobile_app.py` : Kivy launcher

## Requirements

- Windows (or Linux/macOS)
- Python 3.12 recommended
- Tesseract OCR installed for image/scanned text OCR

Optional for scanned PDF OCR quality:
- Poppler (if using `pdf2image` conversion path)

## Quick Start (Web Mode)

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Start backend:

```powershell
Set-Location ".\Truthdoc AI"
..\.venv312\Scripts\python.exe .\backend.py
```

4. Start frontend in another terminal:

```powershell
Set-Location ".\Truthdoc AI"
..\.venv312\Scripts\python.exe .\web_frontend.py
```

5. Open in browser:

- http://127.0.0.1:8080/

## API Endpoints

- `GET /health`
- `POST /verify-document/`
- `POST /verify-sms/`
- `POST /verify-link/`

## Notes

- Default backend URL is `http://127.0.0.1:8000`.
- Frontend is served at `http://127.0.0.1:8080`.
- If a PDF has no extractable text and OCR cannot read it, convert to a clearer image/PDF or DOCX and retry.

## Deploy OCR Backend On Render

Use this when you want image/scanned PDF OCR to work from all devices.

Files added for deployment:

- `Dockerfile`
- `requirements-server.txt`
- `render.yaml`

### Steps

1. Push your latest code to GitHub.
2. In Render, create a new **Blueprint** and connect this repository.
3. Render will use `render.yaml` and build from `Dockerfile`.
4. After deploy, copy your Render backend URL (for example `https://truthdoc-ocr-backend.onrender.com`).
5. In Vercel project settings, add environment variable:

```text
BACKEND_URL=https://your-render-backend.onrender.com
```

6. Redeploy Vercel.

### CORS

- Backend CORS is controlled by `CORS_ALLOWED_ORIGINS`.
- Default includes `https://truth-doc.vercel.app` and localhost origins.
- To customize, set comma-separated origins in Render environment:

```text
CORS_ALLOWED_ORIGINS=https://truth-doc.vercel.app,https://your-other-frontend.vercel.app
```
