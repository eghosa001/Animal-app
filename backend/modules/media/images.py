"""Restrict image formats and dimensions; normalize bytes to metadata-free JPEG."""
import hashlib
import io
import warnings
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

ALLOWED_MIME_TO_FORMAT = {"image/jpeg": "JPEG", "image/png": "PNG"}
MAX_INPUT_PIXELS = 18_000_000
MAX_OUTPUT_DIMENSION = 2400
MAX_LISTING_BYTES = 8 * 1024 * 1024
MAX_EVIDENCE_BYTES = 5 * 1024 * 1024

# Pillow limit is an extra guard. The explicit dimensions are checked before decode.
Image.MAX_IMAGE_PIXELS = MAX_INPUT_PIXELS


@dataclass(frozen=True)
class CleanImage:
    body: bytes
    sha256: str
    width: int
    height: int


def sanitize_image(upload, *, max_bytes):
    """Decode and re-encode. Never trust a filename, extension or claimed MIME alone."""
    if upload is None or not getattr(upload, "size", 0):
        raise ValidationError({"file": ["An image file is required"]})
    if upload.size > max_bytes:
        raise ValidationError({"file": ["Image exceeds the allowed size"]})
    declared_type = (getattr(upload, "content_type", "") or "").lower().split(";")[0].strip()
    if declared_type not in ALLOWED_MIME_TO_FORMAT:
        raise ValidationError({"file": ["Only JPEG or PNG images are accepted"]})
    raw = upload.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValidationError({"file": ["Image exceeds the allowed size"]})
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as opened:
                if opened.format != ALLOWED_MIME_TO_FORMAT[declared_type]:
                    raise ValidationError({"file": ["Declared image type does not match file contents"]})
                if getattr(opened, "n_frames", 1) != 1:
                    raise ValidationError({"file": ["Animated or multi-frame images are not accepted"]})
                width, height = opened.size
                if width < 1 or height < 1 or width * height > MAX_INPUT_PIXELS:
                    raise ValidationError({"file": ["Invalid or oversized image dimensions"]})
                image = ImageOps.exif_transpose(opened)
                image.load()
                image = image.convert("RGB")
                image.thumbnail((MAX_OUTPUT_DIMENSION, MAX_OUTPUT_DIMENSION))
                output = io.BytesIO()
                # Freshly encoded JPEG does not contain the untrusted EXIF, ICC, or comment.
                image.save(output, format="JPEG", quality=86, optimize=True)
                clean = output.getvalue()
                result_width, result_height = image.size
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError({"file": ["Image could not be safely decoded"]}) from exc
    if len(clean) > max_bytes:
        raise ValidationError({"file": ["Processed image exceeds size limit"]})
    return CleanImage(
        body=clean,
        sha256=hashlib.sha256(clean).hexdigest(),
        width=result_width,
        height=result_height,
    )
