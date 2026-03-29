# ai-service/app/core/matcher.py

from app.config import settings


class FaceMatcher:
    """
    Handles matching logic using FAISS results.
    """

    def __init__(self, indexer):
        self.indexer = indexer

    def match(self, query_embeddings):
        if query_embeddings is None or len(query_embeddings) == 0:
            return []

        results = {}

        for emb in query_embeddings:
            matches = self.indexer.search(emb, settings.TOP_K)

            for match in matches:
                score = match["score"]
                image_path = match["image_path"]

                # Keep best score per image
                if image_path not in results or score > results[image_path]:
                    results[image_path] = score

        # Sort by similarity (higher = better)
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                "image_path": img,
                "score": float(score)
            }
            for img, score in sorted_results
        ]
