from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from datetime import datetime, time
import random

# Создаём таблицы
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SIP Bot Backend")

# Разрешаем доступ с фронтенда (Netlify)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # можно заменить на точный URL фронтенда
    allow_methods=["*"],
    allow_headers=["*"],
)

# Рабочее время
WORK_START = time(8, 0)
WORK_END = time(19, 0)

# Сессия БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Проверка рабочего времени
def is_work_time():
    now = datetime.now().time()
    return WORK_START <= now <= WORK_END

# ---------------------------
# Эндпоинт: загрузка SIP (админ)
# ---------------------------
@app.post("/admin/upload_sips")
async def upload_sips(
    provider: str = Form(...),
    file: UploadFile = File(...),
    db: Session = next(get_db())
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

# ---------------------------
# Эндпоинт: старт пользователя
# ---------------------------
@app.post("/start")
async def start(data: dict, db: Session = next(get_db())):
    telegram_id = str(data["telegram_id"])
    username = data.get("username", "")
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()

    # Новый пользователь — добавляем в базу
    if not user:
        new_user = models.User(telegram_id=telegram_id, username=username)
        db.add(new_user)
        db.commit()
        return {"status": "pending", "message": "Ожидает одобрения админом"}

    # Проверка рабочего времени
    if not is_work_time():
        return {"status": "closed", "message": "Работа бота недоступна вне рабочего времени"}

    # Если SIP ещё не выдан
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

    # Если SIP уже назначен
    assigned_sip = db.query(models.SIP).filter(models.SIP.number == user.sip_assigned).first()
    if assigned_sip:
        return {
            "status": "ok",
            "sip": assigned_sip.number,
            "host": assigned_sip.host,
            "password": assigned_sip.password
        }
    else:
        # На всякий случай — SIP пропал, выдаём новый
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

# ---------------------------
# Запуск локально
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
