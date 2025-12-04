from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///db.sqlite"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

DBSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
