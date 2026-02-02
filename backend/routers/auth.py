from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from datetime import timedelta
import models, schemas, auth, email_utils, database
from sqlalchemy.exc import IntegrityError
import os

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/register", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate, request: Request, db: Session = Depends(database.get_db)):
    # 1. Check if user exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Create User (Unapproved)
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        is_approved=False, # Default to False
        is_active=True
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Database error")

    # 3. Send Admin Email
    # Construct approval link. 
    base_url = str(request.base_url).rstrip("/")
    approval_link = f"{base_url}/auth/approve?email={new_user.email}&secret={os.environ.get('SECRET_KEY')}"
    
    try:
        await email_utils.send_approval_request(new_user.email, approval_link)
    except Exception as e:
        print(f"FAILED TO SEND EMAIL: {e}")
        # We do NOT raise an HTTP exception here, because the user is already created.
        # We just log it. The user will see "Application Received" but admin won't get email.
        # In a real app, we might want to return a warning.

    return new_user

@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    # Check User & Password
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check Approval
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval by Administrator."
        )

    # Generate Token
    access_token_expires = timedelta(minutes=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/approve")
async def approve_user(email: str, secret: str, db: Session = Depends(database.get_db)):
    # Simple security check to prevent random people from hitting this endpoint
    if secret != os.environ.get("SECRET_KEY"):
         raise HTTPException(status_code=403, detail="Invalid Secret")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_approved = True
    db.commit()
    
    return {"message": f"User {email} has been approved. They can now log in."}
