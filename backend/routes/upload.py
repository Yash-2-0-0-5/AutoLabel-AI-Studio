from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models import Dataset, DataItem
from schemas import UploadResponse
from utils.file_handler import (
    detect_file_type, save_uploaded_file, get_file_preview, init_storage
)
from utils.auto_detection import recommend_strategy, analyze_structure, get_optimal_batch_size

router = APIRouter(prefix="/api", tags=["upload"])

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    dataset_name: str = None,
    db: Session = Depends(get_db)
):
    """
    Upload a file and create a dataset with data items.
    Supports: CSV, Excel, JSON, Images, Audio
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")

    # Detect file type
    file_type = detect_file_type(file.filename)

    if file_type == 'unknown':
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {os.path.splitext(file.filename)[1]}"
        )

    # Create dataset name if not provided
    if not dataset_name:
        dataset_name = f"{os.path.splitext(file.filename)[0]}_{datetime.now().timestamp()}"

    # Check if dataset already exists
    existing = db.query(Dataset).filter(Dataset.name == dataset_name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Dataset '{dataset_name}' already exists")

    # Initialize storage
    init_storage()

    # Read file content
    file_content = await file.read()

    # Save file
    saved_path = save_uploaded_file(file_content, file.filename, file_type)

    # Create dataset record
    dataset = Dataset(
        name=dataset_name,
        file_type=file_type,
        description=f"Dataset uploaded from {file.filename}"
    )
    db.add(dataset)
    db.flush()

    # Get preview and structure
    try:
        preview, structure = get_file_preview(saved_path, file_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

    # Create data items based on file type
    item_count = 0

    if file_type in ['csv', 'excel']:
        # For tabular data, each row is a data item
        if isinstance(preview, list):
            for idx, row in enumerate(preview):
                item = DataItem(
                    dataset_id=dataset.id,
                    raw_data_path=saved_path,
                    file_type=file_type,
                    content_preview=str(row),
                    is_reviewed=False
                )
                db.add(item)
                item_count += 1

    elif file_type == 'json':
        # For JSON, create item(s) based on structure
        if isinstance(preview, list):
            for idx, item_data in enumerate(preview):
                item = DataItem(
                    dataset_id=dataset.id,
                    raw_data_path=saved_path,
                    file_type=file_type,
                    content_preview=str(item_data),
                    is_reviewed=False
                )
                db.add(item)
                item_count += 1
        else:
            item = DataItem(
                dataset_id=dataset.id,
                raw_data_path=saved_path,
                file_type=file_type,
                content_preview=str(preview),
                is_reviewed=False
            )
            db.add(item)
            item_count = 1

    elif file_type in ['image', 'audio']:
        # For media files, create single item per file
        item = DataItem(
            dataset_id=dataset.id,
            raw_data_path=saved_path,
            file_type=file_type,
            content_preview=str(preview),
            is_reviewed=False
        )
        db.add(item)
        item_count = 1

    db.commit()
    db.refresh(dataset)

    # Get recommended strategy
    strategy = recommend_strategy(file_type)
    insights = analyze_structure(file_type, structure)

    return UploadResponse(
        dataset_id=dataset.id,
        dataset_name=dataset.name,
        file_type=file_type,
        item_count=item_count,
        recommended_strategy=strategy['strategy_type'],
        message=f"Successfully uploaded {item_count} items from {file.filename}",
        preview=insights
    )

@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    """List all datasets"""
    datasets = db.query(Dataset).all()
    return {
        "total": len(datasets),
        "datasets": datasets
    }

@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Get a specific dataset with all its items"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return dataset

@router.get("/datasets/{dataset_id}/items")
def get_dataset_items(dataset_id: int, db: Session = Depends(get_db)):
    """Get all items in a dataset"""
    items = db.query(DataItem).filter(DataItem.dataset_id == dataset_id).all()

    if not items:
        raise HTTPException(status_code=404, detail="No items found for this dataset")

    return {
        "dataset_id": dataset_id,
        "item_count": len(items),
        "items": items
    }
