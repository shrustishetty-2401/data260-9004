from datetime import datetime, timezone

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()

templates = Jinja2Templates(directory="code/templates")

SESSION_TIMEOUT_SECONDS = 900


USERS = {
    "student": {
        "password": "data260",
        "name": "Shrusti Shetty",
    }
}


def get_current_user(request: Request):
    username = request.session.get("username")

    if not username:
        return None

    last_activity = request.session.get("last_activity")
    now = datetime.now(timezone.utc).timestamp()

    if last_activity is None:
        request.session.clear()
        return None

    if now - last_activity > SESSION_TIMEOUT_SECONDS:
        request.session.clear()
        return None

    request.session["last_activity"] = now

    return USERS.get(username)


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = get_current_user(request)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "user": user,
        },
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": None,
        },
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    user = USERS.get(username)

    if user is None or user["password"] != password:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": "Invalid username or password.",
            },
            status_code=401,
        )

    request.session["username"] = username
    request.session["last_activity"] = (
        datetime.now(timezone.utc).timestamp()
    )

    return RedirectResponse(
        url="/dashboard",
        status_code=303,
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = get_current_user(request)

    if user is None:
        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
        },
    )


@router.get("/logout")
def logout(request: Request):
    request.session.clear()

    return RedirectResponse(
        url="/",
        status_code=303,
    )