from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from datetime import datetime, time
import random

# Создаём таблицы
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SIP Bot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # можно заменить на URL фронтенда
    allow_methods=["*"],
    allow_headers=["*"],
)

WORK_START = time(8, 0)
WORK_END = time(19, 0)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_work_time():
    now = datetime.now().time()
    return WORK_START <= now <= WORK_END

@app.post("/admin/upload_sips")
async def upload_sips(
    provider: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = await file.read()
    lines = content.decode("utf-8").splitlines()

    if not lines or not lines[0].lower().startswith("host:"):
        return {"status": "error", "message": "Неверный формат файла"}

    host = lines[0].split(":", 1)[1].strip()
    added = 0
    for line in lines[1:]:
        if ":" not in line:
            continue
        login, password = [x.strip() for x in line.split(":", 1)]
        exists = db.query(models.SIP).filter(models.SIP.number == login).first()
        if exists:
            continue
        sip = models.SIP(number=login, password=password, host=host, provider=provider)
        db.add(sip)
        added += 1

    db.commit()
    return {"status": "ok", "added": added, "provider": provider, "host": host}

@app.post("/start")
async def start(data: dict, db: Session = Depends(get_db)):
    telegram_id = str(data["telegram_id"])
    username = data.get("username", "")
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()

    if not user:
        new_user = models.User(telegram_id=telegram_id, username=username)
        db.add(new_user)
        db.commit()
        return {"status": "pending", "message": "Ожидает одобрения админом"}

    if not is_work_time():
        return {"status": "closed", "message": "Работа бота недоступна вне рабочего времени"}

    if not user.sip_assigned:
        free_sips = db.query(models.SIP).filter(models.SIP.status == "free").all()
        if not free_sips:
            return {"status": "error", "message": "Свободные SIP закончились"}

        sip = random.choice(free_sips)
        sip.status = "used"
        sip.assigned_to = telegram_id
        user.sip_assigned = sip.number
        db.commit()
        return {
            "status": "ok",
            "sip": sip.number,
            "host": sip.host,
            "password": sip.password
        }

    assigned_sip = db.query(models.SIP).filter(models.SIP.number == user.sip_assigned).first()
    if assigned_sip:
        return {
            "status": "ok",
            "sip": assigned_sip.number,
            "host": assigned_sip.host,
            "password": assigned_sip.password
        }
    else:
        free_sips = db.query(models.SIP).filter(models.SIP.status == "free").all()
        if not free_sips:
            return {"status": "error", "message": "Свободные SIP закончились"}
        sip = random.choice(free_sips)
        sip.status = "used"
        sip.assigned_to = telegram_id
        user.sip_assigned = sip.number
        db.commit()
        return {
            "status": "ok",
            "sip": sip.number,
            "host": sip.host,
            "password": sip.password
        }
