from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///.internos.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True) 

class Base(DeclarativeBase):
    pass

def get_db():
    from contextlib import contextmanager
    @contextmanager
    def _session_scope():
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    return _session_scope()


