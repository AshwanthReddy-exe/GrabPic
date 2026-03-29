# app/core/indexer.py

import faiss
import numpy as np
import os
import json


class FaceIndexer:
    def __init__(self, dim, index_path="app/data/faces.index", meta_path="app/data/faces_meta.json"):
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path

        os.makedirs("app/data", exist_ok=True)

        # Initialize FAISS index (cosine similarity)
        self.index = faiss.IndexFlatIP(dim)

        # Normalize embeddings for cosine similarity
        self.metadata = []
        self.id_counter = 0

        # Load if exists
        self._load()

    # -------------------------
    # Add embeddings
    # -------------------------
    def add(self, embeddings, image_paths):
        if len(embeddings) == 0:
            return 0

        embeddings = np.array(embeddings).astype("float32")

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)

        self.index.add(embeddings)

        count = 0
        for i in range(len(embeddings)):
            self.metadata.append({
                "id": self.id_counter,
                "image_path": image_paths[i]
            })
            self.id_counter += 1
            count += 1

        return count

    # -------------------------
    # Search
    # -------------------------
    def search(self, query_embedding, top_k=5):
        if self.index.ntotal == 0:
            return []

        query = np.array([query_embedding]).astype("float32")
        faiss.normalize_L2(query)

        scores, indices = self.index.search(query, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue

            results.append({
                "score": float(score),
                "image_path": self.metadata[idx]["image_path"]
            })

        return results

    # -------------------------
    # Save to disk
    # -------------------------
    def save(self):
        faiss.write_index(self.index, self.index_path)

        with open(self.meta_path, "w") as f:
            json.dump({
                "metadata": self.metadata,
                "id_counter": self.id_counter
            }, f)

    # -------------------------
    # Load from disk
    # -------------------------
    def _load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)

        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r") as f:
                data = json.load(f)
                self.metadata = data["metadata"]
                self.id_counter = data["id_counter"]
