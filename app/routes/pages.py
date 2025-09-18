from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.templating import Jinja2Templates
import os

from .auth import require_login

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 👇 Root redirects to login
@router.get("/")
async def root():
    return RedirectResponse(url="/login", status_code=302)

# 👇 Secure dashboard
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, auth=Depends(require_login)):
    username = request.session.get("user")  # set at login
    return templates.TemplateResponse("dashboard.html", {"request": request, "username": username})