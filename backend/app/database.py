from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings

db_url = settings.database_url
# Hosted providers (Neon, Render, Heroku...) often give "postgres://" or "postgresql://" URLs.
# Normalise them so SQLAlchemy uses the psycopg2 driver.
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

is_sqlite = db_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
# pool_pre_ping reconnects automatically when Neon has suspended an idle database
engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=not is_sqlite,
    pool_recycle=300 if not is_sqlite else -1,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
