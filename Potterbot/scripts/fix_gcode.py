"""Rewrite Potterbot G-code so the ram sees Cura-like flow.

PrusaSlicer (1) uses a rounded-rectangle bead, so the same nominal width is
leaner than Cura's rectangle, and (2) ramps E from ~0 to full over the first
spiral loop. A clay ram is a piston: commanded E is how far it moves. Tiny E
starves the bead. Scale print E to Cura volume, then hold full E/mm on every
climbing spiral start (including each object in sequential prints).

Retracts, unretracts, and the end E-500 are left alone.
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

from generate_bundle import cura_flow_multiplier, layer_for_nozzle

MOVE_RE = re.compile(r"^\s*(?P<cmd>G[01])\b(?P<body>[^;]*)", re.I)
AXIS_RE = re.compile(r"\b([XYZEF])\s*(-?[0-9]+(?:\.[0-9]+)?)", re.I)
E_RE = re.compile(r"\bE(-?[0-9]+(?:\.[0-9]+)?)", re.I)
NOZZLE_RE = re.compile(r"^;\s*nozzle_diameter\s*=\s*([0-9.]+)", re.I)
LAYER_RE = re.compile(r"^;\s*layer_height\s*=\s*([0-9.]+)", re.I)
HEIGHT_RE = re.compile(r"^;\s*HEIGHT:\s*(-?[0-9.]+)", re.I)
TYPE_RE = re.compile(r"^;\s*TYPE:\s*(.*)$", re.I)
CUSTOM_TYPES = frozenset({"custom", "wipe tower"})

POST_COMMENT = (
    "; Potterbot post: print E scaled to Cura rectangular volume; "
    "spiral start held at full ram flow"
)


def _axes(body: str) -> dict[str, float]:
    return {m.group(1).upper(): float(m.group(2)) for m in AXIS_RE.finditer(body)}


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return 0.5 * (ordered[mid - 1] + ordered[mid])


def _parse_header(lines: list[str]) -> tuple[float, float]:
    nozzle = 5.0
    layer = 1.5
    for raw in lines[:80]:
        match = NOZZLE_RE.match(raw)
        if match:
            nozzle = float(match.group(1).split(",")[0])
        match = LAYER_RE.match(raw)
        if match:
            layer = float(match.group(1).split(",")[0])
    if layer <= 0:
        layer = layer_for_nozzle(int(round(nozzle)))
    return nozzle, layer


def _replace_e(line: str, new_e: float) -> str:
    def _sub(match: re.Match[str]) -> str:
        return f"E{new_e:.5f}"

    return E_RE.sub(_sub, line, count=1)


def apply(text: str) -> str:
    if POST_COMMENT in text:
        return text
    lines = text.splitlines()
    nozzle, layer = _parse_header(lines)
    multiplier = cura_flow_multiplier(nozzle, layer)

    x = y = z = 0.0
    xy_known = False
    relative = False
    current_type = ""
    layer_id = -1
    height = layer

    class Seg:
        __slots__ = ("index", "dist", "e", "z0", "z1", "layer", "height", "custom")

        def __init__(
            self,
            index: int,
            dist: float,
            e: float,
            z0: float,
            z1: float,
            layer: int,
            height: float,
            custom: bool,
        ) -> None:
            self.index = index
            self.dist = dist
            self.e = e
            self.z0 = z0
            self.z1 = z1
            self.layer = layer
            self.height = height
            self.custom = custom

    segs: list[Seg] = []

    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped.upper() == ";LAYER_CHANGE":
            layer_id += 1
            current_type = ""
            continue
        height_match = HEIGHT_RE.match(raw)
        if height_match:
            height = float(height_match.group(1))
            continue
        type_match = TYPE_RE.match(raw)
        if type_match:
            current_type = type_match.group(1).strip().lower()
            continue
        code = raw.split(";", 1)[0].strip()
        if not code:
            continue
        upper = code.upper()
        if upper.startswith("G90"):
            relative = False
            continue
        if upper.startswith("G91"):
            relative = True
            continue
        move = MOVE_RE.match(code)
        if not move:
            continue
        axes = _axes(move.group("body"))
        nx, ny, nz = x, y, z
        if "X" in axes:
            nx = x + axes["X"] if relative else axes["X"]
        if "Y" in axes:
            ny = y + axes["Y"] if relative else axes["Y"]
        if "Z" in axes:
            nz = z + axes["Z"] if relative else axes["Z"]
        dist = math.hypot(nx - x, ny - y) if xy_known or "X" in axes or "Y" in axes else 0.0
        e = axes.get("E", 0.0)
        custom = current_type in CUSTOM_TYPES or relative
        if dist > 0.05 and e > 0.0 and not custom:
            segs.append(Seg(i, dist, e, z, nz, layer_id, height, custom))
        x, y, z = nx, ny, nz
        if "X" in axes or "Y" in axes:
            xy_known = True

    # Scale print E to Cura's rectangular volume.
    scaled_e = {seg.index: seg.e * multiplier for seg in segs}

    by_layer: dict[int, list[Seg]] = {}
    for seg in segs:
        by_layer.setdefault(seg.layer, []).append(seg)

    full_rates = [
        scaled_e[seg.index] / seg.dist
        for seg in segs
        if abs(seg.z1 - seg.z0) < 0.05 and seg.dist > 0.5
    ]
    full = _median(full_rates)

    for layer_segs in by_layer.values():
        climb = max(s.z1 for s in layer_segs) - min(s.z0 for s in layer_segs)
        need = max(0.4 * (layer_segs[0].height or layer), 0.4)
        if climb < need:
            continue
        rates = [scaled_e[s.index] / s.dist for s in layer_segs if s.dist > 0.2]
        if len(rates) < 4:
            continue
        start = _median(rates[: max(2, len(rates) // 5)])
        end = _median(rates[-max(2, len(rates) // 5) :])
        target = full if full > 0 else end
        if target <= 0:
            continue
        # Ramp: first part of the loop is starved relative to the end / file full flow.
        if start >= 0.5 * target:
            continue
        for seg in layer_segs:
            scaled_e[seg.index] = target * seg.dist

    if not scaled_e:
        return text

    out: list[str] = []
    wrote_comment = False
    for i, raw in enumerate(lines):
        if i in scaled_e:
            out.append(_replace_e(raw, scaled_e[i]))
        else:
            out.append(raw)
        if not wrote_comment and raw.strip().upper() == ";LAYER_CHANGE":
            out.append(POST_COMMENT)
            wrote_comment = True
    if not wrote_comment:
        out.append(POST_COMMENT)

    ended = text.endswith("\n")
    result = "\n".join(out)
    if ended:
        result += "\n"
    return result


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("usage: fix_gcode.py <file.gcode>", file=sys.stderr)
        return 2
    path = Path(args[-1])
    original = path.read_text(encoding="utf-8", errors="replace")
    fixed = apply(original)
    if fixed != original:
        path.write_text(fixed, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
