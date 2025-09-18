from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
import os

router = APIRouter()
security = HTTPBasic()

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "password")


# ---- Login Page ----
@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return """
    <html>
    <body style="font-family:sans-serif;">
      <h2>🔐 Admin Login</h2>
      <form action="/login" method="post">
        <input type="text" name="username" placeholder="Username"/><br><br>
        <input type="password" name="password" placeholder="Password"/><br><br>
        <button type="submit">Login</button>
      </form>
    </body>
    </html>
    """


# ---- Handle Login ----
@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(key="session", value="authenticated", httponly=True)
        return response
    return HTMLResponse("<h3>❌ Invalid credentials</h3>", status_code=401)


# ---- Handle Logout ----
@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session")
    return response


# ---- Dependency: Require Login ----
def require_login(request: Request):
    if request.cookies.get("session") != "authenticated":
        return RedirectResponse(url="/login", status_code=302)
