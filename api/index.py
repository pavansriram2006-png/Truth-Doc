import importlib.util
import os
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR / "Truthdoc AI"
BACKEND_FILE = PROJECT_DIR / "backend.py"
BACKEND_URL = os.getenv("BACKEND_URL", "").strip()


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
    # When BACKEND_URL is set (for example to Render), frontend calls that backend.
    # Otherwise it uses same-origin API routes.
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "backend_url": BACKEND_URL,
        },
    )
