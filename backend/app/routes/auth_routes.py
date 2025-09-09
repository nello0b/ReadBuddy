# app/routes/auth_routes.py

from fastapi import APIRouter, HTTPException, Header
from app.services.auth.auth0 import verify_auth0_token
from database import db
from config import DEBUG_MODE
from app.models.user import User

router = APIRouter()

@router.post("/api/auth/token")
async def auth_with_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid Authorization header format")

    token = authorization.split(" ")[1]

    if DEBUG_MODE:
        print("📥 Received token:", token)

    try:
        payload = verify_auth0_token(token)
        if DEBUG_MODE:
            print("🔍 Decoded payload:", payload)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    sub = payload.get("sub")
    email = payload.get("email")
    name = payload.get("name")

    if DEBUG_MODE:
        print(f"🧾 sub: {sub}, 📧 email: {email}, 👤 name: {name}")

    if not sub:
        raise HTTPException(status_code=400, detail="Token missing required 'sub' claim")

    user = db.get_user_by_sub(sub)

    if not user:
        if DEBUG_MODE:
            print("➕ Creating new user in DB")
        db.create_user(User(sub=sub, email=email, name=name))
        user = db.get_user_by_sub(sub)

        if DEBUG_MODE:
            print("✅ User created and retrieved:", user)

    return {
        "status": "ok",
        "user": {
            "id": str(user.get("_id")),
            "email": user.get("email"),
            "name": user.get("name")
        }
    }
