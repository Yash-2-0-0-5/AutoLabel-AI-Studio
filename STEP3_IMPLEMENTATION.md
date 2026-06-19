# Step 3: Gemini AI Auto-Labeling Engine - Implementation Details

## Overview

This document provides technical details on the implementation of the Gemini AI Auto-Labeling Engine for AutoLabel AI Studio.

## File Structure

```
backend/
├── services/
│   ├── __init__.py
│   └── gemini_service.py          # Core labeling service
├── routes/
│   ├── labeling.py                # API endpoints for labeling
│   └── upload.py                  # Existing upload endpoints
├── main.py                        # Updated with labeling router
└── requirements.txt               # Updated with google-generativeai
```

## Core Service Architecture

### GeminiLabelingService Class

**Location:** `backend/services/gemini_service.py`

#### Initialization

```python
service = GeminiLabelingService()
```

Initializes the service by:
1. Reading `GEMINI_API_KEY` from environment
2. Configuring Google Generative AI client
3. Setting model to `gemini-1.5-flash`
4. Logging initialization status

**Error Handling:**
- Raises `ValueError` if API key not found
- Raises `ImportError` if google-generativeai not installed

#### Key Methods

##### 1. `label_text_data(content_preview: str, file_type: str) -> Dict`

Handles CSV, Excel, and JSON data labeling.

**Process:**
1. Generate context-aware prompt based on file type
2. Call Gemini API with prompt
3. Parse JSON response with multi-strategy fallback
4. Validate response structure
5. Return `{"label": str, "confidence_score": float}`

**Example:**
```python
result = service.label_text_data(
    content_preview="{'category': 'electronics', 'price': 29.99}",
    file_type="csv"
)
# {"label": "electronics", "confidence_score": 0.95}
```

##### 2. `label_image_data(image_path: str) -> Dict`

Handles image labeling with vision API.

**Process:**
1. Verify image file exists
2. Upload image to Gemini API
3. Send multimodal prompt (text + image)
4. Parse JSON response
5. Return label and confidence

**Example:**
```python
result = service.label_image_data("storage/images/photo.jpg")
# {"label": "landscape", "confidence_score": 0.87}
```

##### 3. `label_audio_metadata(metadata: Dict) -> Dict`

Handles audio data labeling via metadata.

**Process:**
1. Format metadata as JSON
2. Create audio classification prompt
3. Call API with metadata context
4. Parse and validate response
5. Return label and confidence

**Example:**
```python
metadata = {"duration": 2.5, "sample_rate": 44100}
result = service.label_audio_metadata(metadata)
# {"label": "speech", "confidence_score": 0.84}
```

##### 4. `label_data_item(data_item) -> Tuple[str, float]`

Main routing method for any DataItem.

**Process:**
1. Detect file type from data_item.file_type
2. Route to appropriate labeling method
3. Return (label, confidence_score) tuple
4. Propagate errors with context

**Example:**
```python
label, confidence = service.label_data_item(data_item)
# ("electronics", 0.92)
```

### JSON Parsing Strategy

The service uses a multi-strategy approach to extract JSON from API responses:

#### Strategy 1: Direct Parsing
```python
result = json.loads(response_text)
```

Works when response is clean JSON.

#### Strategy 2: Markdown Extraction
```python
# Extract from ```json...```
json_match = re.search(r'\{[^{}]*\}', response_text)
result = json.loads(json_match.group())
```

Works when response contains markdown code blocks.

#### Strategy 3: Context Extraction
```python
# Find first { and last }
start_idx = response_text.find('{')
end_idx = response_text.rfind('}')
json_str = response_text[start_idx:end_idx + 1]
result = json.loads(json_str)
```

Works when response has JSON embedded in text.

#### Validation

All parsed responses are validated:

