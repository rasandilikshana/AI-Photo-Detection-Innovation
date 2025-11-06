"""
Security utilities
"""

import re
from typing import List
from app.config import settings


def generate_slug(title: str) -> str:
    """
    Generate URL-friendly slug from title

    Example:
        "My Amazing Photo Competition!" -> "my-amazing-photo-competition"
    """
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


def validate_file_extension(filename: str, allowed_extensions: List[str] = None) -> bool:
    """
    Validate file extension

    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (default: from settings)

    Returns:
        True if extension is allowed, False otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = settings.allowed_extensions_list

    if '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove directory separators
    filename = filename.replace('/', '').replace('\\', '')

    # Remove potentially dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)

    return filename
