import uuid
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from database import get_conn
from schemas import TokenOut, MfaPendingOut
from utils.auth import verify_password, create_access_token, create_pre_auth_token, get_current_user
from utils.audit import write_audit
from limiter import limiter

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=MfaPendingOut)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    conn: asyncpg.Connection        = Depends(get_conn),
):
    row = await conn.fetchrow(
        "SELECT id, name, initials, email, password_hash, role, is_active FROM staff_users WHERE email=$1",
        form.username.lower(),
    )
    if not row or not verify_password(form.password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not row["is_active"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account disabled")

    pre_auth_token = create_pre_auth_token(str(row["id"]))
    await write_audit(conn, "Staff Login (password step)", actor={"id": row["id"], "name": row["name"]}, detail=f"Password verified: {form.username}")
    return {"pre_auth_token": pre_auth_token, "registration_required": not has_credential}


@router.post("/logout")
async def logout(
    current: dict              = Depends(get_current_user),
    conn:    asyncpg.Connection = Depends(get_conn),
):
    await write_audit(conn, "Staff Logout", actor=current)
    return {"detail": "Logged out"}
