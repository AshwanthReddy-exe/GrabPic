# GrabPic Architecture

## Overview

GrabPic has three services:
- **Frontend**: React + Vite
- **Backend**: Spring Boot 3 / Java 21
- **AI service**: FastAPI / Python 3.11

Frontend ↔ backend and backend ↔ AI service communicate over HTTP. Images are served through signed URLs/tokens, not direct backend file serving.

## System map

```text
User → Frontend → Backend → AI service
                    │          │
                    │          ├─ FAISS indexes (local disk)
                    │          └─ Face detection / embedding / matching
                    └─ Azure Blob Storage (original images)
```

## Service responsibilities

### Frontend
- Event creation
- Photo upload
- Selfie search
- Results display and pagination
- Image modal/navigation

Key parts: `Home.jsx`, `CreateEvent.jsx`, `EventPage.jsx`, `client.js`

### Backend
- Event lifecycle
- Upload validation
- AI service orchestration
- Azure Blob integration
- Pagination and response shaping
- Signed URL generation

Key parts: `EventController`, `EventService`, `AiService`, `TokenService`

### AI service
- Face detection
- Embedding extraction
- FAISS indexing/search
- Multi-selfie aggregation
- Secure image serving

Key parts: `FaceDetector`, `FaceEmbedder`, `FaceIndexer`, `FaceMatcher`, `SearchService`

## Data flow

### Event creation
1. Frontend sends `POST /events`.
2. Backend creates the event ID.
3. Organizer uploads photos.
4. Backend forwards photos to the AI service.
5. AI service processes in the background and stores the index.

### Search
1. Frontend sends selfie uploads to backend.
2. Backend forwards to AI service.
3. AI service loads the FAISS index, matches faces, and returns hits.
4. Backend builds `ImageMatch` data, adds signed URLs, and paginates.
5. Frontend groups results into strong/weak matches.

### Image access
- **Azure Blob path**: SAS URL, ~10 min expiry.
- **AI service path**: `/images/{event_id}/images/{filename}`, token-verified, ~3 hour expiry.

## Storage

### AI service local disk

```text
/app/data/
└── events/{event_id}/
    ├── meta.json
    ├── status.json
    ├── index/
    │   ├── faces.index
    │   └── meta.json
    └── images/{uuid}.jpg
```

- `meta.json`: event and expiry metadata
- `status.json`: processing state
- `faces.index`: FAISS index
- index `meta.json`: image/embedding mapping

### Azure Blob Storage
```text
events/{event_id}/images/{uuid}.jpg
```

- Upload: AI service during processing
- Download: backend-generated SAS URLs
- Delete: expiry cleanup

## Face recognition pipeline

1. **Detection**: InsightFace Buffalo_L / RetinaFace, resized to 640×640.
2. **Embedding**: ArcFace, 512-dim, L2 normalized.
3. **Indexing**: FAISS flat index with cosine similarity.
4. **Matching**:
   - Strong: `score >= 0.65`
   - Weak: `0.5 <= score < 0.65`
   - No match: `< 0.5`

Multi-selfie fusion searches each selfie independently, then deduplicates and ranks combined results.

## Security

- Signed URLs use HMAC-based tokens.
- Tokens include event ID, image filename, and expiry.
- Token expiry: 3 hours.
- Image access rate limit: 60 req/min/IP.
- Events auto-delete after 10 hours.

Cleanup runs every 10 minutes and removes blob objects, local files, and FAISS indexes for expired events.

## Scalability

Current limits:
- AI service is stateful
- FAISS indexes live on local disk
- Backend has no cache layer

Path to scale:
1. Externalize FAISS state.
2. Move background work to a queue/worker model.
3. Move event metadata to PostgreSQL.
4. Add CDN-backed image delivery.

## Monitoring

| Metric | Alert |
|---|---|
| Image processing time | > 30s/image |
| Search latency | > 2s |
| 429 hits | > 10/min |
| Disk usage | > 80% |
| Cleanup errors | > 0 |

Log key events: event creation, processing start/finish/fail, search requests, token failures, rate limit hits.

## Why these choices

- **FAISS**: fast similarity search, low memory use, cosine support.
- **InsightFace**: pre-trained, accurate, ONNX-friendly.
- **Azure Blob**: cheap storage, SAS support, CDN-ready.
- **Spring Boot**: mature, type-safe, strong Azure support.

## Future work

- Kubernetes + Helm
- Event-driven processing
- Redis/CDN caching
- Prometheus, Grafana, Jaeger, ELK
