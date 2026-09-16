"""Generate the Potterbot vendor-folder assets PrusaSlicer draws on the plater.

Writes vendor/Potterbot/POTTERBOT9_bed.stl (the 15x15 in bat) and
vendor/Potterbot/POTTERBOT9_texture.svg (white textured bat surface).

PrusaSlicer 2.9.6 only draws a vendor bed when BOTH bed_model and bed_texture
resolve (Bed3D::detect_type), so both files are required. The STL origin is
placed at the centre of bed_shape with Z 0 at the bat top. The texture is
stretched over the bed_shape bounding box (image top = back of the bed) and
drawn only inside the bed_shape polygon, which is why the rounded front
corners live in bed_shape (generate_bundle.py) and not in the SVG: SVG
textures are always opaque in PrusaSlicer's printbed shader, so a transparent
corner would render as dark grey, not as background.

Standard library only. The wizard thumbnail (POTTERBOT9_thumbnail.png) is a
one-off image crop; see tools/make_thumbnail.ps1.
"""

from __future__ import annotations

import math
import random
import struct
from pathlib import Path

import generate_bundle as bundle

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "vendor" / "Potterbot"
BED_STL = ASSET_DIR / "POTTERBOT9_bed.stl"
BED_SVG = ASSET_DIR / "POTTERBOT9_texture.svg"

# Printable area (bed_shape in the bundle): 15 in bat clipped to Y travel.
BED_X = float(bundle.BED_X)
BED_Y = float(bundle.BED_Y)

# Physical bat: 15 x 15 in, ~1/4 in thick, rounded corners, starts at X0 Y0.
BAT_SIZE = 381.0
BAT_THICKNESS = 6.35
BAT_CORNER_RADIUS = bundle.BAT_CORNER_RADIUS
CORNER_SEGMENTS = bundle.BED_CORNER_SEGMENTS

# Used-bat grey with a visible dark grid (same idea as the Raise3D plate, inverted).
BAT_FILL = "#A9A5A0"
BAT_SPECKLE_DARK = "#6F6B66"
BAT_SPECKLE_LIGHT = "#D3CFC9"
BAT_EDGE = "#4A4744"
GRID_STROKE = "#26241F"
GRID_OPACITY = 0.28
GRID_OPACITY_STRONG = 0.55
SPECKLE_COUNT = 2600
SPECKLE_SEED = 20260916


def rounded_rect(
    x0: float, y0: float, x1: float, y1: float, radius: float, segments: int
) -> list[tuple[float, float]]:
    """Counter-clockwise outline of a rounded rectangle."""
    r = min(radius, (x1 - x0) / 2, (y1 - y0) / 2)
    corners = [
        (x1 - r, y0 + r, -90.0),  # bottom-right
        (x1 - r, y1 - r, 0.0),  # top-right
        (x0 + r, y1 - r, 90.0),  # top-left
        (x0 + r, y0 + r, 180.0),  # bottom-left
    ]
    points: list[tuple[float, float]] = []
    for cx, cy, start in corners:
        for i in range(segments + 1):
            a = math.radians(start + 90.0 * i / segments)
            points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return points


def prism_triangles(
    outline: list[tuple[float, float]], z_bottom: float, z_top: float
) -> list[tuple[tuple[float, float, float], ...]]:
    """Triangles (CCW seen from outside) for a convex prism."""
    cx = sum(p[0] for p in outline) / len(outline)
    cy = sum(p[1] for p in outline) / len(outline)
    tris: list[tuple[tuple[float, float, float], ...]] = []
    n = len(outline)
    for i in range(n):
        ax, ay = outline[i]
        bx, by = outline[(i + 1) % n]
        # Top (normal +Z): fan from the centre, CCW.
        tris.append(((cx, cy, z_top), (ax, ay, z_top), (bx, by, z_top)))
        # Bottom (normal -Z): reversed winding.
        tris.append(((cx, cy, z_bottom), (bx, by, z_bottom), (ax, ay, z_bottom)))
        # Side wall (outward normal): two triangles.
        tris.append(((ax, ay, z_bottom), (bx, by, z_bottom), (bx, by, z_top)))
        tris.append(((ax, ay, z_bottom), (bx, by, z_top), (ax, ay, z_top)))
    return tris


def normal(tri: tuple[tuple[float, float, float], ...]) -> tuple[float, float, float]:
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / length, ny / length, nz / length)


def write_binary_stl(path: Path, tris: list[tuple[tuple[float, float, float], ...]], name: str) -> None:
    header = name.encode("ascii")[:80].ljust(80, b"\0")
    out = bytearray(header)
    out += struct.pack("<I", len(tris))
    for tri in tris:
        out += struct.pack("<3f", *normal(tri))
        for v in tri:
            out += struct.pack("<3f", *v)
        out += struct.pack("<H", 0)
    path.write_bytes(bytes(out))


