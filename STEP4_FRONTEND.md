# Step 4: Frontend UI and Human-in-the-Loop Workflow

## Overview

The AutoLabel AI Studio frontend provides a complete user interface for managing datasets, reviewing AI-generated labels, and correcting them with a human-in-the-loop workflow.

## Architecture

### Technology Stack

- **React 18.3.1** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Axios** - HTTP client for API calls

### Component Structure

```
frontend/src/
├── App.jsx                 # Main application with routing/tabs
├── api/
│   └── client.js          # Centralized API client
├── components/
│   ├── UploadSection.jsx   # Drag-and-drop file upload
│   ├── DatasetsList.jsx    # Dataset cards grid
│   ├── DatasetView.jsx     # Dataset items table with labeling controls
│   ├── ReviewQueue.jsx     # Prioritized review queue (low confidence)
│   └── CorrectionModal.jsx # Modal for label correction
└── index.css              # Tailwind CSS imports
```

## Features

### 1. Upload Section

**Location:** `frontend/src/components/UploadSection.jsx`

Features:
- Drag-and-drop interface
- File input browser
- Optional dataset name
- Real-time upload progress
- Success/error notifications
- Supports: CSV, Excel, JSON, Images, Audio

**API Integration:**
```javascript
uploadApi.uploadFile(file, datasetName)
// POST /api/upload
```

**State Management:**
- `isDragging` - Visual feedback during drag
- `isLoading` - Prevent double-upload
- `error` - Display error messages
- `success` - Show upload confirmation
- `datasetName` - Optional dataset naming

### 2. Datasets List

**Location:** `frontend/src/components/DatasetsList.jsx`

Features:
- Grid layout of dataset cards
- File type icons
- Creation timestamp
- Clickable to view dataset
- Auto-refresh every 5 seconds
- Empty state handling

**API Integration:**
```javascript
datasetsApi.list()
// GET /api/datasets
```

### 3. Dataset View

**Location:** `frontend/src/components/DatasetView.jsx`

Features:
- Table view of all items in dataset
- Columns: ID, Preview, AI Label, Confidence, Status, Action
- Real-time progress bar showing labeling completion
- Color-coded confidence scores (red < 0.6, yellow 0.6-0.8, green > 0.8)
- "Start AI Labeling" button to begin background processing
- Auto-polling for status updates (2 seconds)
- Click any row to open correction modal

**API Integration:**
```javascript
datasetsApi.get(datasetId)              // GET /api/datasets/{id}
datasetsApi.getItems(datasetId)         // GET /api/datasets/{id}/items
datasetsApi.getStatus(datasetId)        // GET /api/datasets/{id}/process/status
datasetsApi.process(datasetId)          // POST /api/datasets/{id}/process
```

**Confidence Color Coding:**
- Green (1.0): Perfect confidence / manually corrected
- Light Green (0.8-1.0): High confidence
- Yellow (0.6-0.8): Medium confidence
- Red (< 0.6): Low confidence - needs review

### 4. Review Queue

**Location:** `frontend/src/components/ReviewQueue.jsx`

**Purpose:** Prioritized view for human-in-the-loop corrections

**Filtering Logic:**
Items appear in review queue if:
- Confidence score < 0.7 OR
- is_reviewed == False
- AND has a final_label

**Priority Levels:**
- **CRITICAL:** Confidence < 0.5 AND not reviewed
- **HIGH:** Not reviewed
- **MEDIUM:** Confidence < 0.7

**Stats Display:**
- Critical items count (red card)
- High priority items count (orange card)
- Total in queue count (blue card)

**Features:**
- Auto-refresh every 3 seconds
- Sorted by confidence (lowest first)
- Shows dataset name for multi-dataset view
- One-click correction via modal
- Removes from queue after correction

**API Integration:**
```javascript
datasetsApi.list()                      // GET /api/datasets
datasetsApi.getItems(datasetId)         // GET /api/datasets/{id}/items
```

### 5. Correction Modal

**Location:** `frontend/src/components/CorrectionModal.jsx`

**Features:**
- Shows item preview
- Displays AI-assigned label and confidence
- Input field for corrected label
- Character counter (max 50 chars)
- Error handling and validation
- Submit and cancel buttons

**Validation:**
- Label required (non-empty)
- Max 50 characters
- Trimmed of whitespace

**API Integration:**
```javascript
itemsApi.correctLabel(itemId, correctedLabel)
// PUT /api/items/{id}/correct
// Updates: final_label, confidence_score (→ 1.0), is_reviewed (→ True)
```

**Response:**
```json
{
  "item_id": 1,
  "final_label": "corrected_label",
  "confidence_score": 1.0,
  "is_reviewed": true,
  "status": "success"
}
```

## API Client

**Location:** `frontend/src/api/client.js`

Centralized API client using Axios with three main namespaces:

### datasetsApi

```javascript
datasetsApi.list()                    // Get all datasets
datasetsApi.get(datasetId)           // Get specific dataset
datasetsApi.getItems(datasetId)      // Get items in dataset
datasetsApi.getStatus(datasetId)     // Get processing status
datasetsApi.process(datasetId)       // Start AI labeling
```

### uploadApi

```javascript
uploadApi.uploadFile(file, datasetName)  // Upload file
```

### itemsApi

```javascript
itemsApi.get(itemId)                     // Get item details
itemsApi.label(itemId)                   // Label single item
itemsApi.correctLabel(itemId, label)    // Correct label (NEW)
itemsApi.review(itemId, isReviewed)     // Mark reviewed
```

