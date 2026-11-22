"""FE-03.3: tách pixel gốc theo lựa chọn người dùng; không sửa ảnh nguồn hoặc vẽ lại asset."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Register.png do người dùng cung cấp")
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = Path(__file__).resolve().parents[1] / "src" / "assets" / "auth"

    # Tọa độ dành riêng bản export1556x1091 đã kiểm tra; không đoán crop khi source đổi.
    boxes = {
        "register-illustration.webp": (1, 1, 756, 1090),
        "register-cap.png": (1054, 43, 1190, 154),
        "register-email.png": (882, 368, 922, 407),
        "register-lock.png": (888, 486, 927, 526),
        "register-eye-off.png": (1344, 481, 1395, 532),
    }

    with Image.open(source) as image:
        if image.size != (1556, 1091):
            raise SystemExit(
                "Kích thước source khác bản đã review; cần đối chiếu lại trước khi tách."
            )
        output.mkdir(parents=True, exist_ok=True)
        assets = []
        for name, box in boxes.items():
            target = output / name
            cropped = image.crop(box)
            if target.suffix == ".webp":
                # Lossless chỉ đổi codec để tải nhẹ hơn; kiểm tra pixel sau giải mã vẫn giống nguồn.
                cropped.save(
                    target,
                    format="WEBP",
                    lossless=True,
                    method=6,
                    icc_profile=image.info.get("icc_profile", b""),
                )
            else:
                cropped.save(target, format="PNG")
            with Image.open(target) as decoded:
                identical = decoded.convert("RGBA").tobytes() == cropped.convert("RGBA").tobytes()
            if not identical:
                raise SystemExit("Asset không giữ nguyên pixel; cần kiểm tra lại trước khi dùng.")
            assets.append(
                {
                    "file": name,
                    "box": box,
                    "width": cropped.width,
                    "height": cropped.height,
                    "pixelIdentityVerified": identical,
                }
            )

    # Manifest không chứa đường dẫn máy/email; checksum giúp kiểm tra đúng nguồn sau này.
    manifest = {
        "source": "User-provided Register.png",
        "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "method": "Pillow crop + lossless encoding only; decoded pixels and source file retained",
        "authorization": "User delegated closest available Figma source after the asset-source question",
        "assets": assets,
    }
    (output / "source.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(assets)} original image regions; source unchanged.")


if __name__ == "__main__":
    main()
