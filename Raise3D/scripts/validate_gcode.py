"""Safety checks for Raise3D Pro2 Plus Hyper Speed G-code (left, right, and dual)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BED_X = 305.0
BED_Y = 305.0
MAX_Z = 605.0
# Right nozzle (T1): factory ~25 mm X lives in firmware; slicer offset is 0. Do not also apply M218.
T1_MIN_X = 25.0
MAX_HOTEND = 300.0
MAX_BED = 120.0

KNOWN_CMD = re.compile(r"^(?:G\d+|M\d+|T[01]\b|SET_VELOCITY_LIMIT\b)", re.I)
FORBIDDEN = [
    (re.compile(r"^G29\b", re.I), "G29 bed mesh/level is not in the ideaMaker reference"),
    (re.compile(r"^M92\b", re.I), "M92 would overwrite firmware calibrations"),
    (re.compile(r"^M218\b", re.I), "M218 offsets are not in the ideaMaker reference"),
    (re.compile(r"^M600\b", re.I), "M600 is reported not to work on this Klipper conversion"),
    (re.compile(r"^PRINT_START\b", re.I), "generic Klipper PRINT_START is not authoritative"),
    (re.compile(r"^BED_MESH", re.I), "bed mesh command is not in the ideaMaker reference"),
    (re.compile(r"^SET_HEATER_TEMPERATURE\b", re.I), "generic Klipper heater helper not in reference"),
    (
        re.compile(r"^M204\b", re.I),
        "M204 is PrusaSlicer Klipper-flavor accel; convert with ensure_m99123_first.py to SET_VELOCITY_LIMIT (ideaMaker)",
    ),
]
SUSPICIOUS = [
    (re.compile(r"^G28\s*$", re.I), "bare G28 (reference homes X/Y then Z separately)"),
]


def strip_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()


def temps(line: str) -> list[tuple[str, float]]:
    found = []
    if re.match(r"^M10[49]\b", line, re.I) or re.match(r"^M1[49]0\b", line, re.I):
        for m in re.finditer(r"\bS(-?\d+(?:\.\d+)?)", line, re.I):
            cmd = line.split()[0].upper()
            found.append((cmd, float(m.group(1))))
    return found


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    has_t0 = False
    has_t1 = False
    has_m1001 = False
    has_m1002 = False
    has_shutdown_hot = False
    has_shutdown_bed = False
    has_m84 = False
    relative = False
    max_z = 0.0
    saw_m99123 = False
    current_tool: int | None = None
    in_print = False

    if lines and lines[0].startswith("M99123"):
        saw_m99123 = True
    else:
        errors.append("missing M99123 Hyper Speed header on line 1 (required by ideaMaker Hyper Speed files)")

    if ";Dimension:" not in text:
        errors.append("missing ;Dimension: header comment")
    if "RAISE3D Pro2 Plus - Hyper Speed" not in text:
        errors.append("missing ;Printer Type: RAISE3D Pro2 Plus - Hyper Speed")

    for lineno, raw in enumerate(lines, 1):
        line = strip_comment(raw)
        if not line:
            continue
        upper = line.upper()
        if re.match(r"^T0\b", line, re.I):
            has_t0 = True
            current_tool = 0
        if re.match(r"^T1\b", line, re.I):
            has_t1 = True
            current_tool = 1
        if upper.startswith("M1001"):
            has_m1001 = True
            in_print = True
        if upper.startswith("M1002"):
            has_m1002 = True
            in_print = False
        if re.match(r"^M104\b", line, re.I) and re.search(r"\bS0(?:\.0+)?\b", line, re.I):
            has_shutdown_hot = True
        if re.match(r"^M140\b", line, re.I) and re.search(r"\bS0(?:\.0+)?\b", line, re.I):
            has_shutdown_bed = True
        if upper.startswith("M84"):
            has_m84 = True
        if upper.startswith("G91"):
            relative = True
        if upper.startswith("G90"):
            relative = False

        if line and not KNOWN_CMD.match(line):
            where = " after M1001" if in_print else ""
            errors.append(f"line {lineno}: not G-code{where} ({line[:80]})")
        for rx, msg in FORBIDDEN:
            if rx.search(line):
                errors.append(f"line {lineno}: forbidden: {msg} ({line})")
        for rx, msg in SUSPICIOUS:
            if rx.search(line):
                errors.append(f"line {lineno}: suspicious: {msg} ({line})")

        for cmd, temp in temps(line):
            if cmd in {"M104", "M109"} and temp > MAX_HOTEND:
                errors.append(f"line {lineno}: hotend temperature {temp} exceeds {MAX_HOTEND}")
            if cmd in {"M140", "M190"} and temp > MAX_BED:
                errors.append(f"line {lineno}: bed temperature {temp} exceeds {MAX_BED}")

        if not relative:
            xm = re.search(r"\bX(-?\d+(?:\.\d+)?)", line, re.I)
            ym = re.search(r"\bY(-?\d+(?:\.\d+)?)", line, re.I)
            zm = re.search(r"\bZ(-?\d+(?:\.\d+)?)", line, re.I)
            # Homing and purge use Y0 / X20; allow a small negative skirt margin
            if xm:
                x = float(xm.group(1))
                if x < -5 or x > BED_X + 5:
                    errors.append(f"line {lineno}: X {x} outside 0..{BED_X} (with 5 mm margin)")
                if in_print and current_tool == 1 and x < T1_MIN_X:
                    errors.append(
                        f"line {lineno}: T1 X {x} is left of {T1_MIN_X:g} mm keep-out "
                        "(right nozzle firmware offset; start purge before M1001 is allowed)"
                    )
            if ym:
                y = float(ym.group(1))
                if y < -5 or y > BED_Y + 5:
                    errors.append(f"line {lineno}: Y {y} outside 0..{BED_Y} (with 5 mm margin)")
            if zm:
                z = float(zm.group(1))
                max_z = max(max_z, z)
                if z < -0.05:
                    errors.append(f"line {lineno}: negative absolute Z {z}")
                if z > MAX_Z:
                    errors.append(f"line {lineno}: Z {z} exceeds {MAX_Z}")

    if not has_t0 and not has_t1:
        errors.append("missing T0 or T1 tool selection")
    if not has_m1001:
        errors.append("missing M1001 start marker")
    if not has_m1002:
        errors.append("missing M1002 end marker")
    if not has_shutdown_hot:
        errors.append("missing hotend shutdown (M104 S0)")
    if not has_shutdown_bed:
        errors.append("missing bed shutdown (M140 S0)")
    if not has_m84:
        errors.append("missing M84 (motors off)")
    if not saw_m99123:
        pass  # already recorded
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "gcode",
        nargs="?",
        type=Path,
        help="G-code path (PrusaSlicer post-process passes this as the last arg)",
    )
    parser.add_argument("--json", action="store_true")
    args, extra = parser.parse_known_args(argv)
    path = args.gcode
    if extra:
        path = Path(extra[-1])
    if path is None:
        parser.error("gcode path required")
    if not path.is_file():
        print(f"not found: {path}", file=sys.stderr)
        return 1
    errors = validate(path)
    if args.json:
        print(json.dumps({"file": str(path), "ok": not errors, "errors": errors}, indent=2))
    else:
        if errors:
            print(f"FAIL {path}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"PASS {path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
