"""Image compression, link preview fetching, and file utilities."""

import base64
import io
import logging
import os
import re
import struct
import urllib.request
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

MAX_IMAGE_DIMENSION = 1200
JPEG_QUALITY = 80
LINK_PREVIEW_TIMEOUT = 5
MAX_PREVIEW_SIZE = 2 * 1024 * 1024  # 2MB max for preview download


def compress_image(data: bytes, mime_type: str = "image/jpeg") -> tuple[bytes, str]:
    """Compress image to max 1200px on longest side. Returns (compressed_data, mime_type)."""
    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow not installed — returning original image")
        return data, mime_type

    img = Image.open(io.BytesIO(data))
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGBA")

    w, h = img.size
    scale = MAX_IMAGE_DIMENSION / max(w, h)
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    out = io.BytesIO()
    fmt = "JPEG" if img.mode == "RGBA" else "JPEG"
    if img.mode == "RGBA":
        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(background, img).convert("RGB")
    else:
        img = img.convert("RGB")

    img.save(out, format=fmt, quality=JPEG_QUALITY, optimize=True)
    return out.getvalue(), "image/jpeg"


def image_to_base64(data: bytes) -> str:
    """Convert raw image bytes to a base64 data URI string."""
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def format_file_size(size_bytes: int) -> str:
    """Format byte count as human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_file_icon(filename: str) -> str:
    """Return an emoji icon based on file extension."""
    ext = os.path.splitext(filename)[1].lower()
    icons = {
        ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️", ".gif": "🖼️",
        ".webp": "🖼️", ".bmp": "🖼️", ".svg": "🖼️",
        ".mp3": "🎵", ".wav": "🎵", ".ogg": "🎵", ".flac": "🎵",
        ".mp4": "🎬", ".mov": "🎬", ".avi": "🎬", ".mkv": "🎬",
        ".pdf": "📕", ".doc": "📝", ".docx": "📝", ".txt": "📄",
        ".zip": "📦", ".rar": "📦", ".tar": "📦", ".gz": "📦",
        ".py": "💻", ".js": "💻", ".html": "💻", ".css": "💻",
    }
    return icons.get(ext, "📄")


def chunk_file(filepath: str, chunk_size: int = 1024 * 256) -> list[bytes]:
    """Split a file into chunks for transfer. Returns list of byte chunks."""
    chunks = []
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
    return chunks


def fetch_link_preview(url: str) -> dict | None:
    """Fetch OpenGraph/title/description for a URL. Returns dict or None."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "ChitChat/1.0 LinkPreview",
            "Accept": "text/html",
        })
        with urllib.request.urlopen(req, timeout=LINK_PREVIEW_TIMEOUT) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return {"url": url, "domain": urlparse(url).netloc}
            content = resp.read(MAX_PREVIEW_SIZE).decode("utf-8", errors="ignore")
    except Exception:
        return {"url": url, "domain": urlparse(url).netloc}

    preview = {"url": url, "domain": urlparse(url).netloc}

    # Extract <title>
    title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.I | re.S)
    if title_match:
        preview["title"] = title_match.group(1).strip()[:200]

    # Extract OpenGraph tags
    for prop, key in [
        ("og:title", "title"), ("og:description", "description"),
        ("og:image", "thumbnail"), ("og:site_name", "site_name"),
    ]:
        m = re.search(
            rf'<meta\s+property=["\']{prop}["\']\s+content=["\'](.*?)["\']',
            content, re.I)
        if m:
            preview[key] = m.group(1).strip()[:500]

    if "description" not in preview:
        desc_match = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
            content, re.I)
        if desc_match:
            preview["description"] = desc_match.group(1).strip()[:300]

    return preview
