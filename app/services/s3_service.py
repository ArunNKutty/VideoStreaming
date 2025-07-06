"""
AWS S3 service for video storage and streaming
"""
import boto3
import logging
from typing import Optional, Dict
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for handling S3 operations"""

    def __init__(self):
        """Initialize S3 service (lazy initialization)"""
        self.s3_client = None
        self.bucket_name = settings.S3_BUCKET_NAME
        self._initialized = False

    def _initialize_client(self):
        """Initialize S3 client on first use"""
        if self._initialized:
            return

        try:
            # Check if credentials are provided
            if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
                logger.warning("AWS credentials not provided. S3 functionality will be disabled.")
                return

            # Configure boto3 client
            config = Config(
                region_name=settings.AWS_REGION,
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                max_pool_connections=50
            )

            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
                endpoint_url=settings.S3_ENDPOINT_URL,
                config=config
            )

            # Try to ensure bucket exists, but don't fail if we can't
            self._ensure_bucket_exists_safe()
            self._initialized = True
            logger.info("S3 client initialized successfully")

        except NoCredentialsError:
            logger.error("AWS credentials not found")
            self.s3_client = None
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            self.s3_client = None
    
    def _ensure_bucket_exists_safe(self):
        """Safely try to ensure bucket exists, don't fail if we can't"""
        if not self.s3_client:
            return

        try:
            # Try to check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, try to create it
                try:
                    if settings.AWS_REGION == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
                        )
                    logger.info(f"Created S3 bucket '{self.bucket_name}'")
                except ClientError as create_error:
                    logger.warning(f"Could not create bucket: {create_error}. Will try to upload anyway.")
            elif error_code == '403':
                logger.warning(f"Access denied checking bucket '{self.bucket_name}'. Will try to upload anyway.")
            else:
                logger.warning(f"Error checking bucket: {e}. Will try to upload anyway.")
    
    async def upload_file(self, file_content: bytes, key: str, content_type: str = None) -> str:
        """Upload file to S3"""
        self._initialize_client()

        if not self.s3_client:
            raise Exception("S3 client not available. Check AWS credentials.")

        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type

            # Upload file
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                **extra_args
            )

            # Return S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            logger.info(f"Uploaded file to S3: {s3_url}")
            return s3_url

        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise
    
    async def upload_hls_files(self, video_id: str, local_hls_dir: str) -> Dict[str, str]:
        """Upload all HLS files (playlist and segments) to S3"""
        self._initialize_client()

        # Try S3 upload if available
        if not self.s3_client:
            logger.warning("S3 client not available. Files remain in local directory only.")
            return {}

        try:
            uploaded_files = {}
            hls_path = Path(local_hls_dir)

            if not hls_path.exists():
                raise FileNotFoundError(f"HLS directory not found: {local_hls_dir}")

            # Upload all files in the HLS directory to S3
            for file_path in hls_path.iterdir():
                if file_path.is_file():
                    # Determine content type
                    content_type = self._get_content_type(file_path.suffix)

                    # S3 key for the file
                    s3_key = f"videos/{video_id}/hls/{file_path.name}"

                    # Read and upload file
                    with open(file_path, 'rb') as f:
                        file_content = f.read()

                    s3_url = await self.upload_file(file_content, s3_key, content_type)
                    uploaded_files[file_path.name] = s3_url

            logger.info(f"Uploaded {len(uploaded_files)} HLS files for video {video_id} to S3")
            return uploaded_files

        except Exception as e:
            logger.error(f"Failed to upload HLS files to S3: {e}. Files remain in local directory.")
            return {}



    def _get_content_type(self, file_extension: str) -> str:
        """Get content type based on file extension"""
        content_types = {
            '.m3u8': 'application/vnd.apple.mpegurl',
            '.ts': 'video/MP2T',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.mov': 'video/quicktime'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')
    
    def get_hls_url(self, video_id: str) -> str:
        """Get HLS playlist URL from S3 (public URL)"""
        s3_key = f"videos/{video_id}/hls/index.m3u8"
        return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    
    def get_file_url(self, video_id: str, filename: str) -> str:
        """Get file URL from S3 (public URL)"""
        s3_key = f"videos/{video_id}/hls/{filename}"
        return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    
    async def delete_video_files(self, video_id: str) -> bool:
        """Delete all files for a video from S3"""
        try:
            # List all objects with the video prefix
            prefix = f"videos/{video_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                logger.info(f"No files found for video {video_id}")
                return True
            
            # Delete all objects
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            
            self.s3_client.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': objects_to_delete}
            )
            
            logger.info(f"Deleted {len(objects_to_delete)} files for video {video_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete video files: {e}")
            return False
    
    def check_file_exists(self, video_id: str, filename: str) -> bool:
        """Check if a file exists in S3 or persistent directories"""
        # Check S3 first
        self._initialize_client()
        if self.s3_client:
            try:
                s3_key = f"videos/{video_id}/hls/{filename}"
                self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                return True
            except ClientError:
                pass

        # No local storage - return False if S3 check fails
        return False

    def get_local_file_path(self, video_id: str, filename: str) -> Optional[Path]:
        """Local storage disabled - always returns None"""
        # Parameters kept for API compatibility but not used
        return None


# Global service instance
s3_service = S3Service()
