from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User
from app.auth.security import hash_password, verify_password
from app.auth.otp_utils import generate_otp_secret, verify_otp_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
def register_user(email: str, password: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    otp_secret = generate_otp_secret()
    new_user = User(email=email, password_hash=hash_password(password), otp_secret=otp_secret)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "otp_secret": otp_secret}

@router.post("/login")
def login_user(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful. Please verify OTP to continue."}

@router.post("/verify-otp")
def verify_otp(email: str, token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_otp_token(user.otp_secret, token):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user.is_verified = True
    db.commit()
    return {"message": "2FA verification successful"}

