import os

# ai-service/app/config.py

class Settings:
    """
    Central configuration for AI service.
    Modify values here instead of hardcoding in logic.
    """

    # -------------------------
    # MODEL CONFIG
    # -------------------------
    MODEL_NAME = "buffalo_l"
    DETECTION_SIZE = (640, 640)

    # -------------------------
    # EMBEDDING CONFIG
    # -------------------------
    EMBEDDING_DIM = 512

    # -------------------------
    # SEARCH CONFIG
    # -------------------------
    TOP_K = 20   # number of nearest neighbors to fetch

    # -------------------------
    # MATCHING THRESHOLDS
    # (tune based on real data)
    # -------------------------
    STRONG_THRESHOLD = 0.65
    WEAK_THRESHOLD = 0.5

    # -------------------------
    # USER INPUT LIMITS
    # -------------------------
    MAX_SELFIES = 4
    MIN_SELFIES = 1

    # -------------------------
    # IMAGE PROCESSING
    # -------------------------
    MAX_IMAGE_WIDTH = 800

    # -------------------------
    # STORAGE PATHS
    # -------------------------
    # STORAGE PATHS
    BASE_DATA_DIR = os.getenv("BASE_DATA_DIR", "/app/data")
    QUERY_DIR = os.getenv("QUERY_DIR", "/app/query_data")

    # -------------------------
    # SECURITY & EXPIRY
    # -------------------------
    IMAGE_TOKEN_SECRET = os.getenv("IMAGE_TOKEN_SECRET", "defaultSecretKeyForTokensIfEnvMissing")
    EVENT_EXPIRY_HOURS = int(os.getenv("EVENT_EXPIRY_HOURS", "3"))


# Singleton instance (use everywhere)
settings = Settings()
