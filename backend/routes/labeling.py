from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import get_db
from models import Dataset, DataItem
from schemas import UploadResponse
from services.gemini_service import GeminiLabelingService
from services.model_training import LocalModelTrainer

router = APIRouter(prefix="/api", tags=["labeling"])
logger = logging.getLogger(__name__)

# Initialize services
try:
    gemini_service = GeminiLabelingService()
except Exception as e:
    logger.error(f"Failed to initialize Gemini service: {str(e)}")
    gemini_service = None

try:
    model_trainer = LocalModelTrainer()
except Exception as e:
    logger.error(f"Failed to initialize model trainer: {str(e)}")
    model_trainer = None

@router.post("/datasets/{dataset_id}/process")
def process_dataset(
    dataset_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger background processing of unlabeled items in a dataset.
    Uses Gemini AI to automatically label items.

    This endpoint returns immediately and processes items in background.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if not gemini_service:
        raise HTTPException(
            status_code=503,
            detail="Gemini service not initialized. Check GEMINI_API_KEY in .env"
        )

    # Get unlabeled items
    unlabeled_items = db.query(DataItem).filter(
        DataItem.dataset_id == dataset_id,
        DataItem.final_label.is_(None)
    ).all()

    if not unlabeled_items:
        return {
            "status": "no_items",
            "dataset_id": dataset_id,
            "message": "No unlabeled items found in dataset"
        }

    # Schedule background task
    background_tasks.add_task(
        _process_dataset_background,
        dataset_id=dataset_id,
        item_ids=[item.id for item in unlabeled_items]
    )

    return {
        "status": "processing",
        "dataset_id": dataset_id,
        "queued_items": len(unlabeled_items),
        "message": f"Started processing {len(unlabeled_items)} items in background"
    }

def _process_dataset_background(dataset_id: int, item_ids: list):
    """
    Background task to process dataset items with Gemini.
    Updates database with labels and confidence scores.
    """
    from database import SessionLocal

    db = SessionLocal()
    processed = 0
    failed = 0
    errors = []

    try:
        for item_id in item_ids:
            try:
                item = db.query(DataItem).filter(DataItem.id == item_id).first()

                if not item or item.final_label:
                    continue

                logger.info(f"Processing item {item_id}...")

                # Label the item
                label, confidence = gemini_service.label_data_item(item)

                # Update database
                item.final_label = label
                item.confidence_score = confidence
                db.commit()

                processed += 1
                logger.info(
                    f"Item {item_id} labeled: {label} "
                    f"(confidence: {confidence})"
                )

            except Exception as e:
                failed += 1
                error_msg = f"Item {item_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                db.rollback()

                # Continue processing other items
                continue

        logger.info(
            f"Dataset {dataset_id} processing complete: "
            f"{processed} processed, {failed} failed"
        )

    finally:
        db.close()

@router.get("/datasets/{dataset_id}/process/status")
def get_processing_status(dataset_id: int, db: Session = Depends(get_db)):
    """
    Get status of labeling in a dataset.
    Returns counts of labeled, unlabeled, and total items.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    total_items = db.query(DataItem).filter(
        DataItem.dataset_id == dataset_id
    ).count()

    labeled_items = db.query(DataItem).filter(
        DataItem.dataset_id == dataset_id,
        DataItem.final_label.isnot(None)
    ).count()

    unlabeled_items = total_items - labeled_items

    # Calculate average confidence
    labeled_with_confidence = db.query(DataItem).filter(
        DataItem.dataset_id == dataset_id,
        DataItem.final_label.isnot(None),
        DataItem.confidence_score.isnot(None)
    ).all()

    avg_confidence = None
    if labeled_with_confidence:
        avg_confidence = round(
            sum(item.confidence_score for item in labeled_with_confidence) /
            len(labeled_with_confidence),
            4
        )

    return {
        "dataset_id": dataset_id,
        "total_items": total_items,
        "labeled_items": labeled_items,
        "unlabeled_items": unlabeled_items,
        "completion_percentage": round(
            (labeled_items / total_items * 100) if total_items > 0 else 0, 2
        ),
        "average_confidence": avg_confidence
    }

@router.post("/items/{item_id}/label")
def label_single_item(item_id: int, db: Session = Depends(get_db)):
    """
    Label a single data item immediately.
    Returns the generated label and confidence score.
    """
    item = db.query(DataItem).filter(DataItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Data item not found")

    if not gemini_service:
        raise HTTPException(
            status_code=503,
            detail="Gemini service not initialized. Check GEMINI_API_KEY in .env"
        )

    try:
        logger.info(f"Labeling item {item_id}...")
        label, confidence = gemini_service.label_data_item(item)

        # Update database
        item.final_label = label
        item.confidence_score = confidence
        db.commit()

        return {
            "item_id": item_id,
            "label": label,
            "confidence_score": confidence,
            "status": "success"
        }

    except ValueError as e:
        logger.error(f"Validation error labeling item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Labeling failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error labeling item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )

@router.get("/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get details of a specific data item"""
    item = db.query(DataItem).filter(DataItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Data item not found")

    return {
        "id": item.id,
        "dataset_id": item.dataset_id,
        "file_type": item.file_type,
        "content_preview": item.content_preview[:200] + "..." if len(item.content_preview) > 200 else item.content_preview,
        "final_label": item.final_label,
        "confidence_score": item.confidence_score,
        "is_reviewed": item.is_reviewed,
        "created_at": item.created_at
    }

@router.put("/items/{item_id}/review")
def review_item(item_id: int, is_reviewed: bool, db: Session = Depends(get_db)):
    """Mark an item as reviewed after label inspection"""
    item = db.query(DataItem).filter(DataItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Data item not found")

    item.is_reviewed = is_reviewed
    db.commit()

    return {
        "item_id": item_id,
        "is_reviewed": is_reviewed,
        "status": "success"
    }

@router.put("/items/{item_id}/correct")
def correct_item_label(
    item_id: int,
    corrected_label: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Manually correct an item's label (human-in-the-loop).
    Sets confidence_score to 1.0 and marks as reviewed.
    May trigger model retraining if threshold is reached.
    """
    item = db.query(DataItem).filter(DataItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Data item not found")

    if not corrected_label or len(corrected_label.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Corrected label cannot be empty"
        )

    if len(corrected_label) > 50:
        raise HTTPException(
            status_code=400,
            detail="Label must be 50 characters or less"
        )

    # Update with human correction
    item.final_label = corrected_label.strip()
    item.confidence_score = 1.0
    item.is_reviewed = True
    db.commit()

    logger.info(
        f"Item {item_id} manually corrected: label={item.final_label}"
    )

    # Check if we should trigger retraining
    dataset_id = item.dataset_id
    reviewed_count = db.query(DataItem).filter(
        DataItem.dataset_id == dataset_id,
        DataItem.is_reviewed == True
    ).count()

    # Trigger retraining every 10 reviewed items
    if reviewed_count % 10 == 0 and model_trainer:
        background_tasks.add_task(
            _train_model_background,
            dataset_id=dataset_id
        )
        logger.info(
            f"Retraining triggered for dataset {dataset_id} "
            f"(reviewed items: {reviewed_count})"
        )

    return {
        "item_id": item_id,
        "final_label": item.final_label,
        "confidence_score": item.confidence_score,
        "is_reviewed": item.is_reviewed,
        "status": "success"
    }

@router.post("/datasets/{dataset_id}/train-model")
def train_dataset_model(
    dataset_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger model training on dataset.
    Uses all reviewed items as training data.
    """
    if not model_trainer:
        raise HTTPException(
            status_code=503,
            detail="Model training service not available"
        )

    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get reviewed items
    reviewed_items = db.query(DataItem).filter(
        DataItem.dataset_id == dataset_id,
        DataItem.is_reviewed == True,
        DataItem.final_label.isnot(None)
    ).all()

    if len(reviewed_items) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 reviewed items to train model"
        )

    # Queue background training
    background_tasks.add_task(
        _train_model_background,
        dataset_id=dataset_id
    )

    return {
        "status": "queued",
        "dataset_id": dataset_id,
        "training_samples": len(reviewed_items),
        "message": f"Model training queued for dataset {dataset.name}"
    }

def _train_model_background(dataset_id: int):
    """Background task for model training"""
    from database import SessionLocal

    db = SessionLocal()

    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            logger.error(f"Dataset {dataset_id} not found")
            return

        # Get reviewed items for training
        reviewed_items = db.query(DataItem).filter(
            DataItem.dataset_id == dataset_id,
            DataItem.is_reviewed == True,
            DataItem.final_label.isnot(None)
        ).all()

        if len(reviewed_items) < 2:
            logger.warning(
                f"Not enough reviewed items to train model for dataset {dataset_id}"
            )
            return

        # Extract text and labels
        texts = [item.content_preview for item in reviewed_items]
        labels = [item.final_label for item in reviewed_items]

        # Train model
        logger.info(f"Starting model training for dataset {dataset_id}...")
        metadata = model_trainer.train_model(
            dataset_id=dataset_id,
            dataset_name=dataset.name,
            texts=texts,
            labels=labels,
            model_type="logistic_regression"
        )

        logger.info(
            f"Model training completed for dataset {dataset_id}: "
            f"Accuracy={metadata['accuracy']:.4f}, "
            f"F1={metadata['f1_score']:.4f}"
        )

    except Exception as e:
        logger.error(f"Model training failed for dataset {dataset_id}: {str(e)}")

    finally:
        db.close()
