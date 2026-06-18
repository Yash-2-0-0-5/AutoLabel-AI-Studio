import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple

STORAGE_DIR = "storage"
UPLOAD_DIR = os.path.join(STORAGE_DIR, "uploads")
IMAGES_DIR = os.path.join(STORAGE_DIR, "images")
AUDIO_DIR = os.path.join(STORAGE_DIR, "audio")

def init_storage():
    """Initialize storage directories"""
    for directory in [UPLOAD_DIR, IMAGES_DIR, AUDIO_DIR]:
        os.makedirs(directory, exist_ok=True)

def detect_file_type(filename: str) -> str:
    """Detect file type from filename"""
    ext = os.path.splitext(filename)[1].lower()

    if ext in ['.csv']:
        return 'csv'
    elif ext in ['.xlsx', '.xls']:
        return 'excel'
    elif ext in ['.json']:
        return 'json'
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        return 'image'
    elif ext in ['.mp3', '.wav', '.flac', '.m4a', '.aac']:
        return 'audio'
    else:
        return 'unknown'

def process_csv(file_path: str) -> Tuple[List[Dict], str]:
    """Process CSV file and return preview and structure"""
    df = pd.read_csv(file_path)

    preview_rows = df.head(5).to_dict(orient='records')
    columns = list(df.columns)
    structure = {
        "columns": columns,
        "total_rows": len(df),
        "sample_rows": preview_rows
    }

    return preview_rows, json.dumps(structure)

def process_excel(file_path: str) -> Tuple[List[Dict], str]:
    """Process Excel file and return preview and structure"""
    df = pd.read_excel(file_path)

    preview_rows = df.head(5).to_dict(orient='records')
    columns = list(df.columns)
    structure = {
        "columns": columns,
        "total_rows": len(df),
        "sample_rows": preview_rows
    }

    return preview_rows, json.dumps(structure)

def process_json(file_path: str) -> Tuple[Dict, str]:
    """Process JSON file and return structure"""
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Handle both list and dict JSON
    if isinstance(data, list):
        preview = data[:5]
        structure = {
            "type": "array",
            "item_count": len(data),
            "sample_items": preview
        }
    else:
        preview = data
        structure = {
            "type": "object",
            "keys": list(data.keys()) if isinstance(data, dict) else [],
            "sample": data
        }

    return preview, json.dumps(structure)

def process_image(file_path: str) -> Tuple[Dict, str]:
    """Process image file and return metadata"""
    from PIL import Image

    img = Image.open(file_path)
    metadata = {
        "format": img.format,
        "size": img.size,
        "mode": img.mode,
        "path": file_path
    }

    structure = json.dumps(metadata)
    return metadata, structure

def process_audio(file_path: str) -> Tuple[Dict, str]:
    """Process audio file and return metadata"""
    import wave

    try:
        with wave.open(file_path, 'rb') as wav_file:
            n_frames = wav_file.getnframes()
            framerate = wav_file.getframerate()
            duration = n_frames / framerate

            metadata = {
                "duration_seconds": round(duration, 2),
                "frame_rate": framerate,
                "channels": wav_file.getnchannels(),
                "path": file_path
            }
    except:
        # For non-WAV audio files, just get basic file info
        metadata = {
            "path": file_path,
            "file_size_bytes": os.path.getsize(file_path)
        }

    structure = json.dumps(metadata)
    return metadata, structure

def save_uploaded_file(file_content: bytes, filename: str, file_type: str) -> str:
    """Save uploaded file to storage directory"""
    init_storage()

    if file_type == 'image':
        save_path = os.path.join(IMAGES_DIR, filename)
    elif file_type == 'audio':
        save_path = os.path.join(AUDIO_DIR, filename)
    else:
        save_path = os.path.join(UPLOAD_DIR, filename)

    with open(save_path, 'wb') as f:
        f.write(file_content)

    return save_path

def get_file_preview(file_path: str, file_type: str) -> Tuple[Any, str]:
    """Get preview for a file based on its type"""
    if file_type == 'csv':
        return process_csv(file_path)
    elif file_type == 'excel':
        return process_excel(file_path)
    elif file_type == 'json':
        return process_json(file_path)
    elif file_type == 'image':
        return process_image(file_path)
    elif file_type == 'audio':
        return process_audio(file_path)
    else:
        return {}, json.dumps({"message": "Unsupported file type"})
