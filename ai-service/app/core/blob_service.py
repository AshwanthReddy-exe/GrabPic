import os
import logging
from datetime import datetime, timedelta, timezone
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize BlobServiceClient
blob_service_client = None
if settings.AZURE_STORAGE_CONNECTION_STRING:
    try:
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
    except Exception as e:
        logger.error(f"Failed to initialize BlobServiceClient: {e}")

def upload_image_bytes(event_id: str, filename: str, content: bytes):
    """
    Uploads an image in-memory byte content to Azure Blob Storage.
    Path: events/{event_id}/images/{filename}
    """
    if not settings.USE_BLOB_STORAGE:
        return

    if not blob_service_client:
        logger.error("BlobServiceClient not initialized. Skipping upload.")
        return

    try:
        blob_path = f"events/{event_id}/images/{filename}"
        container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER_NAME)
        
        container_client.upload_blob(name=blob_path, data=content, overwrite=True)
        
        logger.info(f"Blob upload success: {blob_path}")
        print(f"Blob upload success: {blob_path}")
    except Exception as e:
        logger.error(f"Blob upload failed for {filename}: {e}")
        print(f"Blob upload failed: {e}")

def generate_download_sas(blob_name: str) -> str:
    """
    Generates a SAS URL for a given blob with read permission and attachment content disposition.
    """
    if not settings.USE_BLOB_STORAGE:
        raise ValueError("Blob storage is not enabled.")

    if not blob_service_client:
        raise ValueError("BlobServiceClient not initialized.")

    conn_str = settings.AZURE_STORAGE_CONNECTION_STRING
    if not conn_str:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING is not set.")

    # Parse connection string
    conn_dict = dict(x.split("=", 1) for x in conn_str.split(";") if x and "=" in x)
    account_name = conn_dict.get("AccountName")
    account_key = conn_dict.get("AccountKey")

    if not account_name or not account_key:
        raise ValueError("Could not parse AccountName or AccountKey from Connection String.")

    filename = blob_name.split("/")[-1]

    sas_token = generate_blob_sas(
        account_name=account_name,
        account_key=account_key,
        container_name=settings.AZURE_CONTAINER_NAME,
        blob_name=blob_name,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(minutes=10),
        content_disposition=f'attachment; filename="{filename}"'
    )

    return f"https://{account_name}.blob.core.windows.net/{settings.AZURE_CONTAINER_NAME}/{blob_name}?{sas_token}"


def delete_event_blobs(event_id: str):
    """
    Deletes all blobs for a given event from Azure Blob Storage.
    Prefix: events/{event_id}/
    """
    if not settings.USE_BLOB_STORAGE:
        return

    if not blob_service_client:
        logger.error("BlobServiceClient not initialized. Skipping deletion.")
        return

    try:
        print(f"[BLOB CLEANUP] Deleting blobs for event: {event_id}")
        logger.info(f"[BLOB CLEANUP] Deleting blobs for event: {event_id}")
        
        container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER_NAME)
        
        # DEBUG: List all blobs to verify structure (Temporary)
        print("[DEBUG] Listing all blobs in container...")
        all_blobs = container_client.list_blobs()
        
        for blob in all_blobs:
            # print(f"[DEBUG BLOB] {blob.name}") # Uncomment if needed for deeper debugging
            
            # Dynamic matching: event_id at start or as a directory segment
            if blob.name.startswith(event_id) or f"/{event_id}/" in blob.name:
                print(f"[BLOB DELETE] {blob.name}")
                container_client.delete_blob(blob.name)
        
        print(f"[BLOB CLEANUP DONE] {event_id}")
        logger.info(f"[BLOB CLEANUP DONE] {event_id}")
    except Exception as e:
        logger.error(f"Blob cleanup failed for event {event_id}: {e}")
        print(f"Blob cleanup failed: {e}")
