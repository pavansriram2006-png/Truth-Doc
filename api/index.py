import importlib.util
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR / "Truthdoc AI"
BACKEND_FILE = PROJECT_DIR / "backend.py"


# Load existing backend app from file path because project folder contains a space.
spec = importlib.util.spec_from_file_location("truthdoc_backend", str(BACKEND_FILE))
backend_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(backend_module)

app = backend_module.app

# Serve frontend assets and template from the existing project structure.
app.mount("/static", StaticFiles(directory=str(PROJECT_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(PROJECT_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Empty backend_url makes frontend call same-origin API routes on Vercel.
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "backend_url": "",
        },
    )
