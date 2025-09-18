from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
import os

from ..routes.auth import require_login  # 👈 import login check

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "..", "templates")


@router.get("/")
async def chat_page():
    return FileResponse(os.path.join(TEMPLATE_DIR, "chat.html"))


@router.get("/dashboard")
async def dashboard_page(request: Request, auth=Depends(require_login)):
    """Dashboard is only accessible if logged in."""
    return FileResponse(os.path.join(TEMPLATE_DIR, "dashboard.html"))