```python
def _validate_response(self, data: Dict) -> Dict:
    # Check required fields
    if {"label", "confidence_score"} != set(data.keys()):
        raise ValueError("Missing required fields")
    
    # Validate label
    if not isinstance(data["label"], str) or len(data["label"]) > 50:
        raise ValueError("Invalid label")
    
    # Validate confidence
    confidence = float(data["confidence_score"])
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("Confidence out of range")
    
    return data
```

## API Endpoints

### POST /api/datasets/{dataset_id}/process

**Handler:** `process_dataset(dataset_id, background_tasks, db)`

**Flow:**
1. Verify dataset exists
2. Verify Gemini service is initialized
3. Query unlabeled items
4. Queue background task
5. Return immediately with status

**Background Task:** `_process_dataset_background(dataset_id, item_ids)`

Executes in background:
1. Create new database session
2. For each item:
   - Call `gemini_service.label_data_item(item)`
   - Update item.final_label and item.confidence_score
   - Commit to database
   - Log result
3. Handle exceptions gracefully (continue on error)
4. Close database session

**Key Features:**
- Non-blocking: Returns immediately
- Error resilient: Continues on individual item failures
- Atomic: Each item update is committed separately
- Logged: All operations logged for debugging

### GET /api/datasets/{dataset_id}/process/status

**Handler:** `get_processing_status(dataset_id, db)`

**Returns:**
- Total items count
- Labeled items count
- Unlabeled items count
- Completion percentage
- Average confidence score

**Query:**
```python
total = db.query(DataItem).filter(DataItem.dataset_id == dataset_id).count()
labeled = db.query(DataItem).filter(
    DataItem.dataset_id == dataset_id,
    DataItem.final_label.isnot(None)
).count()
avg_confidence = sum(scores) / len(scores)
```

### POST /api/items/{item_id}/label

**Handler:** `label_single_item(item_id, db)`

**Flow:**
1. Fetch item from database
2. Call `gemini_service.label_data_item(item)`
3. Update item.final_label and item.confidence_score
4. Commit to database
5. Return result

**Error Handling:**
- `ValueError`: Returns 400 with error message
- `Exception`: Returns 500 with error details
- Missing item: Returns 404

### GET /api/items/{item_id}

**Handler:** `get_item(item_id, db)`

**Returns:** Complete item details including:
- ID, dataset_id, file_type
- Content preview (first 200 chars)
- Final label (if labeled)
- Confidence score (if labeled)
- Review status
- Created timestamp

### PUT /api/items/{item_id}/review

**Handler:** `review_item(item_id, is_reviewed, db)`

**Updates:** `DataItem.is_reviewed` flag

**Returns:** Updated status

## Prompt Engineering

### Tabular Data Prompt Template

```
Analyze the following [FILE_TYPE] data record and provide a classification label.

Data: {content_preview}

IMPORTANT: Respond ONLY with a valid JSON object (no markdown, no extra text).
The JSON must contain exactly these two keys:
- "label": A concise classification label (string, max 50 characters)
- "confidence_score": A float between 0.0 and 1.0 indicating your confidence

Example response:
{"label": "electronics", "confidence_score": 0.95}

Now classify the data above:
```

**Key Elements:**
- Clear task description
- Explicit format requirements
- Strict JSON schema definition
- Example response format
- No extra instructions

### Image Prompt Template

```
Analyze this image and provide a classification label based on its content.

IMPORTANT: Respond ONLY with a valid JSON object (no markdown, no extra text).
The JSON must contain exactly these two keys:
- "label": A concise classification label describing the main content (string, max 50 characters)
- "confidence_score": A float between 0.0 and 1.0 indicating your confidence

Example response:
{"label": "landscape", "confidence_score": 0.85}

Now classify the image:
```

### Audio Prompt Template

```
Analyze the following audio content and provide a classification label.

Content: {metadata_json}

IMPORTANT: Respond ONLY with a valid JSON object (no markdown, no extra text).
The JSON must contain exactly these two keys:
- "label": A classification label for the audio content (string, max 50 characters)
- "confidence_score": A float between 0.0 and 1.0 indicating your confidence

Example response:
{"label": "speech", "confidence_score": 0.88}

Now classify the audio:
```

