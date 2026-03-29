# ai-service/app/core/embedder.py

import numpy as np


class FaceEmbedder:
    """
    Handles extraction of face embeddings.
    """

    def extract(self, faces):
        """
        Convert detected faces into embedding vectors.

        Args:
            faces: list of face objects from InsightFace

        Returns:
            numpy array of shape (n_faces, embedding_dim)
            OR None if no faces
        """
        if not faces:
            return None

        embeddings = [face.embedding for face in faces]

        return np.array(embeddings)
