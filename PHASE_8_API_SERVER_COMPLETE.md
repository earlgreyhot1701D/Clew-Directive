# Phase 8: API Layer - Local Development Server

**Status**: ✅ COMPLETE  
**Date**: February 14, 2026  
**Task**: Create FastAPI server wrapping Lambda handlers for local development

---

## What Was Built

### FastAPI Development Server

**File**: `backend/main.py`

**Purpose**: Wraps AWS Lambda handlers in a FastAPI server for local development. In production, these handlers run as Lambda functions behind API Gateway.

**Endpoints**:
1. `GET /` - Health check
2. `GET /health` - Health check
3. `POST /vibe-check` - Process Vibe Check responses, return profile
4. `POST /refine-profile` - Refine profile based on user correction
5. `POST /generate-briefing` - Generate learning path and PDF

**Features**:
- ✅ CORS enabled for localhost:3000
- ✅ Request/response validation with Pydantic
- ✅ Automatic API documentation at `/docs`
- ✅ Hot reload during development
- ✅ Proper error handling and HTTP status codes
- ✅ Logging for all requests

---

## Server Status

**Running**: ✅ http://localhost:8000  
**API Docs**: http://localhost:8000/docs  
**Frontend**: http://localhost:3000 (Next.js)

**Note**: WeasyPrint warning present (PDF generation requires additional system libraries on Windows). PDFs won't generate yet, but API endpoints work.

---

## API Endpoints

### 1. POST /vibe-check

**Request**:
```json
{
  "vibe_check_responses": {
    "skepticism": "Curious but haven't started learning",
    "goal": "Understand what AI actually is and isn't",
    "learning_style": "Reading and thinking at my own pace",
    "context": "Business / Marketing / Operations"
  }
}
```

**Response**:
```json
{
  "profile": "You're approaching AI with curiosity but healthy skepticism..."
}
```

### 2. POST /refine-profile

**Request**:
```json
{
  "original_profile": "You're approaching AI...",
  "user_correction": "Actually I'm more hands-on..."
}
```

**Response**:
```json
{
  "profile": "You're approaching AI with hands-on curiosity..."
}
```

### 3. POST /generate-briefing

**Request**:
```json
{
  "approved_profile": "You're approaching AI with curiosity..."
}
```

**Response**:
```json
{
  "learning_path": [
    {
      "id": 1,
      "category": "FOUNDATIONS",
      "title": "Elements of AI",
      "provider": "University of Helsinki",
      "hours": 30,
      "difficulty": "Beginner",
      "format": "Self-paced course",
      "reasoning": "This free course...",
      "url": "https://course.elementsofai.com/"
    }
  ],
  "total_hours": 53,
  "next_steps": "Start with Resource 1...",
  "pdf_url": "https://s3.../briefing.pdf" or null
}
```

---

## Dependencies Added

**File**: `backend/requirements.txt`

```
# API server (local development)
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.10.0
```

**Installed**: ✅

---

## Next Steps

### Phase 8B: Frontend API Integration

Now that the backend API is running, we need to update the frontend to call the real API instead of using mock data.

**Tasks**:
1. Create API client in frontend
2. Replace mock profile generation with real API call
3. Replace mock briefing generation with real API call
4. Handle loading states
5. Handle error states
6. Test end-to-end flow

**Files to Update**:
- `frontend/src/app/page.tsx` - Replace mock handlers with API calls

---

## Testing the API

### Using curl:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test vibe-check
curl -X POST http://localhost:8000/vibe-check \
  -H "Content-Type: application/json" \
  -d '{
    "vibe_check_responses": {
      "skepticism": "Curious but haven't started learning",
      "goal": "Understand what AI actually is and isn't",
      "learning_style": "Reading and thinking at my own pace",
      "context": "Business / Marketing / Operations"
    }
  }'
```

### Using API Docs:

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI)

---

## Known Issues

### WeasyPrint Warning

**Issue**: PDF generation requires system libraries not installed on Windows

**Warning**:
```
WeasyPrint could not import some external libraries
cannot load library 'libgobject-2.0-0'
```

**Impact**: 
- API endpoints work fine
- Profile generation works
- Learning path generation works
- PDF generation will fail (returns null)

**Solution** (for later):
- Install GTK+ libraries on Windows
- Or use Docker (Linux container has libraries)
- Or deploy to AWS Lambda (has libraries)

**For now**: Frontend can display learning path without PDF

---

## Architecture

```
Frontend (Next.js)          Backend (FastAPI)           Agents
http://localhost:3000  →  http://localhost:8000  →  Orchestrator
                                                    ├─ Navigator (Bedrock)
                                                    ├─ Scout
                                                    └─ PDF Generator
```

**Flow**:
1. User completes Vibe Check in frontend
2. Frontend POST to `/vibe-check`
3. FastAPI calls Lambda handler
4. Lambda handler calls Orchestrator
5. Orchestrator calls Navigator agent
6. Navigator calls Bedrock (Claude Sonnet)
7. Profile returned to frontend

---

## Dev Server Commands

### Start Backend API:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### Start Frontend:
```bash
cd frontend
npm run dev
```

### Run Tests:
```bash
python -m pytest backend/tests/test_lambda_handlers.py -v
```

---

**Task Owner**: Backend + API Team  
**Reviewer**: Full Stack Lead  
**Status**: Ready for frontend integration (Phase 8B)
