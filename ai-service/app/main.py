from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

import os
import shutil
import uuid
import zipfile
import io
import time
import json
import asyncio
from typing import List
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.detector import FaceDetector
from app.core.embedder import FaceEmbedder
from app.core.indexer import FaceIndexer
from app.core.matcher import FaceMatcher
from app.services.processor import ImageProcessor
from app.services.search_service import SearchService
from app.core.security import verify_token
from app.core.limiter import is_rate_limited
from app.core.blob_service import upload_image_bytes, delete_event_blobs, generate_download_sas


# -------------------------
# Initialize App
# -------------------------
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# -------------------------
# Single Source of Truth (IMPORTANT)
# -------------------------
BASE_DATA_DIR = settings.BASE_DATA_DIR  # should be /app/data

# Create events dir without mounting it publicly
events_dir = os.path.join(BASE_DATA_DIR, "events")
os.makedirs(events_dir, exist_ok=True)


# -------------------------
# Ensure required dirs exist
# -------------------------
os.makedirs(BASE_DATA_DIR, exist_ok=True)
os.makedirs(settings.QUERY_DIR, exist_ok=True)


# -------------------------
# Initialize Core Components
# -------------------------
detector = FaceDetector()
embedder = FaceEmbedder()

# -------------------------
# Background Cleanup Scheduler
# -------------------------
async def cleanup_expired_events():
    while True:
        try:
            events_path = os.path.join(settings.BASE_DATA_DIR, "events")
            if os.path.exists(events_path):
                now = int(time.time())
                for event_id in os.listdir(events_path):
                    event_dir = os.path.join(events_path, event_id)
                    meta_path = os.path.join(event_dir, "meta.json")
                    
                    if os.path.exists(meta_path):
                        with open(meta_path, "r") as f:
                            try:
                                meta = json.load(f)
                                expires_at = meta.get("expiresAt", 0)
                                if expires_at > 0 and now > expires_at:
                                    try:
                                        print(f"[CLEANUP] Event {event_id} expired. Deleting...")
                                        # Delete from Azure Blob first
                                        delete_event_blobs(event_id)
                                        # Then local
                                        shutil.rmtree(event_dir)
                                    except Exception as event_err:
                                        print(f"[CLEANUP] Failed to delete event {event_id}: {event_err}")
                            except json.JSONDecodeError:
                                print(f"[CLEANUP] Failed to parse meta.json for {event_id}")
        except Exception as e:
            print(f"[CLEANUP] Error during cleanup: {e}")
            
        await asyncio.sleep(600) 

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_expired_events())


# -------------------------
# Helpers
# -------------------------

def update_event_status(event_id: str, status: str):
    event_dir = os.path.join(settings.BASE_DATA_DIR, "events", event_id)
    status_path = os.path.join(event_dir, "status.json")
    os.makedirs(event_dir, exist_ok=True)
    with open(status_path, "w") as f:
        json.dump({"status": status}, f)

def background_process_images(event_id: str, images_data: list):
    print(f"[PROCESS START] Event: {event_id}")
    try:
        update_event_status(event_id, "processing")
        
        event_dir = os.path.join(settings.BASE_DATA_DIR, "events", event_id)
        index_dir = os.path.join(event_dir, "index")
        os.makedirs(index_dir, exist_ok=True)

        indexer = FaceIndexer(
            settings.EMBEDDING_DIM,
            index_path=os.path.join(index_dir, "faces.index"),
            meta_path=os.path.join(index_dir, "meta.json")
        )

        processor = ImageProcessor(detector, embedder, indexer)
        processor.process_images(images_data)
        
        update_event_status(event_id, "completed")
        print(f"[PROCESS DONE] Event: {event_id}")
    except Exception as e:
        print(f"[PROCESS FAILED] Event: {event_id}, Error: {e}")
        update_event_status(event_id, "failed")


# -------------------------
# API: Process Images
# -------------------------
@app.post("/process/{event_id}")
async def process_images(event_id: str, background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    event_dir = os.path.join(settings.BASE_DATA_DIR, "events", event_id)
    
    # Ensure required directories exist before writing any file
    os.makedirs(event_dir, exist_ok=True)
    os.makedirs(os.path.join(event_dir, "index"), exist_ok=True)

    # Initialize meta.json if it doesn't exist
    event_meta_path = os.path.join(event_dir, "meta.json")
    if not os.path.exists(event_meta_path):
        now = int(time.time())
        expiry = now + (settings.EVENT_EXPIRY_HOURS * 3600)
        meta_data = {
            "eventId": event_id,
            "createdAt": now,
            "expiresAt": expiry
        }
        with open(event_meta_path, "w") as f:
            json.dump(meta_data, f)

    images_data = []
    for file in files:
        filename = f"{uuid.uuid4()}.jpg"
        content = await file.read()
        
        images_data.append((filename, content))
        
        # Dual-write: Upload to Azure Blob in background
        if settings.USE_BLOB_STORAGE:
            background_tasks.add_task(upload_image_bytes, event_id, filename, content)

    # Trigger background processing
    background_tasks.add_task(background_process_images, event_id, images_data)

    return {
        "status": "processing_started",
        "eventId": event_id
    }

@app.get("/status/{event_id}")
async def get_processing_status(event_id: str):
    event_dir = os.path.join(settings.BASE_DATA_DIR, "events", event_id)
    status_path = os.path.join(event_dir, "status.json")
    
    if not os.path.exists(status_path):
        return {"status": "not_found"}
        
    try:
        with open(status_path, "r") as f:
            return json.load(f)
    except Exception:
        return {"status": "error"}


# -------------------------
# API: Serve Image Securely
# -------------------------
@app.get("/images/{event_id}/images/{filename}")
async def get_image(request: Request, event_id: str, filename: str, token: str = None):
    # Rate limiting: 60 requests per minute per IP
    if is_rate_limited(request.client.host):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
        
    if not verify_token(event_id, filename, token):
        raise HTTPException(status_code=403, detail="Invalid token, signature verification failed or token expired.")
        
    file_path = os.path.join(BASE_DATA_DIR, "events", event_id, "images", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
        
    return FileResponse(file_path)

# -------------------------
# API: Search Images
# -------------------------
@app.post("/search/{event_id}")
async def search_images(event_id: str, files: List[UploadFile] = File(...)):
    import numpy as np
    import cv2

    event_dir = os.path.join(BASE_DATA_DIR, "events", event_id)
    index_dir = os.path.join(event_dir, "index")

    if not os.path.exists(event_dir):
        return {"error": "Invalid event_id"}

    images = []

    for file in files:
        try:
            contents = await file.read()

            np_arr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if image is not None:
                images.append(image)

        except Exception as e:
            print(f"[ERROR] {e}")
            continue

    if not images:
        return {"error": "Invalid images"}

    indexer = FaceIndexer(
        settings.EMBEDDING_DIM,
        index_path=os.path.join(index_dir, "faces.index"),
        meta_path=os.path.join(index_dir, "meta.json")
    )

    matcher = FaceMatcher(indexer)
    search_service = SearchService(detector, embedder, matcher)

    return search_service.search(images)


# -------------------------
# API: Download Event Images
# -------------------------
# -------------------------
# API: Download Event Images
# -------------------------
@app.get("/download/{blob_name:path}")
async def download_image(blob_name: str):
    """
    Generates a secure SAS URL for direct downloading from Azure Blob Storage.
    The Content-Disposition is set to attachment for direct browser download.
    """
    try:
        url = generate_download_sas(blob_name)
        return {"url": url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
