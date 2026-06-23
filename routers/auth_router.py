from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from database import get_db
import models
from auth import verify_password
from config import templates
from datetime import datetime

router = APIRouter()


def _get_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def _save_log(db: Session, action: str, request: Request,
              user: models.User = None, branch_code: str = ""):
    try:
        db.add(models.LoginLog(
            user_id=user.id if user else None,
            branch_code=user.branch_code if user else branch_code,
            branch_name=user.branch_name if user else "",
            role=user.role if user else "",
            action=action,
            ip_address=_get_ip(request),
            user_agent=request.headers.get("user-agent", "")[:300],
            created_at=datetime.now(),
        ))
        db.commit()
    except Exception:
        db.rollback()


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
        _save_log(db, "login_failed", request, branch_code=branch_code)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "아이디 또는 비밀번호가 올바르지 않습니다."},
        )

    _save_log(db, "login_success", request, user=user)

    request.session["user_id"] = user.id
    request.session["role"] = user.role
    request.session["branch_code"] = user.branch_code
    request.session["branch_name"] = user.branch_name

    if user.role == "branch":
        return RedirectResponse("/branch/dashboard", status_code=302)
    return RedirectResponse("/admin/dashboard", status_code=302)


@router.get("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            _save_log(db, "logout", request, user=user)
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
