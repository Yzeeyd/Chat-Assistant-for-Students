from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, Time, func
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(190), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    schedule_items = relationship('ScheduleItem', back_populates='user', cascade='all, delete-orphan')
    messages = relationship('ChatMessage', back_populates='user', cascade='all, delete-orphan')
    reminders = relationship('Reminder', back_populates='user', cascade='all, delete-orphan')
    academic_plan_items = relationship('AcademicPlanItem', back_populates='user', cascade='all, delete-orphan')
    assignments = relationship('Assignment', back_populates='user', cascade='all, delete-orphan')


class ScheduleItem(Base):
    __tablename__ = 'schedule_items'
    __table_args__ = (
        Index('ix_schedule_items_user_day', 'user_id', 'day_of_week'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_code = Column(String(40), nullable=True)
    course_name = Column(String(200), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    room_text = Column(String(80), nullable=False)
    instructor = Column(String(180), nullable=True)
    credits = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship('User', back_populates='schedule_items')


class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    __table_args__ = (
        Index('ix_chat_messages_user_created', 'user_id', 'id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship('User', back_populates='messages')


class Reminder(Base):
    __tablename__ = 'reminders'
    __table_args__ = (
        Index('ix_reminders_user_done', 'user_id', 'is_done'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(200), nullable=False)
    remind_at_text = Column(String(120), nullable=False)
    remind_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    is_done = Column(Boolean, nullable=False, default=False, server_default='0')
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship('User', back_populates='reminders')


class AcademicPlanItem(Base):
    __tablename__ = 'academic_plan_items'
    __table_args__ = (
        Index('ix_academic_plan_user_status', 'user_id', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_code = Column(String(40), nullable=True)
    course_name = Column(String(200), nullable=False)
    credits = Column(Integer, nullable=True)
    semester = Column(String(60), nullable=True)
    status = Column(String(40), nullable=False, default='planned')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship('User', back_populates='academic_plan_items')


class UniversityRule(Base):
    __tablename__ = 'university_rules'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    category = Column(String(80), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class Assignment(Base):
    __tablename__ = 'assignments'
    __table_args__ = (
        Index('ix_assignments_user_id', 'user_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(200), nullable=False)
    course_name = Column(String(200), nullable=True)
    due_date_text = Column(String(120), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship('User', back_populates='assignments')
