from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import logging

from database import get_db
from models import Dataset, DataItem
from services.export_service import ExportService
from services.model_training import LocalModelTrainer

router = APIRouter(prefix="/api", tags=["export"])
logger = logging.getLogger(__name__)

export_service = ExportService()
model_trainer = LocalModelTrainer()

@router.get("/datasets/{dataset_id}/export/csv")
def export_dataset_csv(dataset_id: int, db: Session = Depends(get_db)):
    """Export dataset as CSV file"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    items = db.query(DataItem).filter(DataItem.dataset_id == dataset_id).all()

    try:
        csv_content = export_service.export_to_csv(dataset, items)

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={dataset.name}_export.csv"
            }
        )
    except Exception as e:
        logger.error(f"CSV export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datasets/{dataset_id}/export/json")
def export_dataset_json(dataset_id: int, db: Session = Depends(get_db)):
    """Export dataset as JSON file"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    items = db.query(DataItem).filter(DataItem.dataset_id == dataset_id).all()

    try:
        json_content = export_service.export_to_json(dataset, items)

        return StreamingResponse(
            iter([json_content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={dataset.name}_export.json"
            }
        )
    except Exception as e:
        logger.error(f"JSON export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datasets/{dataset_id}/export/ml-ready")
def export_dataset_ml_ready(dataset_id: int, db: Session = Depends(get_db)):
    """Export dataset in ML-ready format (CSV with features and labels)"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    items = db.query(DataItem).filter(DataItem.dataset_id == dataset_id).all()

    try:
        csv_content = export_service.export_to_ml_ready_csv(dataset, items)

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={dataset.name}_ml_ready.csv"
            }
        )
    except Exception as e:
        logger.error(f"ML-ready export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datasets/{dataset_id}/export/zip")
def export_dataset_zip(dataset_id: int, db: Session = Depends(get_db)):
    """Export complete dataset as ZIP with all formats and original files"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    items = db.query(DataItem).filter(DataItem.dataset_id == dataset_id).all()

    try:
        zip_content = export_service.export_to_zip(dataset, items)

        return StreamingResponse(
            iter([zip_content]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={dataset.name}_export.zip"
            }
        )
    except Exception as e:
        logger.error(f"ZIP export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
def list_models():
    """List all trained local models"""
    try:
        models = model_trainer.list_models()

        return {
            "total_models": len(models),
            "models": models
        }
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{dataset_id}")
def get_model_info(dataset_id: int):
    """Get metadata for specific trained model"""
    metadata = model_trainer.get_metadata(dataset_id)

    if not metadata:
        raise HTTPException(
            status_code=404,
            detail=f"No trained model found for dataset {dataset_id}"
        )

    return metadata

@router.post("/models/{dataset_id}/delete")
def delete_model(dataset_id: int):
    """Delete trained model and artifacts"""
    try:
        success = model_trainer.delete_model(dataset_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete model"
            )

        logger.info(f"Deleted model for dataset {dataset_id}")

        return {
            "status": "success",
            "message": f"Model for dataset {dataset_id} deleted"
        }
    except Exception as e:
        logger.error(f"Failed to delete model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exports")
def list_exports():
    """List all available dataset exports"""
    try:
        exports = export_service.list_exports()

        return {
            "total_exports": len(exports),
            "exports": exports
        }
    except Exception as e:
        logger.error(f"Failed to list exports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
