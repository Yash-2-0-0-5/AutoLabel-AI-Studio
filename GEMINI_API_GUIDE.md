# AutoLabel AI Studio - Gemini AI Labeling Engine

## Overview

The Gemini AI Labeling Engine provides automatic data labeling using Google's Generative AI models. It supports multiple data types with intelligent prompt engineering and strict JSON validation.

## Architecture

### Core Components

1. **GeminiLabelingService** (`backend/services/gemini_service.py`)
   - Initializes with Google Generative AI SDK
   - Handles file type-specific labeling strategies
   - Implements robust JSON parsing and validation
   - Provides error handling for API failures

2. **Labeling Routes** (`backend/routes/labeling.py`)
   - Background task processing for batch labeling
   - Single-item labeling endpoint
   - Processing status tracking
   - Item review workflow

## Setup

### 1. Install Dependencies

```bash
pip install google-generativeai
```

### 2. Configure API Key

Set the `GEMINI_API_KEY` environment variable:

```bash
# In .env file
GEMINI_API_KEY=your-actual-gemini-api-key
```

Get your API key from: https://aistudio.google.com/app/apikey

### 3. Verify Installation

```python
from services.gemini_service import GeminiLabelingService

service = GeminiLabelingService()
# Should initialize without errors
```

## API Endpoints

### 1. Process Dataset (Background Task)

**Endpoint:** `POST /api/datasets/{dataset_id}/process`

Starts background processing of all unlabeled items in a dataset using Gemini AI.

**Request:**
```bash
curl -X POST http://localhost:8000/api/datasets/1/process
```

**Response:**
```json
{
  "status": "processing",
  "dataset_id": 1,
  "queued_items": 5,
  "message": "Started processing 5 items in background"
}
```

**Status Codes:**
- `200`: Processing started successfully
- `404`: Dataset not found
- `503`: Gemini service not initialized

### 2. Get Processing Status

**Endpoint:** `GET /api/datasets/{dataset_id}/process/status`

Get the labeling completion status for a dataset.

**Request:**
```bash
curl http://localhost:8000/api/datasets/1/process/status
```

**Response:**
```json
{
  "dataset_id": 1,
  "total_items": 5,
  "labeled_items": 3,
  "unlabeled_items": 2,
  "completion_percentage": 60.0,
  "average_confidence": 0.8825
}
```

### 3. Label Single Item (Immediate)

**Endpoint:** `POST /api/items/{item_id}/label`

Labels a single item immediately and returns the result.

**Request:**
```bash
curl -X POST http://localhost:8000/api/items/1/label
```

**Response:**
```json
{
  "item_id": 1,
  "label": "electronics",
  "confidence_score": 0.92,
  "status": "success"
}
```

**Status Codes:**
- `200`: Label generated successfully
- `400`: Validation error (malformed JSON from API, etc.)
- `404`: Item not found
- `500`: Server error
- `503`: Gemini service not initialized

### 4. Get Item Details

**Endpoint:** `GET /api/items/{item_id}`

Retrieve details of a specific data item.

**Request:**
```bash
curl http://localhost:8000/api/items/1
```

**Response:**
```json
{
  "id": 1,
  "dataset_id": 1,
  "file_type": "csv",
  "content_preview": "{'text': 'Great product!', 'category': 'electronics'}",
  "final_label": "electronics",
  "confidence_score": 0.92,
  "is_reviewed": false,
  "created_at": "2026-06-18T20:46:30.915194"
}
```

### 5. Review Item

**Endpoint:** `PUT /api/items/{item_id}/review`

Mark an item as reviewed after inspection.

**Request:**
```bash
curl -X PUT http://localhost:8000/api/items/1/review \
  -H "Content-Type: application/json" \
  -d '{"is_reviewed": true}'
```

**Response:**
```json
{
  "item_id": 1,
  "is_reviewed": true,
  "status": "success"
}
```

## JSON Response Schema

All labels are returned with the following strict schema:

```json
{
  "label": "string (1-50 characters)",
  "confidence_score": "number (0.0 to 1.0)"
}
```

**Validation Rules:**
- `label`: Required, string type, 1-50 characters, trimmed of whitespace
- `confidence_score`: Required, float type, must be between 0.0 and 1.0 (inclusive)

## Labeling Strategies by File Type

### CSV/Excel/JSON (Tabular Data)

**Strategy:** Text Classification

**Prompt Pattern:**
```
Analyze the following [FILE_TYPE] data record and provide a classification label.

Data: {content_preview}

IMPORTANT: Respond ONLY with a valid JSON object...
```

**Example:**
```python
result = service.label_text_data(
    content_preview="{'text': 'Excellent service!', 'category': 'restaurant'}",
    file_type="csv"
)
# Returns: {"label": "positive", "confidence_score": 0.89}
```

### Images

**Strategy:** Visual Classification

**Capabilities:**
- Image classification (object, scene, concept)
- Content description
- Confidence scoring

**Implementation:**
```python
result = service.label_image_data(image_path="/path/to/image.jpg")
# Returns: {"label": "landscape", "confidence_score": 0.87}
```

### Audio

**Strategy:** Audio Metadata Analysis

