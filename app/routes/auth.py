from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.templating import Jinja2Templates
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import RedirectResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Simple login form page
@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Handle login POST
@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "1234":  # replace with real check
        request.session["user"] = username
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login?error=1", status_code=302)

# Logout
@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

# Dependency
from fastapi.responses import RedirectResponse

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi import Request, HTTPException

def require_login(request: Request):
    if "user" not in request.session:
        print("🚨 No user in session, redirecting")  # debug print
        raise HTTPException(
            status_code=303,
            detail="Redirect",
            headers={"Location": "/login"},
        )
    print("✅ User in session:", request.session["user"])  # debug print
    return request.session["user"]