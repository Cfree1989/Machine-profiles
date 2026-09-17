"""Validator must accept official-style clay G-code and reject heat or missing retract."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_gcode import ValidationError, validate  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class GcodeSafetyTests(unittest.TestCase):
    def test_good_vase_passes(self) -> None:
        validate((FIXTURES / "good_vase.gcode").read_text(encoding="utf-8"))

    def test_heat_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate((FIXTURES / "heat_rejected.gcode").read_text(encoding="utf-8"))
        self.assertIn("heater", str(ctx.exception).lower())

    def test_missing_end_retract_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate((FIXTURES / "no_retract_rejected.gcode").read_text(encoding="utf-8"))
        self.assertIn("E-500", str(ctx.exception))

    def test_retract_at_z400_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate((FIXTURES / "retract_at_z400_rejected.gcode").read_text(encoding="utf-8"))
        self.assertIn("Z400", str(ctx.exception))

    def test_end_push_e500_is_not_a_retract(self) -> None:
        text = (FIXTURES / "good_vase.gcode").read_text(encoding="utf-8").replace("E-500", "E500")
        with self.assertRaises(ValidationError) as ctx:
            validate(text)
        self.assertIn("E-500", str(ctx.exception))

    def test_official_cura_end_retract_present(self) -> None:
        sample = (ROOT / "reference" / "cura" / "no_bottom__layers.gcode").read_text(
            encoding="utf-8", errors="replace"
        )
        self.assertIn("G0 Z10 E-500 F1000", sample)
        self.assertIn("G28 ;Home All", sample)


if __name__ == "__main__":
    unittest.main()
