# ai-service/app/services/processor.py

from app.utils.image import preprocess_image


class ImageProcessor:
    """
    Handles bulk image processing pipeline.
    """

    def __init__(self, detector, embedder, indexer):
        self.detector = detector
        self.embedder = embedder
        self.indexer = indexer

        self.no_face_images = []  # store images without faces

    def process_images(self, image_paths):
        """
        Process a list of images and populate FAISS index.

        Args:
            image_paths: list of image file paths
        """
        total_images = 0
        total_faces = 0
        total_embeddings = 0

        for path in image_paths:
            total_images += 1

            try:
                image = preprocess_image(path)

                # Step 1: Detect faces
                faces = self.detector.detect(image)

                if faces is None or len(faces) == 0:
                    self.no_face_images.append(path)
                    continue

                total_faces += len(faces)

                # Step 2: Extract embeddings
                embeddings = self.embedder.extract(faces)

                if embeddings is None or len(embeddings) == 0:
                    self.no_face_images.append(path)
                    continue

                total_embeddings += len(embeddings)

                # Step 3: Map each embedding → image_path
                image_paths_batch = [path] * len(embeddings)

                # Step 4: Add to FAISS index
                self.indexer.add(embeddings, image_paths_batch)

            except Exception as e:
                print(f"[ERROR] Failed processing {path}: {e}")
                continue

        # Step 5: Persist index + metadata
        self.indexer.save()

        return {
            "images_processed": total_images,
            "faces_detected": total_faces,
            "embeddings_created": total_embeddings,
            "no_face_images": len(self.no_face_images)
        }

    def get_no_face_images(self):
        """
        Return images with no detected faces.
        """
        return self.no_face_images
