# Step 5: Active Learning, Local Model Retraining & Export

## Overview

This step implements an advanced active learning workflow where the system learns from human corrections and gradually shifts from expensive API calls (Gemini) to efficient local inference. It also provides multiple export formats for downstream use.

## Architecture

### Components

1. **LocalModelTrainer** (`backend/services/model_training.py`)
   - Trains sklearn/xgboost models on reviewed data
   - Manages model persistence and metadata
   - Provides inference interface

2. **ExportService** (`backend/services/export_service.py`)
   - Exports datasets in multiple formats
   - Generates ML-ready training data
   - Creates deployable ZIP packages

3. **Enhanced Labeling Pipeline**
   - Check for local model first (confidence >= 0.7)
   - Fall back to Gemini API if no local model or low confidence
   - Log which model was used for each prediction

4. **Auto-Retraining Trigger**
   - Every 10 reviewed items, automatically retrain model
   - Manual trigger via API endpoint
   - Background task processing

## Features

### 1. Local Model Training

**Models Supported:**
- LogisticRegression (lightweight, fast)
- RandomForest (more powerful, slower)
- Default: LogisticRegression

**Training Process:**
1. Collect reviewed items (is_reviewed=True)
2. Vectorize text using TfidfVectorizer
3. Train classifier on 80% of data
4. Evaluate on 20% test set
5. Save model + vectorizer + metadata

**Feature Engineering:**
- TF-IDF vectorization
- Unigrams + bigrams (1-2 grams)
- Max 1000 features
- Min doc frequency: 1
- Max doc frequency: 0.9
- English stop words removed

**Evaluation Metrics:**
- Accuracy
- Precision (weighted)
- Recall (weighted)
- F1-Score (weighted)

**Metadata Stored:**
```json
{
  "dataset_id": 1,
  "dataset_name": "reviews",
  "model_type": "logistic_regression",
  "training_date": "2026-06-19T10:30:00",
  "training_samples": 50,
  "n_classes": 5,
  "classes": ["electronics", "clothing", "furniture", ...],
  "test_samples": 10,
  "accuracy": 0.92,
  "precision": 0.91,
  "recall": 0.90,
  "f1_score": 0.91,
  "n_features": 1000,
  "vectorizer_params": {...}
}
```

### 2. Intelligent Labeling Pipeline

**Decision Tree:**
```
For each item:
  ├─ Is file_type in [csv, excel, json]?
  │  ├─ YES: Check for local model
  │  │  ├─ Model exists AND confidence >= 0.7?
  │  │  │  ├─ YES: Use local model
  │  │  │  └─ NO: Fall back to Gemini
  │  │  └─ No model: Use Gemini
  │  └─ NO: Use Gemini (for images, audio)
  └─ Return (label, confidence, model_used)
```

**Benefits:**
- Cost reduction: Local model for confident predictions
- Speed: Local models are 10-100x faster than API
- Fallback safety: API ensures no low-confidence predictions
- Continuous learning: Models improve with more corrections

### 3. Auto-Retraining Trigger

**When Triggered:**
- Every 10 human corrections (every multiple of 10 reviewed items)
- Manual trigger via `/api/datasets/{id}/train-model`

**Automatic Flow:**
1. User corrects label (is_reviewed=True)
2. Count reviewed items in dataset
3. If count % 10 == 0, queue background training
4. Background task trains new model
5. Model becomes active immediately

**Example:**
```
Correction 1-9:  No training
Correction 10:   Training triggered (queue background)
Correction 11-19: No training
Correction 20:   Training triggered (queue background)
```

### 4. Hybrid Inference Strategy

**Config:**
- Local model confidence threshold: 0.7
- If local confidence < 0.7: Fall back to Gemini
- Gemini returns confidence 1.0 for high-confidence predictions

**Benefits:**
- Best of both worlds
- Cost control: Reduce API calls by 70-90%
- Quality: Maintain accuracy with API fallback
- Learning: Continuous model improvement

## Export Functionality

### Export Formats

#### 1. CSV Export
**Contents:**
- ID, content_preview, file_type, final_label, confidence_score, is_reviewed, created_at
- All items included
- Human-readable format

