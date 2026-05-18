import bcrypt
from fastapi import Request
from starlette.responses import RedirectResponse


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def get_session_user(request: Request) -> dict | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return {
        "user_id": user_id,
        "role": request.session.get("role"),
        "branch_code": request.session.get("branch_code"),
        "branch_name": request.session.get("branch_name"),
    }


def require_branch(request: Request):
    user = get_session_user(request)
    if not user or user["role"] != "branch":
        return None
    return user


def require_admin(request: Request):
    user = get_session_user(request)
    if not user or user["role"] not in ("coretail", "welfare"):
        return None
    return user
