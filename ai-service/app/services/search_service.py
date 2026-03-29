# ai-service/app/services/search_service.py

from app.config import settings


class SearchService:
    def __init__(self, detector, embedder, matcher):
        self.detector = detector
        self.embedder = embedder
        self.matcher = matcher

    def search(self, images):
        if not images:
            return {"error": "No images provided"}

        query_embeddings = []

        # -------------------------
        # Extract embeddings
        # -------------------------
        for image in images:
            try:
                faces = self.detector.detect(image)

                if not faces:
                    continue

                embeddings = self.embedder.extract(faces)

                if embeddings is not None and len(embeddings) > 0:
                    query_embeddings.append(embeddings[0])

            except Exception as e:
                print(f"[ERROR] {e}")
                continue

        if not query_embeddings:
            return {"error": "No faces detected"}

        # -------------------------
        # 🔥 MULTI-SELFIE FUSION
        # -------------------------
        fused_results = {}

        for emb in query_embeddings:
            results = self.matcher.indexer.search(emb, settings.TOP_K)

            for r in results:
                path = r["image_path"]
                score = r["score"]

                if path not in fused_results or score > fused_results[path]:
                    fused_results[path] = score

        # -------------------------
        # Sort
        # -------------------------
        sorted_results = sorted(
            fused_results.items(),
            key=lambda x: x[1],
            reverse=True
        )

        import os

        formatted = [
            {
                "image_id": os.path.basename(path),  # extract filename
                "score": float(score)
            }
            for path, score in sorted_results
        ]

        # -------------------------
        # Threshold filtering
        # -------------------------
        strong = [
            r for r in formatted
            if r["score"] >= settings.STRONG_THRESHOLD
        ]

        weak = [
            r
            for r in formatted
            if settings.WEAK_THRESHOLD <= r["score"] < settings.STRONG_THRESHOLD
        ]

        return {
            "total_results": len(formatted),
            "strong_matches": strong,
            "weak_matches": weak
        }
