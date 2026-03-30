# ai-service/app/services/processor.py

from app.utils.image import preprocess_image_from_bytes


class ImageProcessor:
    """
    Handles bulk image processing pipeline.
    """

    def __init__(self, detector, embedder, indexer):
        self.detector = detector
        self.embedder = embedder
        self.indexer = indexer

        self.no_face_images = []  # store images without faces

    def process_images(self, images_data):
        """
        Process a list of images and populate FAISS index.

        Args:
            images_data: list of tuples (filename, content: bytes)
        """
        total_images = 0
        total_faces = 0
        total_embeddings = 0

        for filename, content in images_data:
            total_images += 1

            try:
                image = preprocess_image_from_bytes(content)

                # Step 1: Detect faces
                faces = self.detector.detect(image)

                if faces is None or len(faces) == 0:
                    self.no_face_images.append(filename)
                    continue

                total_faces += len(faces)

                # Step 2: Extract embeddings
                embeddings = self.embedder.extract(faces)

                if embeddings is None or len(embeddings) == 0:
                    self.no_face_images.append(filename)
                    continue

                total_embeddings += len(embeddings)

                # Step 3: Map each embedding → filename
                filenames_batch = [filename] * len(embeddings)

                # Step 4: Add to FAISS index
                self.indexer.add(embeddings, filenames_batch)

            except Exception as e:
                print(f"[ERROR] Failed processing {filename}: {e}")
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
