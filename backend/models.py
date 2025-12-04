from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_ts = Column(DateTime, default=datetime.datetime.utcnow)
    end_ts = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # seconds
    word_count = Column(Integer, nullable=True)
    transcript = Column(Text, nullable=True)