**Capabilities:**
- Classification based on metadata (duration, sample rate)
- Content type inference
- Confidence scoring

**Implementation:**
```python
metadata = {
    "duration_seconds": 2.5,
    "sample_rate": 44100,
    "channels": 2
}
result = service.label_audio_metadata(metadata)
# Returns: {"label": "speech", "confidence_score": 0.84}
```

## Error Handling

### Robust JSON Parsing

The service attempts to extract valid JSON from API responses in this order:

1. **Direct JSON parsing** - If response is valid JSON
2. **Markdown extraction** - If response contains ```json...```
3. **Regex extraction** - If response contains {...}
4. **Context extraction** - Finds first `{` and last `}` and parses between

### Common Errors and Solutions

#### 1. Missing API Key

```
ValueError: GEMINI_API_KEY environment variable not set.
```

**Solution:**
```bash
export GEMINI_API_KEY=your-api-key
```

#### 2. Malformed JSON Response

```
ValueError: Could not parse valid JSON from response
```

**Solution:**
- Service automatically retries with multiple parsing strategies
- If still failing, check API response in logs
- Ensure API key is valid and has sufficient quota

#### 3. Validation Errors

```
ValueError: Field 'confidence_score' must be between 0.0 and 1.0
```

**Solution:**
- API response contained invalid data
- Service sanitizes and validates all responses
- Check error logs for specific issues

#### 4. API Rate Limits

```
ValueError: Gemini API error: Resource has been exhausted
```

**Solution:**
- Implement retry logic with exponential backoff
- Implement request queuing
- Contact Google Cloud support for quota increase

## Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your-api-key

# Optional
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
DATABASE_URL=sqlite:///./autolabel.db
```

### Model Selection

Currently uses: `gemini-1.5-flash`

To use different model:
```python
# Modify in gemini_service.py
self.model = "gemini-pro"  # or other model
```

## Example Workflow

### 1. Upload Dataset

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@reviews.csv" \
  -F "dataset_name=review_dataset"
```

Response: `dataset_id: 1`

### 2. Check Processing Status

```bash
curl http://localhost:8000/api/datasets/1/process/status
```

Response:
```json
{
  "total_items": 5,
  "labeled_items": 0,
  "unlabeled_items": 5,
  "completion_percentage": 0.0
}
```

### 3. Start Background Processing

```bash
curl -X POST http://localhost:8000/api/datasets/1/process
```

### 4. Monitor Progress

```bash
# Poll status endpoint
curl http://localhost:8000/api/datasets/1/process/status
```

Wait for `completion_percentage` to reach 100.

### 5. Review Results

```bash
# Get individual items
curl http://localhost:8000/api/items/1

# Mark as reviewed
curl -X PUT http://localhost:8000/api/items/1/review \
  -H "Content-Type: application/json" \
  -d '{"is_reviewed": true}'
```

## Testing

### Run Core Implementation Tests

```bash
python test_gemini_service.py
```

Tests cover:
- JSON parsing and validation (8 test cases)
- Prompt generation (3 types)
- Service initialization
- Error handling (4 scenarios)
- Database integration

All tests pass without requiring actual API calls.

### Manual API Testing

```bash
# 1. Start backend
cd backend
python -m uvicorn main:app --reload

# 2. Upload test data
python ../test_upload.py

# 3. Label items
curl -X POST http://localhost:8000/api/datasets/1/process
curl http://localhost:8000/api/datasets/1/process/status
```

## Performance Considerations

### Batch Processing
- Items are processed sequentially (one at a time)
- Each API call is independent
- Implement request queuing for large datasets

### Rate Limiting
- Google API has rate limits based on billing plan
- Implement exponential backoff for retries
- Monitor quota usage in Google Cloud Console

### Cost Optimization
- Use `gemini-1.5-flash` for lower cost
- Batch similar items for more efficient processing
- Cache responses when appropriate

## Logging

Logs are output to console with timestamps:

```
2026-06-18 20:46:30,123 - services.gemini_service - INFO - Initialized Gemini service with model: gemini-1.5-flash
2026-06-18 20:46:35,456 - services.gemini_service - INFO - Successfully labeled CSV data: label=electronics, confidence=0.95
```

Enable DEBUG logging:

```bash
export LOG_LEVEL=DEBUG
```

## Troubleshooting

### Issue: Service fails to initialize

**Check:**
- API key is set: `echo $GEMINI_API_KEY`
- google-generativeai is installed: `pip list | grep google`
- Network connectivity

### Issue: Labels are inconsistent

**Check:**
- Different prompt styles may affect results
- Confidence score indicates model uncertainty
- Review low-confidence results manually

### Issue: Processing stalled

**Check:**
- Background task logs for errors
- Database connection is active
- API quota not exceeded

### Issue: Invalid JSON parsing

**Check:**
- API response format in logs
- Ensure all special characters are escaped
- Try with different model version

## Support

For issues with:
- **Google Generative AI SDK**: https://github.com/google/generative-ai-python
- **AutoLabel AI Studio**: Check CLAUDE.md documentation
- **API Rate Limits**: Google Cloud Console quotas page