**Use Case:** Spreadsheet analysis, data review

#### 2. JSON Export
**Structure:**
```json
{
  "metadata": {
    "dataset_id": 1,
    "dataset_name": "reviews",
    "total_items": 100,
    "labeled_items": 95,
    "reviewed_items": 50,
    "average_confidence": 0.82
  },
  "items": [
    {
      "id": 1,
      "content_preview": "...",
      "final_label": "electronics",
      "confidence_score": 0.92,
      "is_reviewed": true
    }
  ]
}
```

**Use Case:** API/database import, structured data access

#### 3. ML-Ready CSV
**Contents:**
- Only reviewed items (is_reviewed=True)
- Only labeled items (final_label != NULL)
- Columns: text, label
- Ready for model training

**Use Case:** Training external models, sharing cleaned data

#### 4. ZIP Archive
**Contains:**
- `metadata.json` - Dataset metadata
- `dataset.csv` - Complete CSV export
- `dataset.json` - Complete JSON export
- `dataset_ml_ready.csv` - ML-ready format
- `images/` - Original image files
- `audio/` - Original audio files
- `MANIFEST.json` - File descriptions

**Use Case:** Complete dataset sharing, deployment packages

### Export Endpoints

```
GET /api/datasets/{id}/export/csv
  → Download dataset.csv

GET /api/datasets/{id}/export/json
  → Download dataset.json

GET /api/datasets/{id}/export/ml-ready
  → Download dataset_ml_ready.csv

GET /api/datasets/{id}/export/zip
  → Download dataset_export.zip

GET /api/exports
  → List all available exports
```

## Model Management

### Endpoints

```
GET /api/models
  → List all trained models

GET /api/models/{dataset_id}
  → Get model metadata

POST /api/datasets/{dataset_id}/train-model
  → Manually trigger training

POST /api/models/{dataset_id}/delete
  → Delete model and artifacts
```

## Complete Workflow

### Step-by-Step

1. **Upload Dataset**
   ```
   POST /api/upload
   → Creates dataset with items
   ```

2. **Start AI Labeling (Gemini)**
   ```
   POST /api/datasets/{id}/process
   → All items labeled with Gemini
   → Confidence varies (0.5-0.95)
   ```

3. **User Reviews & Corrects (Human-in-the-Loop)**
   ```
   PUT /api/items/{id}/correct
   → Correct labels manually
   → Set is_reviewed=True, confidence=1.0
   ```

4. **Auto-Retraining Triggered**
   ```
   After 10 corrections:
   → Background training starts
   → Local model trained on reviewed data
   → Model saved with metadata
   ```

5. **Next Batch Uses Local Model**
   ```
   POST /api/datasets/{new_id}/process
   → For same type dataset:
     ├─ Check for existing model
     ├─ If confidence >= 0.7: Use local model (fast!)
     └─ Else: Fall back to Gemini (safe!)
   ```

6. **More Corrections**
   ```
   User corrects more items
   → After 20, 30, 40... corrections
   → Model continuously improves
   ```

7. **Export Clean Data**
   ```
   GET /api/datasets/{id}/export/zip
   → Get complete dataset
   → Ready for deployment/sharing
   ```

## Retraining Logic Deep Dive

### Trigger Conditions

```python
# In correct_item_label():
reviewed_count = count(is_reviewed=True)
if reviewed_count % 10 == 0:
    queue_background_training(dataset_id)
```

### Training Data

- **Only** reviewed items (is_reviewed=True)
- **Only** labeled items (final_label is not NULL)
- Examples: User-corrected labels (confidence=1.0)
- No Gemini-only predictions (to avoid bias)

### Model Quality

With more corrections:
- Training samples increase (10 → 20 → 30...)
- Class distribution becomes more representative
- Feature coverage improves
- Model accuracy typically improves

### Fallback Safety

If local model confidence < 0.7:
- Don't use prediction
- Fall back to Gemini API
- Gemini has higher accuracy (98%+)
- Ensures quality threshold maintained

## Cost Reduction Analysis

### Scenario: Dataset with 100 items

**All Gemini (Baseline):**
```
100 items × Gemini cost = 100 units
Time: 100 × 2s = 200s
```

