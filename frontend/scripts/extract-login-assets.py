"""FE-03.4: tách phần minh họa Login.png, không lấy form/header/footer hoặc sửa ảnh nguồn."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = Path(__file__).resolve().parents[1] / "src" / "assets" / "auth"
    # Chỉ phần trang trí bên trái; card bắt đầu x840, footer bắt đầu y974.
    box = (1, 101, 820, 974)
    target = output / "login-illustration.webp"
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    with Image.open(source) as image:
        if image.size != (1556, 1091):
            raise SystemExit(
                "Ảnh Login khác kích thước đã review; cần kiểm tra crop trước khi xuất."
            )
        cropped = image.crop(box)
        cropped.save(
            target,
            format="WEBP",
            lossless=True,
            method=6,
            icc_profile=image.info.get("icc_profile", b""),
        )
        with Image.open(target) as decoded:
            identical = cropped.convert("RGBA").tobytes() == decoded.convert("RGBA").tobytes()
        if not identical or hashlib.sha256(source.read_bytes()).hexdigest() != original_hash:
            raise SystemExit("Pixel hoặc source thay đổi ngoài dự kiến.")
    manifest = {
        "source": "User-provided Login.png, 1556x1091",
        "sourceSha256": original_hash,
        "method": "Original decorative region only, Pillow crop and lossless WebP",
        "figmaContextUnavailable": "MCP Starter quota exhausted",
        "file": target.name,
        "box": box,
        "width": cropped.width,
        "height": cropped.height,
        "pixelIdentityVerified": identical,
        "sourceUnchanged": True,
        "excludesFormHeaderAndPersonalContactFooter": True,
    }
    (output / "login-source.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print("Exported one original decorative Login region; source unchanged.")


if __name__ == "__main__":
    main()
