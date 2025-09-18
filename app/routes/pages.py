from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.templating import Jinja2Templates

from .auth import require_login  # 👈 make sure this import points to your auth.py

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ------------------------------
# Root → redirect to login
# ------------------------------
@router.get("/")
async def root():
    return RedirectResponse(url="/login", status_code=302)


# ------------------------------
# Dashboard (requires login)
# ------------------------------
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, auth=Depends(require_login)):
    username = request.session.get("user")  # set in auth.py on login
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "username": username}
    )


# ------------------------------
# Chat page (public)
# ------------------------------
@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})
