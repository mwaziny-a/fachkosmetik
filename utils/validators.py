from fastapi import UploadFile, HTTPException
from utils.config import settings


async def validate_image_file(file: UploadFile) -> None:
    if file.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Accepted: JPEG, PNG, WebP.",
        )
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if hasattr(file, "size") and file.size and file.size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file.size/(1024*1024):.1f} MB. Max: {settings.max_upload_size_mb} MB.",
        )