## Error Handling Strategy

### API Errors

```python
except self.client.APIError as e:
    logger.error(f"Gemini API error: {str(e)}")
    raise ValueError(f"Gemini API error: {str(e)}")
```

Catches:
- Rate limit exceeded
- Invalid API key
- Service unavailable
- Quota exceeded

### JSON Parse Errors

```python
except json.JSONDecodeError:
    # Try next parsing strategy
```

Multi-strategy parsing prevents single-point failures.

### Validation Errors

```python
except ValueError as e:
    logger.error(f"Validation error: {str(e)}")
    raise ValueError(f"Response validation failed: {str(e)}")
```

Detailed error messages help debugging.

### File Not Found

```python
except FileNotFoundError as e:
    logger.error(f"Image file error: {str(e)}")
    raise ValueError(str(e))
```

Specific error for image/audio files.

## Testing

### Unit Tests (`test_gemini_service.py`)

**Test Suite 1: JSON Parsing (8 cases)**
- Valid JSON
- JSON with markdown
- JSON with extra text
- JSON with newlines
- Missing fields
- Out-of-range values
- Wrong data types
- Oversized labels

**Test Suite 2: Prompt Generation**
- Tabular data prompt
- Image prompt
- Audio prompt

**Test Suite 3: Service Initialization**
- Missing API key
- Valid API key

**Test Suite 4: Error Handling (4 cases)**
- Empty response
- Invalid JSON
- Non-dict response
- Null values

**Test Suite 5: Database Integration**
- Database existence
- Table verification
- Data item count
- Sample data retrieval

### Integration Testing

Manual workflow:
1. Run `test_upload.py` to create test data
2. Start backend: `uvicorn main:app --reload`
3. Label dataset: `curl -X POST http://localhost:8000/api/datasets/1/process`
4. Check status: `curl http://localhost:8000/api/datasets/1/process/status`
5. Query results: `curl http://localhost:8000/api/items/1`

## Performance Metrics

### Single Item Labeling
- Time: ~2-3 seconds (depends on API latency)
- API calls: 1 per item
- Database operations: 1 update

### Batch Processing (10 items)
- Time: ~20-30 seconds (sequential)
- API calls: 10 total
- Database operations: 10 updates
- Memory: Minimal (streaming)

### Error Recovery
- Failures are logged but don't stop batch processing
- Average retry time: < 5 seconds per item
- Database consistency: Maintained per-item

## Dependencies

**New Requirements:**
```
google-generativeai>=0.6.0
```

**Why:**
- Official Google SDK for Generative AI
- Handles authentication
- Manages API requests
- Provides streaming and non-streaming interfaces

## Future Enhancements

1. **Streaming Responses**
   - Use streaming API for large batches
   - Reduce latency

2. **Caching**
   - Cache identical inputs
   - Reduce API calls

3. **Batch Requests**
   - Group similar items
   - Optimize API usage

4. **Custom Models**
   - Fine-tune on domain-specific data
   - Improve accuracy

5. **Human-in-the-Loop**
   - Flag low-confidence items
   - Request manual review
   - Iterative improvement

6. **Multi-Stage Labeling**
   - Multiple classifiers per item
   - Ensemble voting
   - Higher accuracy

## Security Considerations

1. **API Key Protection**
   - Never commit to git
   - Use environment variables
   - Rotate regularly

2. **Rate Limiting**
   - Implement quota tracking
   - Queue requests intelligently
   - Alert on excessive usage

3. **Data Privacy**
   - Don't send sensitive data to API without consent
   - Review Google's data retention policy
   - Consider on-premise alternatives

4. **Error Messages**
   - Don't expose API keys in errors
   - Log errors securely
   - Sanitize stack traces
