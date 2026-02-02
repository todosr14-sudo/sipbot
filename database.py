from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite база в файле sipbot.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./sipbot.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
