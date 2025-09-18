from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import os

router = APIRouter()

# Example users (username: password)
USERS = {
    "admin": "1234",
    "staff1": "pass1",
    "staff2": "pass2"
}

@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return RedirectResponse(url="/static/login.html")

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in USERS and USERS[username] == password:
        request.session["user"] = username
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login?error=invalid", status_code=302)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

def require_login(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login", status_code=302)
    return request.session["user"]
