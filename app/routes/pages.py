from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates   # 👈 add this
import os

from ..routes.auth import require_login  # 👈 import login check

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "..", "templates")

templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/")
async def chat_page():
    return FileResponse(os.path.join(TEMPLATE_DIR, "chat.html"))

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, auth=Depends(require_login)):
    username = request.session.get("user")  # comes from login
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "username": username}
    )
