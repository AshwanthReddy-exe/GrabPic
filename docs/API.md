# GrabPic API

## Overview

Base URLs:
- Backend: `http://localhost:8080`
- AI service: `http://localhost:8000`

## Backend API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/events` | Create event |
| POST | `/events/{eventId}/upload` | Upload event photos |
| POST | `/events/{eventId}/search` | Search photos |
| GET | `/events/{eventId}/download` | Download all photos as ZIP |

### POST `/events`

Create a new event.

```bash
curl -X POST http://localhost:8080/events
```

Response:
```json
{ "eventId": "550e8400-e29b-41d4-a716-446655440000" }
```

### POST `/events/{eventId}/upload`

Upload event photos for processing.

```bash
curl -X POST http://localhost:8080/events/{eventId}/upload \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg"
```

Response:
```json
"processing_started"
```

Notes:
- Processing is asynchronous.
- Photos are dual-written to Azure Blob Storage when enabled.

### POST `/events/{eventId}/search`

Search photos using selfie uploads.

Query params:
- `page` (default `1`)
- `size` (default `20`)

```bash
curl -X POST "http://localhost:8080/events/{eventId}/search?page=1&size=20" \
  -F "files=@selfie1.jpg" \
  -F "files=@selfie2.jpg"
```

Response:
```json
{
  "total": 45,
  "page": 1,
  "size": 20,
  "hasMore": true,
  "strongMatches": [{ "imageId": "abc123.jpg", "score": 0.82, "url": "https://..." }],
  "weakMatches": [{ "imageId": "def456.jpg", "score": 0.58, "url": "https://..." }]
}
```

Match rules:
- Strong: `>= 0.65`
- Weak: `0.5-0.65`

### GET `/events/{eventId}/download`

Download all matched photos as a ZIP.

```bash
curl -O http://localhost:8080/events/{eventId}/download
```

Returns: binary ZIP (`photos.zip`).

## AI Service API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/process/{event_id}` | Process and index images |
| GET | `/status/{event_id}` | Check processing status |
| POST | `/search/{event_id}` | Search indexed images |
| GET | `/images/{event_id}/images/{filename}` | Fetch image securely |
| GET | `/download/{blob_name}` | Generate SAS download URL |

### POST `/process/{event_id}`

```bash
curl -X POST http://localhost:8000/process/{event_id} \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg"
```

Response:
```json
{ "status": "processing_started", "eventId": "550e8400-e29b-41d4-a716-446655440000" }
```

Pipeline:
1. Detect faces
2. Extract 512-d embeddings
3. Build FAISS index
4. Store metadata

### GET `/status/{event_id}`

```bash
curl http://localhost:8000/status/{event_id}
```

Response:
```json
{ "status": "completed" }
```

Status values: `not_found`, `processing`, `completed`, `failed`.

### POST `/search/{event_id}`

```bash
curl -X POST http://localhost:8000/search/{event_id} \
  -F "files=@selfie1.jpg" \
  -F "files=@selfie2.jpg"
```

Response:
```json
{
  "strong_matches": [{ "image_id": "abc123.jpg", "score": 0.82 }],
  "weak_matches": [{ "image_id": "def456.jpg", "score": 0.58 }]
}
```

Notes:
- Each selfie is searched independently.
- Results are deduplicated and aggregated.

### GET `/images/{event_id}/images/{filename}`

Secure image fetch using `token` query param.

```bash
curl "http://localhost:8000/images/{event_id}/images/photo.jpg?token=xyz123"
```

Returns image bytes or redirects to Azure Blob SAS.

Limit: 60 requests/min/IP.

### GET `/download/{blob_name}`

Generate a SAS URL for a blob.

```bash
curl http://localhost:8000/download/events/{event_id}/images/photo.jpg
```

Response:
```json
{ "url": "https://storageaccount.blob.core.windows.net/events/...?sv=..." }
```

## Errors

Backend:
```json
{ "error": "Invalid request" }
{ "error": "Event not found" }
{ "error": "Internal server error" }
```

AI service:
```json
{ "error": "Invalid images" }
{ "detail": "Invalid token, signature verification failed or token expired." }
{ "detail": "Image not found" }
{ "detail": "Too many requests. Please try again later." }
```

## Data models

### ImageMatch

```json
{ "imageId": "string", "score": "number (0.0-1.0)", "url": "string" }
```

### SearchResponse

```json
{
  "total": "integer",
  "page": "integer",
  "size": "integer",
  "hasMore": "boolean",
  "strongMatches": "ImageMatch[]",
  "weakMatches": "ImageMatch[]"
}
```

## Other notes

- Image tokens are base64-encoded HMAC signatures.
- Token expiry: 3 hours.
- CORS allows `http://localhost:5173`.
- No WebSocket API yet; poll `/status/{event_id}`.
- Use standard HTTP clients; no official SDKs.
