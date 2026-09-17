"""Post-process must match Cura volume and hold full flow on the spiral start."""

from __future__ import annotations

import math
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fix_gcode import POST_COMMENT, apply  # noqa: E402
from generate_bundle import cura_flow_multiplier  # noqa: E402

E_RE = re.compile(r"\bE(-?[0-9]+(?:\.[0-9]+)?)")


SPIRAL = """\
; nozzle_diameter = 5
; layer_height = 1.5
G90
M83
G1 X0 Y0 Z1.5 F2400
;LAYER_CHANGE
;Z:1.5
;HEIGHT:1.5
;TYPE:Skirt/Brim
G1 X100 Y0 E291.74
G1 X100 Y100 E291.74
;LAYER_CHANGE
;Z:3
;HEIGHT:1.5
;TYPE:External perimeter
G1 Z1.6 X110 Y100 E0.50
G1 Z1.8 X120 Y100 E1.00
G1 Z2.2 X130 Y100 E8.00
G1 Z2.6 X140 Y100 E20.00
G1 Z3.0 X150 Y100 E29.174
G91
G0 Z10 E-500 F1000
G90
"""


class FixGcodeTests(unittest.TestCase):
    def _e_values(self, text: str, kind: str) -> list[float]:
        values: list[float] = []
        capture = False
        for raw in text.splitlines():
            if raw.upper().startswith(";TYPE:"):
                capture = kind.lower() in raw.lower()
                continue
            if not capture:
                continue
            match = E_RE.search(raw.split(";", 1)[0])
            if match:
                value = float(match.group(1))
                if value > 0:
                    values.append(value)
        return values

    def test_cura_multiplier_on_5mm(self) -> None:
        self.assertAlmostEqual(cura_flow_multiplier(5.0, 1.5), 7.5 / (1.5 * (5.0 - 1.5 * (1 - math.pi / 4))), places=6)

    def test_skirt_e_matches_cura_rectangle(self) -> None:
        fixed = apply(SPIRAL)
        self.assertIn(POST_COMMENT, fixed)
        skirt = self._e_values(fixed, "Skirt")
        self.assertEqual(len(skirt), 2)
        # 100 mm of path at Cura 5 x 1.5 mm = 7.5 mm2. Filament 1.75 mm:
        # E/mm = 7.5 / (pi * 1.75^2 / 4). The source used Prusa's 2.9174 E/mm;
        # scale by the Cura/Prusa area ratio.
        expected = 291.74 * cura_flow_multiplier(5.0, 1.5)
        for value in skirt:
            self.assertAlmostEqual(value, expected, places=2)

    def test_spiral_start_is_full_flow(self) -> None:
        fixed = apply(SPIRAL)
        peri = self._e_values(fixed, "External perimeter")
        self.assertEqual(len(peri), 5)
        full_e_per_mm = 291.74 * cura_flow_multiplier(5.0, 1.5) / 100.0
        for value in peri:
            self.assertAlmostEqual(value, full_e_per_mm * 10.0, places=2)

    def test_retracts_untouched(self) -> None:
        fixed = apply(SPIRAL)
        self.assertIn("E-500", fixed)

    def test_each_sequential_object_spiral_is_full(self) -> None:
        # Two complete-object spirals: both first climbing loops start starved.
        two = SPIRAL.replace(
            "G91\nG0 Z10 E-500 F1000\nG90\n",
            ";LAYER_CHANGE\n;Z:1.5\n;HEIGHT:1.5\n;TYPE:Skirt/Brim\n"
            "G1 X200 Y0 E291.74\n"
            ";LAYER_CHANGE\n;Z:3\n;HEIGHT:1.5\n;TYPE:External perimeter\n"
            "G1 Z1.6 X210 Y0 E0.50\n"
            "G1 Z1.8 X220 Y0 E1.00\n"
            "G1 Z2.2 X230 Y0 E8.00\n"
            "G1 Z2.6 X240 Y0 E20.00\n"
            "G1 Z3.0 X250 Y0 E29.174\n"
            "G91\nG0 Z10 E-500 F1000\nG90\n",
        )
        peri = self._e_values(apply(two), "External perimeter")
        self.assertEqual(len(peri), 10)
        full = 291.74 * cura_flow_multiplier(5.0, 1.5) / 100.0 * 10.0
        for value in peri:
            self.assertAlmostEqual(value, full, places=2)

    def test_idempotent(self) -> None:
        once = apply(SPIRAL)
        self.assertEqual(apply(once), once)


if __name__ == "__main__":
    unittest.main()
