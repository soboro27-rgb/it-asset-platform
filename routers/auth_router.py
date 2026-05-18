from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from database import get_db
import models
from auth import verify_password
from config import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user_id"):
        role = request.session.get("role")
        return RedirectResponse("/branch/dashboard" if role == "branch" else "/admin/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login(
    request: Request,
    branch_code: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(
        models.User.branch_code == branch_code,
        models.User.is_active == True,
    ).first()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "아이디 또는 비밀번호가 올바르지 않습니다."},
        )

    request.session["user_id"] = user.id
    request.session["role"] = user.role
    request.session["branch_code"] = user.branch_code
    request.session["branch_name"] = user.branch_name

    if user.role == "branch":
        return RedirectResponse("/branch/dashboard", status_code=302)
    return RedirectResponse("/admin/dashboard", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
