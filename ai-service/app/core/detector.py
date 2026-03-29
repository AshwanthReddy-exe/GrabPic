# ai-service/app/core/detector.py

from insightface.app import FaceAnalysis
from app.config import settings


class FaceDetector:
    """
    Handles face detection using InsightFace.
    """

    def __init__(self):
        self.app = FaceAnalysis(name=settings.MODEL_NAME)
        self.app.prepare(
            ctx_id=0,  # CPU (change later if GPU available)
            det_size=settings.DETECTION_SIZE
        )

    def detect(self, image):
        """
        Detect faces in an image.

        Returns:
            list of face objects
        """
        faces = self.app.get(image)
        return faces
