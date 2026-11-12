"""Render the editable ERD layout without connecting to Django or a database.

SVG uses only the standard library. PNG additionally uses Pillow in a separate
documentation environment; it is deliberately not an application dependency.
"""

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "docs" / "database" / "erd.json"
COLORS = {"cascade": "#296294", "set_null": "#9060a8"}


def validate_layout(data):
    width, height = data["canvas"]["width"], data["canvas"]["height"]
    entities = {entity["id"]: entity for entity in data["entities"]}
    if len(entities) != len(data["entities"]):
        raise ValueError("Entity IDs must be unique.")
    for entity in entities.values():
        x, y, w, h = (entity[key] for key in ("x", "y", "width", "height"))
        if min(x, y) < 0 or x + w > width or y + h > height:
            raise ValueError(f"Entity outside canvas: {entity['id']}")
        if 102 + (len(entity["rows"]) - 1) * 27 > h - 12:
            raise ValueError(f"Rows overflow entity: {entity['id']}")
    boxes = list(entities.values())
    for position, first in enumerate(boxes):
        for second in boxes[position + 1 :]:
            if max(first["x"], second["x"]) < min(
                first["x"] + first["width"], second["x"] + second["width"]
            ) and max(first["y"], second["y"]) < min(
                first["y"] + first["height"], second["y"] + second["height"]
            ):
                raise ValueError(f"Overlapping entities: {first['id']}, {second['id']}")
    for edge in data["relationships"]:
        if edge["from"] not in entities or edge["to"] not in entities:
            raise ValueError("Relationship points to an unknown entity.")
        for start, end in zip(edge["points"], edge["points"][1:]):
            if start[0] != end[0] and start[1] != end[1]:
                raise ValueError("Relationship paths must be orthogonal.")
            for entity in boxes:
                if entity["id"] in {edge["from"], edge["to"]}:
                    continue
                x, y, w, h = (entity[key] for key in ("x", "y", "width", "height"))
                crosses = (
                    start[0] == end[0]
                    and x < start[0] < x + w
                    and max(min(start[1], end[1]), y) < min(max(start[1], end[1]), y + h)
                ) or (
                    start[1] == end[1]
                    and y < start[1] < y + h
                    and max(min(start[0], end[0]), x) < min(max(start[0], end[0]), x + w)
                )
                if crosses:
                    raise ValueError(
                        f"Relationship crosses entity: {edge['from']} -> {edge['to']} / {entity['id']}"
                    )


def drawing_operations(data):
    """Use the same primitives for SVG and PNG so both exports stay aligned."""
    operations = []

    def text(x, y, value, size=20, color="#23344d", *, bold=False, mono=False):
        operations.append(("text", (x, y, value, size, color, bold, mono)))

    text(80, 62, data["title"], 42, bold=True)
    text(80, 99, data["subtitle"], 22, "#607086")
    labels = set()
    for edge in data["relationships"]:
        operations.append(
            ("line", (edge["points"], COLORS[edge["kind"]], edge["kind"] == "set_null"))
        )
        for label in edge["labels"]:
            labels.add((label["x"], label["y"], label["text"], COLORS[edge["kind"]]))
    for x, y, value, color in sorted(labels):
        text(x, y, value, 18, color, bold=True)
    for entity in data["entities"]:
        x, y, w, h = (entity[key] for key in ("x", "y", "width", "height"))
        operations.append(("rect", (x, y, w, h, "#ffffff", "#cdd6e1", 16)))
        operations.append(("rect", (x, y, w, 57, entity["color"], entity["color"], 16)))
        text(x + 22, y + 38, entity["title"], 27, "#ffffff", bold=True)
        text(x + 22, y + 79, entity["table"], 15, "#65758a", mono=True)
        for index, row in enumerate(entity["rows"]):
            key = row.startswith(("PK ", "FK ", "UQ ", "IDX "))
            text(x + 22, y + 102 + index * 27, row, 17, "#215c86" if key else "#23344d", mono=True)
    note = data["notes"]
    operations.append(
        ("rect", (note["x"], note["y"], note["width"], note["height"], "#eef4fa", "#d5e1ed", 16))
    )
    text(note["x"] + 28, note["y"] + 48, note["title"], 29, bold=True)
    for index, line in enumerate(note["lines"]):
        text(note["x"] + 28, note["y"] + 100 + index * 39, line, 22, "#43566f")
    text(80, 1935, "RELATIONSHIP LEGEND", 24, bold=True)
    text(
        80,
        1972,
        "Solid: CASCADE     Dashed: SET_NULL (nullable source FK)     1 / 0..1 / 0..N: cardinality at each entity",
        21,
    )
    text(
        80,
        2008,
        "The blue User branches share a bus. PK/FK types reflect the current models; see docs/DATABASE.md for complete fields and rules.",
        20,
        "#607086",
    )
    return operations