def bat_stl_triangles() -> list[tuple[tuple[float, float, float], ...]]:
    # PrusaSlicer puts the STL origin at the bed_shape centre. The bat starts at
    # bed X0 Y0 and is 381 mm square, so in model coordinates it runs
    # X -190.5..190.5 and Y -180..201 (21 mm overhang at the back).
    cx = BED_X / 2
    cy = BED_Y / 2
    outline = rounded_rect(0.0 - cx, 0.0 - cy, BAT_SIZE - cx, BAT_SIZE - cy, BAT_CORNER_RADIUS, CORNER_SEGMENTS)
    return prism_triangles(outline, -BAT_THICKNESS, 0.0)


def bed_outline_svg_points(inset: float) -> str:
    """bed_shape outline in SVG coordinates (y down = towards the front), shrunk by inset."""
    r = BAT_CORNER_RADIUS - inset
    x0, x1 = inset, BED_X - inset
    y_back, y_front = inset, BED_Y - inset
    pts: list[tuple[float, float]] = [(x0, y_back), (x1, y_back)]
    # Front-right corner: centre (x1 - r, y_front - r), 0 deg -> 90 deg (SVG y down).
    for i in range(CORNER_SEGMENTS + 1):
        a = math.radians(90.0 * i / CORNER_SEGMENTS)
        pts.append((x1 - r + r * math.cos(a), y_front - r + r * math.sin(a)))
    # Front-left corner: centre (x0 + r, y_front - r), 90 deg -> 180 deg.
    for i in range(CORNER_SEGMENTS + 1):
        a = math.radians(90.0 + 90.0 * i / CORNER_SEGMENTS)
        pts.append((x0 + r + r * math.cos(a), y_front - r + r * math.sin(a)))
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)


def bat_svg() -> str:
    rng = random.Random(SPECKLE_SEED)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{BED_X:g}mm" height="{BED_Y:g}mm" viewBox="0 0 {BED_X:g} {BED_Y:g}">',
        "  <!-- Generated by scripts/generate_assets.py. Printable area of the 15 in bat: grey textured surface with a 10 / 50 mm grid. -->",
        "  <!-- PrusaSlicer clips this to the bed_shape polygon (rounded front corners); the SVG itself is a plain rectangle. -->",
        "  <!-- nanosvg (PrusaSlicer) does not render text or patterns, so the texture is plain shapes only. -->",
        f'  <rect width="{BED_X:g}" height="{BED_Y:g}" fill="{BAT_FILL}"/>',
    ]
    # Two-tone speckle so the surface reads as a used plaster bat rather than flat grey.
    for _ in range(SPECKLE_COUNT):
        x = rng.uniform(0.0, BED_X)
        y = rng.uniform(0.0, BED_Y)
        r = rng.uniform(0.25, 0.8)
        opacity = rng.uniform(0.3, 0.75)
        colour = BAT_SPECKLE_DARK if rng.random() < 0.6 else BAT_SPECKLE_LIGHT
        lines.append(
            f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{colour}" fill-opacity="{opacity:.2f}"/>'
        )
    # 10 mm grid with stronger 50 mm lines for placement.
    for x in range(10, int(BED_X), 10):
        strong = x % 50 == 0
        lines.append(
            f'  <line x1="{x}" y1="0" x2="{x}" y2="{BED_Y:g}" stroke="{GRID_STROKE}" '
            f'stroke-width="{0.6 if strong else 0.3}" stroke-opacity="{GRID_OPACITY_STRONG if strong else GRID_OPACITY}"/>'
        )
    for y in range(10, int(BED_Y), 10):
        strong = y % 50 == 0
        lines.append(
            f'  <line x1="0" y1="{y}" x2="{BED_X:g}" y2="{y}" stroke="{GRID_STROKE}" '
            f'stroke-width="{0.6 if strong else 0.3}" stroke-opacity="{GRID_OPACITY_STRONG if strong else GRID_OPACITY}"/>'
        )
    # Bed edge, following the rounded front corners of bed_shape.
    lines.append(
        f'  <polygon points="{bed_outline_svg_points(0.6)}" fill="none" stroke="{BAT_EDGE}" stroke-width="1.2" stroke-opacity="0.9"/>'
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    write_binary_stl(BED_STL, bat_stl_triangles(), "Potterbot 9 bat 381x381x6.35 mm, origin at bed_shape centre")
    BED_SVG.write_text(bat_svg(), encoding="utf-8", newline="\n")
    print(f"Wrote {BED_STL}")
    print(f"Wrote {BED_SVG}")


if __name__ == "__main__":
    main()