**With Active Learning:**
```
Gemini: 30 items = 30 units (initial 30%)
Local: 70 items = 0 units (70% cost savings!)
Time: 30 × 2s + 70 × 0.1s = 67s (3x faster)

Cost reduction: 70%
Speed improvement: 3x
```

## Implementation Details

### LocalModelTrainer Methods

```python
class LocalModelTrainer:
    def train_model(dataset_id, texts, labels) -> Dict
        # Train and save model
        # Return metadata with metrics

    def predict(dataset_id, text) -> Tuple[str, float]
        # Load model and vectorizer
        # Return (label, confidence)

    def model_exists(dataset_id) -> bool
        # Check if model file exists

    def get_metadata(dataset_id) -> Dict
        # Load metadata.json

    def delete_model(dataset_id) -> bool
        # Delete model artifacts

    def list_models() -> List[Dict]
        # Get all models with metadata
```

### ExportService Methods

```python
class ExportService:
    def export_to_csv(dataset, items) -> str
    def export_to_json(dataset, items) -> str
    def export_to_ml_ready_csv(dataset, items) -> str
    def export_to_zip(dataset, items) -> bytes
    def save_export_file(dataset, items, format) -> str
    def list_exports() -> List[Dict]
    def cleanup_old_exports(days=7) -> int
```

## Directory Structure

```
backend/
├── services/
│   ├── gemini_service.py (updated with local model integration)
│   ├── model_training.py (NEW)
│   └── export_service.py (NEW)
├── routes/
│   ├── labeling.py (updated with training triggers)
│   └── export.py (NEW)
└── models/
    ├── dataset_1_model.pkl (trained model)
    ├── dataset_1_vectorizer.pkl (vectorizer)
    └── dataset_1_metadata.json (metadata)

exports/
├── dataset_1_2026-06-19_10-30-00.csv
├── dataset_1_2026-06-19_10-30-00.json
└── dataset_1_2026-06-19_10-30-00.zip
```

## Future Enhancements

1. **Advanced Models**
   - XGBoost for better performance
   - Neural networks for complex patterns
   - Ensemble methods (voting)

2. **Feature Engineering**
   - Domain-specific features
   - Embeddings (Word2Vec, BERT)
   - Feature selection

3. **Active Learning Strategies**
   - Uncertainty sampling
   - Query by committee
   - Expected model change

4. **Model Versioning**
   - Track model history
   - Rollback to previous versions
   - A/B testing

5. **Monitoring & Analytics**
   - Model performance over time
   - Drift detection
   - Cost tracking
   - Accuracy metrics

## Configuration

### Thresholds

```python
# Local model confidence threshold
LOCAL_MODEL_CONFIDENCE_THRESHOLD = 0.7

# Retraining trigger
RETRAINING_INTERVAL = 10  # Every 10 reviewed items

# Minimum training samples
MIN_TRAINING_SAMPLES = 2
```

### Model Parameters

```python
# TfidfVectorizer
MAX_FEATURES = 1000
MIN_DF = 1
MAX_DF = 0.9
NGRAM_RANGE = (1, 2)

# LogisticRegression
MAX_ITER = 1000
RANDOM_STATE = 42

# Train-test split
TEST_SIZE = 0.2
RANDOM_STATE = 42
```

## Security & Best Practices

1. **Model Isolation**
   - One model per dataset type
   - Models stored locally (no remote exposure)
   - Access controlled via API

2. **Data Privacy**
   - Models trained only on user's data
   - No data sent to external services (except Gemini fallback)
   - Clean exports exclude sensitive metadata

3. **Quality Assurance**
   - Confidence thresholds prevent low-quality predictions
   - Evaluation metrics tracked
   - Fallback system ensures safety

4. **Performance**
   - Lazy loading of models
   - Caching where appropriate
   - Background training doesn't block UI

## Summary

Step 5 creates a sophisticated active learning system where:
- Human corrections improve local models
- Local models reduce costs by 70%+
- Gemini API provides safety net
- Complete export functionality for any use case
- Continuous improvement with every correction

The system balances cost, speed, and quality automatically.
