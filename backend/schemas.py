from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any

class DataItemBase(BaseModel):
    raw_data_path: str
    file_type: str
    content_preview: str
    final_label: Optional[str] = None
    confidence_score: Optional[float] = None
    is_reviewed: bool = False

class DataItemCreate(DataItemBase):
    dataset_id: int

class DataItem(DataItemBase):
    id: int
    dataset_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    file_type: str

class DatasetCreate(DatasetBase):
    pass

class Dataset(DatasetBase):
    id: int
    created_at: datetime
    items: List[DataItem] = []

    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    dataset_id: int
    dataset_name: str
    file_type: str
    item_count: int
    recommended_strategy: str
    message: str
    preview: Any

class LabelingStrategy(BaseModel):
    strategy_type: str
    description: str
    parameters: dict
