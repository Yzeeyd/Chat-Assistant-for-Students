from sqlalchemy import Column, Integer, String, Time, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import relationship
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(190), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    schedule_items = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")

class Schedule(Base):
    __tablename__ = "schedule"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_code = Column(String(200), nullable=False)
    course_name = Column(String(200), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 1=Sun ... 7=Sat
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    room_text = Column(String(60), nullable=False)
    instructor = Column(String(200), nullable=True)
    
    user = relationship("User", back_populates="schedule_items")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False)   # user | assistant
    content = Column(Text, nullable=False)
    meta_json = Column(Text, nullable=True)     # JSON string for attachments (schedule items)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="messages")