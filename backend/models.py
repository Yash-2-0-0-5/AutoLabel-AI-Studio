from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(Text, nullable=True)
    file_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("DataItem", back_populates="dataset", cascade="all, delete-orphan")

class DataItem(Base):
    __tablename__ = "data_items"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), index=True)
    raw_data_path = Column(String(500))
    file_type = Column(String(50))
    content_preview = Column(Text)
    final_label = Column(String(255), nullable=True)
    confidence_score = Column(Float, nullable=True)
    is_reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="items")
