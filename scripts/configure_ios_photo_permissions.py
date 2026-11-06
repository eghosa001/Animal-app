#!/usr/bin/env python3
"""Idempotently configure iOS photo library purpose string after Flutter runner generation.

Run after flutter create; do not commit generated Runner/Info.plist until the
final client-owned iOS bundle identifier is approved.
"""
import plistlib
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: configure_ios_photo_permissions.py <ios/Runner/Info.plist>")
    path = Path(sys.argv[1])
    with path.open("rb") as stream:
        content = plistlib.load(stream)
    content["NSPhotoLibraryUsageDescription"] = (
        "Choose photos of your animals or private verification documents to upload."
    )
    # The current flow selects still images only from the gallery, not the camera.
    with path.open("wb") as stream:
        plistlib.dump(content, stream, sort_keys=False)


if __name__ == "__main__":
    main()
