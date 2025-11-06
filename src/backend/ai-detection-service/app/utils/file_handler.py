"""
File handling utilities for A.V.A.R. AI Detection Service
"""

from fastapi import UploadFile
from pathlib import Path
import aiofiles
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file uploads, storage, and cleanup"""

    # Supported RAW file extensions
    RAW_EXTENSIONS = {
        '.cr2', '.cr3',  # Canon
        '.nef', '.nrw',  # Nikon
        '.arw', '.srf', '.sr2',  # Sony
        '.orf',  # Olympus
        '.rw2',  # Panasonic
        '.dng',  # Adobe Digital Negative (universal)
        '.raf',  # Fujifilm
        '.pef',  # Pentax
        '.raw',  # Generic
        '.rwl',  # Leica
        '.3fr',  # Hasselblad
        '.mrw',  # Minolta
        '.dcr',  # Kodak
        '.erf',  # Epson
    }

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True, parents=True)

    def is_valid_raw_extension(self, filename: str) -> bool:
        """Check if file has a valid RAW extension"""
        ext = Path(filename).suffix.lower()
        return ext in self.RAW_EXTENSIONS

    async def save_upload(
        self,
        upload_file: UploadFile,
        submission_id: str,
        file_type: str
    ) -> str:
        """
        Save uploaded file to disk

        Args:
            upload_file: FastAPI UploadFile object
            submission_id: Unique submission identifier
            file_type: Type identifier (e.g., "jpg", "raw")

        Returns:
            Path to saved file
        """
        try:
            # Create submission directory
            submission_dir = self.upload_dir / submission_id
            submission_dir.mkdir(exist_ok=True, parents=True)

            # Generate file path
            ext = Path(upload_file.filename).suffix
            file_path = submission_dir / f"{file_type}{ext}"

            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await upload_file.read()
                await f.write(content)

            logger.info(f"Saved {file_type} file: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to save upload: {str(e)}")
            raise

    async def cleanup_files(self, *file_paths: Optional[str]):
        """
        Delete temporary files after processing

        Args:
            *file_paths: Variable number of file paths to delete
        """
        for file_path in file_paths:
            if file_path is None:
                continue

            try:
                path = Path(file_path)

                # Delete file
                if path.exists() and path.is_file():
                    path.unlink()
                    logger.debug(f"Deleted file: {file_path}")

                # Delete parent directory if empty
                parent_dir = path.parent
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                    logger.debug(f"Deleted empty directory: {parent_dir}")

            except Exception as e:
                logger.warning(f"Failed to cleanup file {file_path}: {str(e)}")

    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        return Path(file_path).stat().st_size

    def get_file_extension(self, file_path: str) -> str:
        """Get file extension"""
        return Path(file_path).suffix.lower()
