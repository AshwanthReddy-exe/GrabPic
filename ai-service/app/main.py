from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

import os
import shutil
import uuid
import zipfile
import io
from typing import List

from app.config import settings
from app.core.detector import FaceDetector
from app.core.embedder import FaceEmbedder
from app.core.indexer import FaceIndexer
from app.core.matcher import FaceMatcher
from app.services.processor import ImageProcessor
from app.services.search_service import SearchService


# -------------------------
# Initialize App
# -------------------------
app = FastAPI()


# -------------------------
# Single Source of Truth (IMPORTANT)
# -------------------------
BASE_DATA_DIR = settings.BASE_DATA_DIR  # should be /app/data

# Serve ALL event data
app.mount("/images", StaticFiles(directory=BASE_DATA_DIR), name="images")


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
# Helper: Save Upload
# -------------------------
def save_upload_file(upload_file: UploadFile, destination: str):
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)


# -------------------------
# API: Process Images
# -------------------------
@app.post("/process/{event_id}")
async def process_images(event_id: str, files: List[UploadFile] = File(...)):
    event_dir = os.path.join(BASE_DATA_DIR, event_id)
    image_dir = os.path.join(event_dir, "images")

    os.makedirs(image_dir, exist_ok=True)

    image_paths = []

    for file in files:
        filename = f"{uuid.uuid4()}.jpg"
        path = os.path.join(image_dir, filename)

        save_upload_file(file, path)
        image_paths.append(path)

    indexer = FaceIndexer(
        settings.EMBEDDING_DIM,
        index_path=os.path.join(event_dir, "faces.index"),
        meta_path=os.path.join(event_dir, "meta.json")
    )

    processor = ImageProcessor(detector, embedder, indexer)
    result = processor.process_images(image_paths)

    return {
        "event_id": event_id,
        **result
    }


# -------------------------
# API: Search Images
# -------------------------
@app.post("/search/{event_id}")
async def search_images(event_id: str, files: List[UploadFile] = File(...)):
    import numpy as np
    import cv2

    event_dir = os.path.join(BASE_DATA_DIR, event_id)

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
        index_path=os.path.join(event_dir, "faces.index"),
        meta_path=os.path.join(event_dir, "meta.json")
    )

    matcher = FaceMatcher(indexer)
    search_service = SearchService(detector, embedder, matcher)

    return search_service.search(images)


# -------------------------
# API: Download Event Images
# -------------------------
@app.get("/events/{event_id}/download")
async def download_event_images(event_id: str):
    event_dir = os.path.join(BASE_DATA_DIR, event_id, "images")

    if not os.path.exists(event_dir):
        return {"error": "Invalid event_id"}

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name in os.listdir(event_dir):
            file_path = os.path.join(event_dir, file_name)
            zip_file.write(file_path, arcname=file_name)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={event_id}.zip"
        }
    )
