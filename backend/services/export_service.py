import os
import json
import csv
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from io import BytesIO, StringIO
import zipfile

logger = logging.getLogger(__name__)

EXPORTS_DIR = "exports"

class ExportService:
    """Service for exporting datasets in multiple formats"""

    def __init__(self):
        """Initialize export service"""
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        logger.info(f"ExportService initialized with exports_dir: {EXPORTS_DIR}")

    def export_to_csv(self, dataset: Dict, items: List[Dict]) -> str:
        """
        Export dataset as CSV.

        Args:
            dataset: Dataset model
            items: List of DataItem models

        Returns:
            CSV content as string
        """
        output = StringIO()
        fieldnames = [
            'id',
            'content_preview',
            'file_type',
            'final_label',
            'confidence_score',
            'is_reviewed',
            'created_at'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for item in items:
            writer.writerow({
                'id': item.id,
                'content_preview': item.content_preview[:500],
                'file_type': item.file_type,
                'final_label': item.final_label or '',
                'confidence_score': item.confidence_score or '',
                'is_reviewed': item.is_reviewed,
                'created_at': item.created_at.isoformat()
            })

        csv_content = output.getvalue()
        logger.info(f"Exported dataset {dataset.id} as CSV ({len(csv_content)} bytes)")

        return csv_content

    def export_to_json(self, dataset: Dict, items: List[Dict]) -> str:
        """
        Export dataset as JSON.

        Args:
            dataset: Dataset model
            items: List of DataItem models

        Returns:
            JSON content as string
        """
        export_data = {
            "metadata": {
                "dataset_id": dataset.id,
                "dataset_name": dataset.name,
                "dataset_type": dataset.file_type,
                "description": dataset.description,
                "created_at": dataset.created_at.isoformat(),
                "exported_at": datetime.utcnow().isoformat(),
                "total_items": len(items),
                "labeled_items": sum(1 for item in items if item.final_label),
                "reviewed_items": sum(1 for item in items if item.is_reviewed),
                "average_confidence": (
                    sum(item.confidence_score or 0 for item in items) / len(items)
                    if items else 0
                )
            },
            "items": [
                {
                    "id": item.id,
                    "content_preview": item.content_preview,
                    "file_type": item.file_type,
                    "final_label": item.final_label,
                    "confidence_score": item.confidence_score,
                    "is_reviewed": item.is_reviewed,
                    "raw_data_path": item.raw_data_path,
                    "created_at": item.created_at.isoformat()
                }
                for item in items
            ]
        }

        json_content = json.dumps(export_data, indent=2)
        logger.info(f"Exported dataset {dataset.id} as JSON ({len(json_content)} bytes)")

        return json_content

    def export_to_ml_ready_csv(self, dataset: Dict, items: List[Dict]) -> str:
        """
        Export dataset in ML-ready format (features + label).

        Only includes labeled items with high confidence (for training).

        Args:
            dataset: Dataset model
            items: List of DataItem models

        Returns:
            CSV content as string
        """
        # Filter: Only labeled and reviewed items
        labeled_items = [
            item for item in items
            if item.final_label and item.is_reviewed
        ]

        output = StringIO()
        fieldnames = ['text', 'label']

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for item in labeled_items:
            writer.writerow({
                'text': item.content_preview[:1000],
                'label': item.final_label
            })

        csv_content = output.getvalue()
        logger.info(
            f"Exported dataset {dataset.id} as ML-ready CSV: "
            f"{len(labeled_items)} high-confidence samples"
        )

        return csv_content

    def export_to_zip(
        self,
        dataset: Dict,
        items: List[Dict],
        include_original_files: bool = True
    ) -> bytes:
        """
        Export dataset as ZIP with assets and metadata.

        Args:
            dataset: Dataset model
            items: List of DataItem models
            include_original_files: Whether to include original uploaded files

        Returns:
            ZIP file content as bytes
        """
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add metadata
            metadata = {
                "dataset_id": dataset.id,
                "dataset_name": dataset.name,
                "dataset_type": dataset.file_type,
                "export_date": datetime.utcnow().isoformat(),
                "total_items": len(items),
                "labeled_items": sum(1 for item in items if item.final_label)
            }

            zip_file.writestr(
                "metadata.json",
                json.dumps(metadata, indent=2)
            )

            # Add CSV export
            csv_content = self.export_to_csv(dataset, items)
            zip_file.writestr("dataset.csv", csv_content)

            # Add JSON export
            json_content = self.export_to_json(dataset, items)
            zip_file.writestr("dataset.json", json_content)

            # Add ML-ready CSV
            ml_csv = self.export_to_ml_ready_csv(dataset, items)
            zip_file.writestr("dataset_ml_ready.csv", ml_csv)

            # Add original files if requested
            if include_original_files:
                for item in items:
                    if item.file_type in ['image', 'audio'] and os.path.exists(item.raw_data_path):
                        try:
                            arcname = os.path.join(
                                item.file_type,
                                os.path.basename(item.raw_data_path)
                            )
                            zip_file.write(item.raw_data_path, arcname=arcname)
                        except Exception as e:
                            logger.warning(f"Failed to add file {item.raw_data_path}: {e}")

            # Add manifest
            manifest = {
                "files": {
                    "metadata.json": "Dataset metadata",
                    "dataset.csv": "Complete dataset in CSV format",
                    "dataset.json": "Complete dataset in JSON format",
                    "dataset_ml_ready.csv": "ML-ready format (labeled + reviewed items only)",
                    "images/": "Original image files (if applicable)",
                    "audio/": "Original audio files (if applicable)"
                },
                "readme": "This ZIP contains the complete labeled dataset ready for training or deployment."
            }

            zip_file.writestr(
                "MANIFEST.json",
                json.dumps(manifest, indent=2)
            )

        zip_content = zip_buffer.getvalue()
        logger.info(f"Exported dataset {dataset.id} as ZIP ({len(zip_content)} bytes)")

        return zip_content

    def save_export_file(
        self,
        dataset: Dict,
        items: List[Dict],
        export_format: str
    ) -> str:
        """
        Save export to disk and return file path.

        Args:
            dataset: Dataset model
            items: List of DataItem models
            export_format: Format ('csv', 'json', 'ml_ready', 'zip')

        Returns:
            Path to saved file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = dataset.name.replace(' ', '_').lower()

        if export_format == 'csv':
            filename = f"{safe_name}_{timestamp}.csv"
            content = self.export_to_csv(dataset, items)

            file_path = os.path.join(EXPORTS_DIR, filename)
            with open(file_path, 'w', newline='') as f:
                f.write(content)

        elif export_format == 'json':
            filename = f"{safe_name}_{timestamp}.json"
            content = self.export_to_json(dataset, items)

            file_path = os.path.join(EXPORTS_DIR, filename)
            with open(file_path, 'w') as f:
                f.write(content)

        elif export_format == 'ml_ready':
            filename = f"{safe_name}_ml_ready_{timestamp}.csv"
            content = self.export_to_ml_ready_csv(dataset, items)

            file_path = os.path.join(EXPORTS_DIR, filename)
            with open(file_path, 'w', newline='') as f:
                f.write(content)

        elif export_format == 'zip':
            filename = f"{safe_name}_{timestamp}.zip"
            content = self.export_to_zip(dataset, items)

            file_path = os.path.join(EXPORTS_DIR, filename)
            with open(file_path, 'wb') as f:
                f.write(content)

        else:
            raise ValueError(f"Unknown export format: {export_format}")

        logger.info(f"Saved export to {file_path}")
        return file_path

    def list_exports(self) -> List[Dict]:
        """List all exported files"""
        exports = []

        if not os.path.exists(EXPORTS_DIR):
            return exports

        for filename in os.listdir(EXPORTS_DIR):
            filepath = os.path.join(EXPORTS_DIR, filename)

            if os.path.isfile(filepath):
                exports.append({
                    "filename": filename,
                    "size_bytes": os.path.getsize(filepath),
                    "created_at": datetime.fromtimestamp(
                        os.path.getctime(filepath)
                    ).isoformat()
                })

        return sorted(exports, key=lambda x: x['created_at'], reverse=True)

    def cleanup_old_exports(self, days: int = 7) -> int:
        """
        Delete exports older than specified days.

        Args:
            days: Delete files older than this many days

        Returns:
            Number of files deleted
        """
        import time

        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0

        if not os.path.exists(EXPORTS_DIR):
            return 0

        for filename in os.listdir(EXPORTS_DIR):
            filepath = os.path.join(EXPORTS_DIR, filename)

            if os.path.isfile(filepath):
                if os.path.getctime(filepath) < cutoff_time:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                        logger.info(f"Deleted old export: {filename}")
                    except Exception as e:
                        logger.error(f"Failed to delete {filename}: {e}")

        return deleted_count
