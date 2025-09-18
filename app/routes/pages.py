from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "..", "templates")

@router.get("/")
async def chat_page():
    return FileResponse(os.path.join(TEMPLATE_DIR, "chat.html"))

@router.get("/dashboard")
async def dashboard_page():
    return FileResponse(os.path.join(TEMPLATE_DIR, "dashboard.html"))
