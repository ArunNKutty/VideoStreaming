"""
Custom exceptions and exception handlers
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)


class VideoProcessingError(Exception):
    """Custom exception for video processing errors"""
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class FileUploadError(Exception):
    """Custom exception for file upload errors"""
    def __init__(self, message: str, filename: str = None):
        self.message = message
        self.filename = filename
        super().__init__(self.message)


async def video_processing_exception_handler(request: Request, exc: VideoProcessingError):
    """Handle video processing errors"""
    logger.error(f"Video processing error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Video Processing Error",
            "message": exc.message,
            "details": exc.details
        }
    )


async def file_upload_exception_handler(request: Request, exc: FileUploadError):
    """Handle file upload errors"""
    logger.error(f"File upload error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "File Upload Error",
            "message": exc.message,
            "filename": exc.filename
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )


def add_exception_handlers(app: FastAPI):
    """Add all exception handlers to the FastAPI app"""
    app.add_exception_handler(VideoProcessingError, video_processing_exception_handler)
    app.add_exception_handler(FileUploadError, file_upload_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
