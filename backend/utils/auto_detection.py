from typing import Dict, Tuple
import json

LABELING_STRATEGIES = {
    'csv': {
        'strategy_type': 'Text Classification',
        'description': 'Suitable for tabular data with text content',
        'parameters': {
            'task_type': 'multi-class-classification',
            'input_columns': 'auto-detect',
            'label_suggestions': 'frequency-based'
        }
    },
    'excel': {
        'strategy_type': 'Structured Data Labeling',
        'description': 'For tabular data in spreadsheet format',
        'parameters': {
            'task_type': 'record-classification',
            'preserve_formatting': True,
            'aggregate_mode': 'row-based'
        }
    },
    'json': {
        'strategy_type': 'Key-Value Labeling',
        'description': 'For hierarchical and structured JSON data',
        'parameters': {
            'task_type': 'nested-structure-labeling',
            'path_based_tagging': True
        }
    },
    'image': {
        'strategy_type': 'Image Labeling',
        'description': 'For image classification, object detection, and semantic segmentation',
        'parameters': {
            'task_type': 'image-classification',
            'sub_tasks': ['classification', 'bounding-box', 'segmentation'],
            'annotation_tool': 'canvas-based'
        }
    },
    'audio': {
        'strategy_type': 'Audio Labeling',
        'description': 'For speech recognition, emotion detection, and sound classification',
        'parameters': {
            'task_type': 'audio-classification',
            'sub_tasks': ['classification', 'transcription', 'emotion-detection'],
            'annotation_tool': 'waveform-based'
        }
    }
}

def recommend_strategy(file_type: str) -> Dict:
    """Recommend labeling strategy based on file type"""
    if file_type in LABELING_STRATEGIES:
        return LABELING_STRATEGIES[file_type]
    else:
        return {
            'strategy_type': 'Manual Labeling',
            'description': 'Manual labeling required for this file type',
            'parameters': {'task_type': 'custom'}
        }

def analyze_structure(file_type: str, structure_json: str) -> Dict:
    """Analyze file structure and provide insights"""
    try:
        structure = json.loads(structure_json)
    except:
        return {}

    insights = {}

    if file_type == 'csv' or file_type == 'excel':
        insights = {
            'column_count': len(structure.get('columns', [])),
            'row_count': structure.get('total_rows', 0),
            'columns': structure.get('columns', []),
            'recommendation': 'Consider text classification or NER for text columns'
        }
    elif file_type == 'json':
        insights = {
            'structure_type': structure.get('type', 'unknown'),
            'item_count': structure.get('item_count', 0),
            'recommendation': 'Use key-value labeling for nested structure'
        }
    elif file_type == 'image':
        insights = {
            'format': structure.get('format'),
            'dimensions': structure.get('size'),
            'color_mode': structure.get('mode'),
            'recommendation': 'Use image classification or object detection'
        }
    elif file_type == 'audio':
        insights = {
            'duration': structure.get('duration_seconds'),
            'sample_rate': structure.get('frame_rate'),
            'channels': structure.get('channels'),
            'recommendation': 'Use transcription or emotion detection labeling'
        }

    return insights

def get_optimal_batch_size(file_type: str, item_count: int) -> int:
    """Recommend batch size for processing"""
    if file_type in ['image', 'audio']:
        return max(10, min(50, item_count // 10))
    elif file_type in ['csv', 'excel']:
        return max(100, min(500, item_count // 5))
    else:
        return 100
