# GrabPic - Face Recognition Photo Sharing

A production-ready face recognition-based photo sharing application that allows event organizers to upload event photos and attendees to find their photos by uploading selfies.

## Overview

GrabPic uses AI-powered face matching to identify people in event photos. Event organizers upload photos from their events, and attendees can find all photos containing themselves by uploading 2-4 selfies.

## Architecture

GrabPic follows a three-tier microservices architecture:

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   FRONTEND      │─────>│     BACKEND      │─────>│    AI SERVICE   │
│   React + Vite  │      │   Spring Boot    │      │  Python/FastAPI │
└─────────────────┘      └──────────────────┘      └─────────────────┘
         │                          │                          │
         └──────────────────────────┴──────────────────────────┘
                                    │
                           ┌────────┴────────┐
                           │   Azure Blob    │
                           │    Storage      │
                           └─────────────────┘
```

### Services

| Service | Technology | Purpose |
|---------|------------|---------|
| **Frontend** | React 19, Vite | User interface for event creation, photo upload, and selfie search |
| **Backend** | Spring Boot 3 (Java 21) | REST API, business logic, Azure Blob integration |
| **AI Service** | Python 3.11, FastAPI | Face detection (InsightFace), embeddings (FAISS), similarity search |

## Features

### Event Organizer
- Create events with auto-generated UUID
- Upload event photos (batch upload supported)
- Photos are automatically processed for face recognition
- Download all matched photos as a ZIP file

### Event Attendee
- Search for photos using 2-4 selfies for better accuracy
- Tiered results: "Your Photos" (strong matches) and "Maybe You" (weak matches)
- Infinite scroll for browsing results
- Click images to view full size with navigation

### Technical Features
- **Multi-selfie fusion**: Upload multiple selfies to improve match accuracy
- **Secure image access**: Token-based signed URLs with expiration
- **Rate limiting**: 60 requests per minute per IP for image access
- **Auto-expiry**: Events automatically delete after 10 hours
- **Azure Blob Storage**: Images stored securely with SAS token access
- **Background cleanup**: Automatic deletion of expired events

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Azure Storage Account (optional, for production)
- 4GB+ RAM available for AI service

### Running with Docker Compose

1. Clone the repository:
```bash
git clone <repository-url>
cd grabpic
```

2. Create a `.env` file:
```bash
AZURE_STORAGE_CONNECTION_STRING=your_connection_string_here
AZURE_CONTAINER_NAME=events
USE_BLOB_STORAGE=true
IMAGE_TOKEN_SECRET=your-secret-key-change-in-production
EVENT_EXPIRY_HOURS=10
AI_PUBLIC_BASE_URL=http://localhost:8000
```

3. Start all services:
```bash
docker-compose up --build
```

4. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8080
- AI Service: http://localhost:8000

## API Documentation

See [API.md](docs/API.md) for complete API documentation.

## Project Structure

```
.
├── grabpic-frontend/          # React frontend
│   ├── src/
│   │   ├── pages/            # Page components (Home, CreateEvent, EventPage)
│   │   ├── api/              # API client
│   │   └── ...
│   └── Dockerfile
├── backend/                   # Spring Boot backend
│   ├── src/main/java/
│   │   └── com/grabpic/backend/
│   │       ├── controller/   # REST controllers
│   │       ├── service/      # Business logic
│   │       └── dto/          # Data transfer objects
│   └── Dockerfile
├── ai-service/               # Python AI service
│   ├── app/
│   │   ├── core/            # Face detection, embedding, indexing
│   │   ├── services/        # Search and processing services
│   │   └── main.py          # FastAPI application
│   └── Dockerfile
├── docker-compose.yml        # Docker orchestration
└── docs/                     # Documentation
```

## Technology Stack

### Frontend
- React 19.2.4 with React Router DOM
- Vite 8.0.1 (build tool)
- Axios (HTTP client)
- Framer Motion (animations)
- Radix UI (dialogs)

### Backend
- Spring Boot 3.3.5
- Java 21
- Azure Storage Blob SDK 12.28.1
- Lombok (code generation)

### AI Service
- FastAPI (Python web framework)
- InsightFace (face detection and recognition)
- FAISS (Facebook AI Similarity Search)
- OpenCV (image processing)
- ONNX Runtime (model inference)

### Infrastructure
- Docker & Docker Compose
- Azure Blob Storage (optional)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob Storage connection | (none) |
| `AZURE_CONTAINER_NAME` | Blob container name | `events` |
| `USE_BLOB_STORAGE` | Enable Azure Blob Storage | `true` |
| `IMAGE_TOKEN_SECRET` | Secret for signing image URLs | (required) |
| `EVENT_EXPIRY_HOURS` | Event auto-deletion time | `10` |
| `AI_PUBLIC_BASE_URL` | Public URL for AI service | (required) |

## Development

### Running Locally (without Docker)

#### Frontend
```bash
cd grabpic-frontend
npm install
npm run dev
```

#### Backend
```bash
cd backend
./gradlew bootRun
```

#### AI Service
```bash
cd ai-service
pip install -r requirements.txt
python -m app.main
```

## Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment instructions.

## Architecture Details

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Security Considerations

- Face data (embeddings) are stored temporarily and deleted with events
- Images are served via time-limited signed URLs
- Rate limiting prevents abuse
- Events auto-expire to limit data retention
