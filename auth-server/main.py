from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import datetime
import uuid
import secrets
import httpx
import os
from typing import List, Optional
from pydantic import BaseModel

from app import models, security, database
from app.database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Server for Auto-Forward Bot")

# Pydantic models
class LicenseValidate(BaseModel):
    license_key: str
    bot_token: str

class LicenseCreate(BaseModel):
    owner_id: str
    days: int
    bot_token_prefix: Optional[str] = None

class LicenseUpdateCredentials(BaseModel):
    api_id: str
    api_hash: str
    bot_token: str

class LicenseResponse(BaseModel):
    key: str
    owner_id: str
    expiry_date: datetime.datetime
    is_active: bool
    is_locked: bool

# Telegram notification settings
TELEGRAM_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")

async def send_telegram_message(chat_id: str, text: str):
    if not TELEGRAM_BOT_TOKEN:
        print(f"TELEGRAM_BOT_TOKEN not set. Cannot send message to {chat_id}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json={"chat_id": chat_id, "text": text})
        except Exception as e:
            print(f"Error sending Telegram message: {e}")

from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    admin_user = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin_user:
        hashed_pw = security.get_password_hash(os.getenv("ADMIN_PASSWORD", "admin123"))
        new_admin = models.User(username="admin", hashed_password=hashed_pw)
        db.add(new_admin)
        db.commit()

@app.post("/token")
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/license/generate", response_model=LicenseResponse)
async def generate_license(data: LicenseCreate, db: Session = Depends(get_db)):
    # Simple check for admin auth could be added here
    new_key = str(uuid.uuid4()).upper().replace("-", "")
    expiry = datetime.datetime.utcnow() + datetime.timedelta(days=data.days)
    
    db_license = models.License(
        key=new_key,
        owner_id=data.owner_id,
        bot_token_prefix=data.bot_token_prefix,
        expiry_date=expiry,
    )
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    
    # Automated key delivery
    await send_telegram_message(data.owner_id, f"Your new license key: {new_key}\nExpires on: {expiry}")
    
    return db_license

@app.post("/license/validate")
async def validate_license(data: LicenseValidate, db: Session = Depends(get_db)):
    db_license = db.query(models.License).filter(models.License.key == data.license_key).first()
    
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")
    
    if db_license.is_locked:
        raise HTTPException(status_code=403, detail="License is locked due to multiple failed attempts")
    
    if not db_license.is_active:
        raise HTTPException(status_code=403, detail="License is inactive")
    
    if db_license.expiry_date < datetime.datetime.utcnow():
        raise HTTPException(status_code=403, detail="License expired")
    
    # Bot token prefix binding
    token_prefix = data.bot_token.split(":")[0]
    if db_license.bot_token_prefix:
        if db_license.bot_token_prefix != token_prefix:
            db_license.failed_attempts += 1
            if db_license.failed_attempts >= 5:
                db_license.is_locked = True
            db.commit()
            raise HTTPException(status_code=403, detail="License bound to another bot token")
    else:
        # First time binding
        db_license.bot_token_prefix = token_prefix
        db.commit()
    
    # Reset failed attempts on successful validation
    db_license.failed_attempts = 0
    db.commit()
    
    return {"status": "valid", "expiry_date": db_license.expiry_date}

@app.get("/license/status/{key}", response_model=LicenseResponse)
async def get_license_status(key: str, db: Session = Depends(get_db)):
    db_license = db.query(models.License).filter(models.License.key == key).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")
    return db_license

@app.post("/license/{key}/credentials")
async def update_license_credentials(key: str, data: LicenseUpdateCredentials, db: Session = Depends(get_db)):
    db_license = db.query(models.License).filter(models.License.key == key).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")
    
    db_license.api_id_encrypted = security.encrypt_data(data.api_id)
    db_license.api_hash_encrypted = security.encrypt_data(data.api_hash)
    db_license.bot_token_encrypted = security.encrypt_data(data.bot_token)
    db.commit()
    
    return {"message": "Credentials updated and encrypted"}

@app.get("/license/{key}/config")
async def get_license_config(key: str, db: Session = Depends(get_db)):
    db_license = db.query(models.License).filter(models.License.key == key).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")
    
    return {
        "API_ID": security.decrypt_data(db_license.api_id_encrypted),
        "API_HASH": security.decrypt_data(db_license.api_hash_encrypted),
        "BOT_TOKEN": security.decrypt_data(db_license.bot_token_encrypted),
        "LICENSE_KEY": db_license.key
    }

# Periodic task for expiry reminder (could be triggered by a cron job calling this endpoint)
@app.post("/tasks/check-expiries")
async def check_expiries(db: Session = Depends(get_db)):
    reminder_date = datetime.datetime.utcnow() + datetime.timedelta(days=3)
    # Get licenses expiring in exactly 3 days (within a 24h window)
    start_reminder = reminder_date.replace(hour=0, minute=0, second=0)
    end_reminder = reminder_date.replace(hour=23, minute=59, second=59)
    
    expiring_soon = db.query(models.License).filter(
        models.License.expiry_date >= start_reminder,
        models.License.expiry_date <= end_reminder,
        models.License.is_active == True
    ).all()
    
    for lic in expiring_soon:
        await send_telegram_message(lic.owner_id, f"Your license {lic.key} will expire in 3 days on {lic.expiry_date}")
        
    return {"count": len(expiring_soon)}
