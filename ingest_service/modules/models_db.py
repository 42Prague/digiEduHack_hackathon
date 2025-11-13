"""
SQLAlchemy ORM models for the ingestion service.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .db import Base


class Teacher(Base):
    __tablename__ = "teacher"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(Text, nullable=True)
    normalized_name = Column(Text, nullable=True, index=True)
    email = Column(Text, nullable=True, unique=True)

    audio_recordings = relationship("AudioRecording", back_populates="teacher")
    survey_responses = relationship("SurveyResponse", back_populates="teacher")
    raw_documents = relationship("RawDocument", back_populates="teacher")


class AudioRecording(Base):
    __tablename__ = "audio_recording"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(Integer, ForeignKey("teacher.id"), nullable=True)
    workshop_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    audio_path = Column(Text, nullable=False)
    transcript_text = Column(Text, nullable=False)
    duration_sec = Column(Integer, nullable=True)

    teacher = relationship("Teacher", back_populates="audio_recordings")


class SurveyResponse(Base):
    __tablename__ = "survey_response"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teacher.id"), nullable=True)
    workshop_id = Column(Integer, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    raw_data = Column(JSONB, nullable=False)
    normalized_data = Column(JSONB, nullable=False)

    teacher = relationship("Teacher", back_populates="survey_responses")


class RawDocument(Base):
    __tablename__ = "raw_document"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_type = Column(Text, nullable=True)
    teacher_id = Column(Integer, ForeignKey("teacher.id"), nullable=True)
    workshop_id = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    original_filename = Column(Text, nullable=False)
    mime_type = Column(Text, nullable=True)
    file_path = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)
    table_data = Column(JSONB, nullable=True)

    teacher = relationship("Teacher", back_populates="raw_documents")