def write_svg(path, data, operations):
    width, height = data["canvas"]["width"], data["canvas"]["height"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(data["title"])}</title>',
        '<desc id="desc">Ten database entities, primary and foreign keys, relationship cardinality, deletion rules, and quiz history snapshots.</desc>',
        f'<rect width="{width}" height="{height}" fill="#f8fafc"/>',
    ]
    for kind, values in operations:
        if kind == "rect":
            x, y, w, h, fill, stroke, radius = values
            parts.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
            )
        elif kind == "line":
            points, color, dashed = values
            positions = " ".join(f"{x},{y}" for x, y in points)
            dash = ' stroke-dasharray="11 8"' if dashed else ""
            parts.append(
                f'<polyline points="{positions}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"{dash}/>'
            )
        else:
            x, y, value, size, color, bold, mono = values
            family = (
                "Menlo, DejaVu Sans Mono, monospace" if mono else "Arial, DejaVu Sans, sans-serif"
            )
            weight = "700" if bold else "400"
            parts.append(
                f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" font-weight="{weight}">{html.escape(value)}</text>'
            )
    path.write_text("\n".join(parts) + "\n</svg>\n", encoding="utf-8")


def pillow_font(size, *, bold=False, mono=False):
    from PIL import ImageFont

    candidates = (
        ["/System/Library/Fonts/Menlo.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
        if mono
        else [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
            if bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default(size=size)


def write_png(path, data, operations):
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError(
            "SVG was generated. PNG needs Pillow in the documentation renderer environment; use --svg-only or the system Python with Pillow."
        ) from exc
    image = Image.new("RGB", (data["canvas"]["width"], data["canvas"]["height"]), "#f8fafc")
    draw = ImageDraw.Draw(image)
    for kind, values in operations:
        if kind == "rect":
            x, y, w, h, fill, stroke, radius = values
            draw.rounded_rectangle(
                (x, y, x + w, y + h), radius=radius, fill=fill, outline=stroke, width=2
            )
        elif kind == "line":
            points, color, dashed = values
            for start, end in zip(points, points[1:]):
                if not dashed:
                    draw.line((tuple(start), tuple(end)), fill=color, width=3)
                    continue
                length = abs(end[0] - start[0]) + abs(end[1] - start[1])
                for offset in range(0, length, 19):
                    stop = min(offset + 11, length)
                    first = (
                        start[0] + (end[0] - start[0]) * offset / length,
                        start[1] + (end[1] - start[1]) * offset / length,
                    )
                    last = (
                        start[0] + (end[0] - start[0]) * stop / length,
                        start[1] + (end[1] - start[1]) * stop / length,
                    )
                    draw.line((first, last), fill=color, width=3)
        else:
            x, y, value, size, color, bold, mono = values
            draw.text(
                (x, y), value, font=pillow_font(size, bold=bold, mono=mono), fill=color, anchor="ls"
            )
    image.save(path, dpi=(150, 150))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_SOURCE.parent)
    parser.add_argument(
        "--svg-only", action="store_true", help="Use only the Python standard library."
    )
    args = parser.parse_args()
    data = json.loads(args.source.read_text(encoding="utf-8"))
    validate_layout(data)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    operations = drawing_operations(data)
    svg = args.output_dir / "erd.svg"
    write_svg(svg, data, operations)
    print(f"SVG: {svg}")
    if not args.svg_only:
        png = args.output_dir / "erd.png"
        write_png(png, data, operations)
        print(f"PNG: {png}")
    print(
        f"Validated {len(data['entities'])} entities and {len(data['relationships'])} relationships; no database access."
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        print(f"ERD render failed: {error}", file=sys.stderr)
        sys.exit(1)