## Navigation & Views

### Main App (App.jsx)

**Tabs:**
1. **Dashboard** - Upload + Datasets list
2. **Review Queue** - Prioritized items for correction

**Header:**
- Application title
- Backend health indicator
- Tab navigation
- Responsive design

## Human-in-the-Loop Workflow

### Complete User Journey

1. **Upload Dataset**
   - User drags/drops file or browses for file
   - Optional: Enter dataset name
   - System creates dataset and items

2. **View Datasets**
   - User sees all uploaded datasets in grid
   - Clicks dataset to view details

3. **Start AI Labeling** (Optional)
   - User clicks "Start AI Labeling" button
   - System processes items in background
   - Progress bar updates in real-time

4. **Review Items**
   - Two options:
     - Option A: Visit specific dataset
     - Option B: Go to Review Queue for all low-confidence items

5. **Correct Labels**
   - User clicks "Edit" button on any item
   - Modal opens with current label and preview
   - User enters corrected label
   - User clicks "Confirm"

6. **Database Update**
   - PUT /api/items/{id}/correct endpoint called
   - final_label updated
   - confidence_score set to 1.0
   - is_reviewed set to True
   - Modal closes
   - Item removed from review queue (if in queue view)

7. **Verification**
   - User can verify changes in dataset view
   - Items with confidence=1.0 show as green
   - Reviewed items marked with "Reviewed" badge

## Styling

### Tailwind CSS Classes

**Color Scheme:**
- Primary: Blue (#2563EB)
- Success: Green (#16A34A)
- Warning: Yellow/Orange
- Danger: Red (#DC2626)
- Neutral: Gray

**Component Patterns:**
- Cards with shadow and border
- Rounded corners (lg)
- Hover states on interactive elements
- Loading spinners
- Badge/tag styling
- Form inputs with focus rings
- Modal with backdrop overlay

## Error Handling

### API Errors

All components handle:
- Network connection errors
- 404 Not Found
- 400 Bad Request (validation errors)
- 500 Server errors
- Timeout errors

**Error Display:**
- Red alert boxes with error message
- User-friendly error descriptions
- Retry buttons where appropriate

### Validation Errors

**Upload:**
- No file selected
- Unsupported file type
- Upload failed

**Correction Modal:**
- Empty label
- Label too long (> 50 chars)
- Server validation errors

## Performance

### Polling Strategy

- **Dataset view:** 2 second interval for status updates
- **Review queue:** 3 second interval for item list refresh
- **Datasets list:** 5 second interval for new datasets
- All polling stops on component unmount

### Optimization

- Conditional rendering (loading states)
- Memo where appropriate (future)
- Efficient list updates (map with key)
- No unnecessary re-renders

## Testing

### Test Coverage (test_frontend_workflow.py)

**5 Test Suites:**

1. **Backend Endpoint Verification**
   - Checks all required endpoints exist
   - Validates API structure

2. **Label Correction Endpoint**
   - Tests PUT /api/items/{id}/correct
   - Verifies database update
   - Checks confidence_score = 1.0
   - Checks is_reviewed = True

3. **Review Queue Logic**
   - Tests item filtering (confidence < 0.7 OR not reviewed)
   - Tests priority level assignment
   - Verifies sorting

4. **API Client Structure**
   - Validates all API methods exist
   - Checks method signatures

5. **Workflow Flow**
   - Documents complete user workflow
   - Lists all API endpoints in order
   - Shows input/output for each step

**Run Tests:**
```bash
python test_frontend_workflow.py
```

**Result:** 5/5 test suites PASS

## Future Enhancements

1. **Bulk Operations**
   - Select multiple items
   - Bulk correct labels
   - Bulk mark as reviewed

2. **Export Functionality**
   - Export to CSV/JSON
   - Download corrected dataset
   - Include metadata

3. **Analytics Dashboard**
   - Charts showing confidence distribution
   - Labeling completion over time
   - Error rate metrics
   - Top mislabeled categories

4. **Advanced Filtering**
   - Filter by date range
   - Filter by confidence range
   - Filter by category
   - Multi-criteria filtering

5. **Batch Upload**
   - Multiple file upload
   - Recursive folder upload
   - Progress for each file

6. **Label Suggestions**
   - Autocomplete suggestions
   - Category dropdown
   - Common labels list

7. **Undo/Redo**
   - Track correction history
   - Undo recent corrections
   - Redo functionality

8. **Team Collaboration**
   - User assignments
   - Comment threads
   - Review assignments

## Deployment

### Development

```bash
cd frontend
npm install
npm run dev
# Opens on http://localhost:5173
```

### Production Build

```bash
npm run build
npm run preview
```

### Docker

Build and run via docker-compose:
```bash
docker-compose up
# Frontend on port 3000
# Backend on port 8000
```

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Accessibility

- Semantic HTML
- ARIA labels on buttons
- Focus indicators
- Color not only indicator (icons for confidence)
- Keyboard navigation support

## Code Quality

- ES6+ JavaScript
- Functional components with hooks
- Proper error handling
- Loading states
- Responsive design

## Summary

The frontend provides a complete, user-friendly interface for the human-in-the-loop data labeling workflow. With drag-and-drop upload, real-time progress tracking, and a prioritized review queue, users can efficiently manage and correct AI-generated labels.

All API endpoints are properly integrated, error handling is robust, and the workflow is intuitive and responsive.
