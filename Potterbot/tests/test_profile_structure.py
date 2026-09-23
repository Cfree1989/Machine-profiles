"""Checks the Potterbot vendor bundle structure."""

from __future__ import annotations

import configparser
import math
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Potterbot.ini"
IDX = ROOT / "vendor" / "Potterbot.idx"
BUNDLE = ROOT / "profiles" / "Potterbot-9-bundle.ini"
ASSETS = ROOT / "vendor" / "Potterbot"

CLAY = "Clay Potterbot"
CLAY_RETRACT = "Clay Potterbot Retract"

sys.path.insert(0, str(ROOT / "scripts"))
import generate_bundle as bundle  # noqa: E402


def stl_bounds(path: Path) -> tuple[int, tuple[float, float], tuple[float, float], tuple[float, float]]:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise AssertionError(f"{path.name}: binary STL size mismatch ({len(data)} bytes for {count} triangles)")
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    offset = 84
    for _ in range(count):
        values = struct.unpack_from("<12f", data, offset)
        offset += 50
        for k in range(3):
            xs.append(values[3 + 3 * k])
            ys.append(values[4 + 3 * k])
            zs.append(values[5 + 3 * k])
    return count, (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


class VendorStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = VENDOR.read_text(encoding="utf-8")
        parser = configparser.RawConfigParser(strict=False)
        parser.optionxform = str
        parser.read_string(text)
        cls.ini = parser
        cls.raw = text

    def test_vendor_files_exist(self) -> None:
        self.assertTrue(VENDOR.is_file())
        self.assertTrue(IDX.is_file())
        self.assertTrue(BUNDLE.is_file())
        self.assertEqual(VENDOR.read_text(encoding="utf-8"), BUNDLE.read_text(encoding="utf-8"))
        self.assertIn("0.1.21 ", IDX.read_text(encoding="utf-8"))

    def test_single_printer_model(self) -> None:
        self.assertEqual(self.ini["vendor"]["name"], "3D Potter (experimental)")
        self.assertEqual(self.ini["vendor"]["repo_id"], "non-prusa-fff")
        self.assertEqual(self.ini["vendor"]["config_version"], "0.1.21")
        model = self.ini["printer_model:POTTERBOT9"]
        self.assertEqual(model["variants"], "1;2;3;4;5;6;7;8;9;10")
        self.assertEqual(model["default_materials"], f"{CLAY};{CLAY_RETRACT}")
        self.assertEqual(model["bed_model"], "POTTERBOT9_bed.stl")
        self.assertEqual(model["bed_texture"], "POTTERBOT9_texture.svg")
        self.assertEqual(model["thumbnail"], "POTTERBOT9_thumbnail.png")
        models = [s for s in self.ini.sections() if s.startswith("printer_model:")]
        self.assertEqual(models, ["printer_model:POTTERBOT9"])
        self.assertNotIn("printer_model:POTTERBOT9R", self.ini)
        self.assertNotIn("CLAY_TRAVEL", self.raw)

    def test_printer_common_is_cold_rrf_unretracted(self) -> None:
        common = self.ini["printer:*common*"]
        self.assertEqual(common["gcode_flavor"], "reprapfirmware")
        self.assertEqual(common["host_type"], "duet")
        self.assertEqual(common["autoemit_temperature_commands"], "0")
        self.assertEqual(common["use_relative_e_distances"], "1")
        self.assertEqual(common["retract_length"], "0")
        self.assertEqual(common["retract_lift"], "0")
        self.assertEqual(common["retract_layer_change"], "0")
        self.assertEqual(common["retract_before_travel"], "15")
        self.assertEqual(common["retract_speed"], "80")
        self.assertEqual(common["deretract_speed"], "80")
        self.assertEqual(common["pause_print_gcode"], "M25")
        self.assertEqual(common["extruder_clearance_height"], "400")
        self.assertEqual(common["extruder_clearance_radius"], "40")
        self.assertEqual(common["default_filament_profile"], f'"{CLAY}"')
        start = common["start_gcode"].replace("\\n", "\n")
        end = common["end_gcode"].replace("\\n", "\n")
        self.assertIn("G28 ;Home all", start)
        self.assertNotIn("G1 Z10 F1000", start)
        self.assertNotIn("E-80", start)
        self.assertNotIn("M104", start)
        self.assertNotIn("M109", start)
        self.assertIn("G0 Z10 E-500 F1000", end)
        self.assertIn("G28 ;Home all", end)

    def test_bed_is_bat_clipped_to_y_travel_with_rounded_front(self) -> None:
        p = self.ini["printer:5mm Nozzle"]
        points = [tuple(float(v) for v in pt.split("x")) for pt in p["bed_shape"].split(",")]
        xs = [x for x, _ in points]
        ys = [y for _, y in points]
        # Bounding box is still the 381 x 360 clip of the bat.
        self.assertEqual((min(xs), max(xs)), (0.0, 381.0))
        self.assertEqual((min(ys), max(ys)), (0.0, 360.0))
        # Back corners are square (bat continues past Y travel)...
        self.assertIn((381.0, 360.0), points)
        self.assertIn((0.0, 360.0), points)
        # ...front corners are rounded 12.7 mm like the bat.
        self.assertNotIn((0.0, 0.0), points)
        self.assertNotIn((381.0, 0.0), points)
        self.assertIn((12.7, 0.0), points)
        self.assertIn((381.0, 12.7), points)
        self.assertIn((0.0, 12.7), points)
        for x, y in points:
            if x < 12.7 and y < 12.7:
                self.assertAlmostEqual(math.hypot(x - 12.7, y - 12.7), 12.7, places=2)
            if x > 381 - 12.7 and y < 12.7:
                self.assertAlmostEqual(math.hypot(x - (381 - 12.7), y - 12.7), 12.7, places=2)
        self.assertGreater(len(points), 20)
        self.assertEqual(p["max_print_height"], "400")
        self.assertEqual(p["nozzle_diameter"], "5")
        # Same polygon on every nozzle variant.
        for nozzle in range(1, 11):
            self.assertEqual(self.ini[f"printer:{nozzle}mm Nozzle"]["bed_shape"], p["bed_shape"])

    def test_ten_nozzle_printers_three_prints_each(self) -> None:
        common = self.ini["print:*common*"]
        self.assertEqual(common["layer_height"], "1.5")
        self.assertEqual(common["first_layer_height"], "1.5")
        printers = [s for s in self.ini.sections() if s.startswith("printer:") and s != "printer:*common*"]
        self.assertEqual(len(printers), 10)
        for nozzle in range(1, 11):
            self.assertIn(f"printer:{nozzle}mm Nozzle", self.ini)
            self.assertNotIn(f"printer:{nozzle}mm Nozzle Retract", self.ini)
            printer = self.ini[f"printer:{nozzle}mm Nozzle"]
            self.assertEqual(printer["printer_model"], "POTTERBOT9")
            self.assertEqual(printer["printer_variant"], str(nozzle))
            layer = min(1.5, 0.8 * float(nozzle))
            self.assertGreaterEqual(float(printer["max_layer_height"]), layer)
            self.assertLess(layer, float(printer["nozzle_diameter"]))
            notes = printer["printer_notes"]
            for keyword in ("PRINTER_VENDOR_POTTERBOT", "PRINTER_MODEL_9", "NO_TEMPLATES", "EXPERIMENTAL"):
                self.assertIn(keyword, notes)
            # Hop threshold lives on the printer so the Retract filament's lift
            # starts just above this nozzle's first layer.
            expected_lift_above = "0.9" if nozzle == 1 else "1.6"
            self.assertEqual(printer["retract_lift_above"], expected_lift_above)
            self.assertNotIn("retract_length", printer)
            self.assertNotIn("start_gcode", printer)
            for alias in ("Vase Hollow", "Vase Bottom", "Infill"):
                section = f"print:{alias} @Potterbot {nozzle}mm"
                self.assertIn(section, self.ini)
                cond = self.ini[section]["compatible_printers_condition"]
                self.assertIn("PRINTER_VENDOR_POTTERBOT", cond)
                self.assertIn(f"nozzle_diameter[0]=={nozzle}", cond)
                self.assertNotIn("CLAY_TRAVEL", cond)
                self.assertEqual(self.ini[section]["alias"], alias)
            hollow = self.ini[f"print:Vase Hollow @Potterbot {nozzle}mm"]
            bottom = self.ini[f"print:Vase Bottom @Potterbot {nozzle}mm"]
            infill = self.ini[f"print:Infill @Potterbot {nozzle}mm"]
            self.assertEqual(hollow["bottom_solid_layers"], "0")
            self.assertEqual(bottom["bottom_solid_layers"], "3")
            self.assertEqual(hollow.get("spiral_vase") or common["spiral_vase"], "1")
            self.assertEqual(bottom.get("spiral_vase") or common["spiral_vase"], "1")
            self.assertEqual(infill["spiral_vase"], "0")
            expected_layer = str(int(layer)) if layer.is_integer() else f"{layer:g}"
            self.assertEqual(hollow.get("layer_height") or common["layer_height"], expected_layer)
            self.assertEqual(hollow["extrusion_width"], str(nozzle))
            self.assertEqual(
                hollow.get("bridge_flow_ratio") or common["bridge_flow_ratio"],
                bundle.fmt_num(bundle.bridge_flow_ratio_for(nozzle)),
            )
            self.assertGreater(
                float(hollow["extrusion_width"]),
                float(hollow.get("layer_height") or common["layer_height"]),
            )
            if layer < 1.5:
                self.assertEqual(hollow["layer_height"], "0.8")
                self.assertEqual(hollow["first_layer_height"], "0.8")
            else:
                self.assertNotIn("layer_height", hollow)

    def test_official_cura_speeds_and_shell(self) -> None:
        p = self.ini["print:*common*"]
        self.assertEqual(p["perimeter_speed"], "40")
        self.assertEqual(p["travel_speed"], "80")
        self.assertEqual(p["solid_infill_speed"], "20")
        self.assertEqual(p["first_layer_speed"], "40")
        self.assertEqual(p["fill_density"], "0%")
        self.assertEqual(p["fill_pattern"], "line")
        self.assertEqual(p["external_perimeters_first"], "1")
        self.assertEqual(p["bottom_fill_pattern"], "archimedeanchords")
        self.assertEqual(p["top_fill_pattern"], "archimedeanchords")
        self.assertEqual(p["complete_objects"], "1")
        self.assertEqual(p["perimeter_generator"], "arachne")
        self.assertEqual(p["infill_overlap"], "15%")
        self.assertEqual(p["top_solid_layers"], "0")
        self.assertEqual(p["perimeters"], "1")
        self.assertEqual(p["skirts"], "3")
        self.assertEqual(p["skirt_distance"], "8")
        self.assertEqual(p["wipe_tower"], "0")
        self.assertEqual(p["default_acceleration"], "3000")
        self.assertEqual(p["first_layer_acceleration"], "3000")
        self.assertEqual(p["travel_acceleration"], "3000")
        self.assertEqual(p["travel_short_distance_acceleration"], "3000")
        self.assertEqual(p["perimeter_acceleration"], "3000")
        five = self.ini["print:Vase Hollow @Potterbot 5mm"]
        self.assertEqual(five.get("layer_height") or p["layer_height"], "1.5")
        self.assertEqual(five["extrusion_width"], "5")

    def test_infill_profile(self) -> None:
        infill = self.ini["print:Infill @Potterbot 5mm"]
        self.assertEqual(infill["spiral_vase"], "0")
        self.assertEqual(infill["fill_density"], "15%")
        self.assertEqual(infill.get("fill_pattern") or self.ini["print:*common*"]["fill_pattern"], "line")
        self.assertEqual(infill["bottom_solid_layers"], "3")
        self.assertEqual(infill["top_solid_layers"], "3")
        self.assertEqual(infill["avoid_crossing_perimeters"], "1")
        self.assertIn(CLAY_RETRACT, infill["notes"])
        self.assertNotIn("Retract printer", infill["notes"])
        self.assertNotIn("Sequential printing (complete objects) is off", infill["notes"])
        self.assertIn("Sequential printing is on", infill["notes"])

    def test_two_clay_filaments(self) -> None:
        filaments = [s for s in self.ini.sections() if s.startswith("filament:") and s != "filament:*common*"]
        self.assertEqual(filaments, [f"filament:{CLAY}", f"filament:{CLAY_RETRACT}"])
        common = self.ini["filament:*common*"]
        self.assertEqual(common["temperature"], "0")
        self.assertEqual(common["first_layer_temperature"], "0")
        self.assertEqual(common["bed_temperature"], "0")
        self.assertEqual(common["first_layer_bed_temperature"], "0")
        self.assertEqual(common["max_fan_speed"], "0")
        self.assertEqual(common["cooling"], "0")
        self.assertEqual(common["min_fan_speed"], "0")
        clay_common_start = common["start_filament_gcode"]
        self.assertTrue(clay_common_start.startswith('"'), clay_common_start)
        self.assertTrue(clay_common_start.endswith('"'), clay_common_start)
        self.assertEqual(common["filament_diameter"], "1.75")
        self.assertIn("PRINTER_VENDOR_POTTERBOT", common["compatible_printers_condition"])

        clay = self.ini[f"filament:{CLAY}"]
        self.assertEqual(clay["inherits"], "*common*")
        # Unretracted clay is only offered with the spiral-vase print profiles.
        self.assertEqual(clay["compatible_prints_condition"], "spiral_vase==1")
        for key in ("filament_retract_length", "filament_retract_lift"):
            self.assertNotIn(key, clay)
        clay_start = clay.get("start_filament_gcode") or common["start_filament_gcode"]
        self.assertNotIn("G1 Z10", clay_start)

        retract = self.ini[f"filament:{CLAY_RETRACT}"]
        self.assertEqual(retract["inherits"], "*common*")
        self.assertNotIn("compatible_prints_condition", retract)
        self.assertEqual(retract["filament_retract_length"], "80")
        self.assertEqual(retract["filament_retract_lift"], "5")
        self.assertNotEqual(retract["filament_retract_length"], "1000")
        for key in ("filament_retract_speed", "filament_deretract_speed", "filament_retract_lift_above"):
            self.assertNotIn(key, retract)  # printer values (80 mm/s, per-nozzle threshold) apply
        retract_start = retract["start_filament_gcode"]
        self.assertTrue(retract_start.startswith('"'), retract_start)
        self.assertTrue(retract_start.endswith('"'), retract_start)
        retract_start = retract_start.replace("\\n", "\n")
        self.assertIn("G1 Z10 F1000", retract_start)
        self.assertNotIn("G28", retract_start)
        self.assertNotIn("E-", retract_start)
        self.assertNotIn("filament:Clay Potterbot Retract Retract", self.ini)

    def test_vendor_assets(self) -> None:
        for name in ("POTTERBOT9_bed.stl", "POTTERBOT9_texture.svg", "POTTERBOT9_thumbnail.png"):
            self.assertTrue((ASSETS / name).is_file(), name)
        count, (x0, x1), (y0, y1), (z0, z1) = stl_bounds(ASSETS / "POTTERBOT9_bed.stl")
        self.assertGreater(count, 0)
        # 381 mm bat centred on the 381 x 360 bed_shape in X, starting at Y0 (21 mm overhang at the back).
        self.assertAlmostEqual(x0, -190.5, places=2)
        self.assertAlmostEqual(x1, 190.5, places=2)
        self.assertAlmostEqual(y0, -180.0, places=2)
        self.assertAlmostEqual(y1, 201.0, places=2)
        self.assertAlmostEqual(z1, 0.0, places=2)
        self.assertAlmostEqual(z0, -6.35, places=2)
        svg = (ASSETS / "POTTERBOT9_texture.svg").read_text(encoding="utf-8")
        self.assertIn('viewBox="0 0 381 360"', svg)
        self.assertNotIn("<text", svg)  # nanosvg does not render text
        self.assertNotIn("<pattern", svg)
        png = (ASSETS / "POTTERBOT9_thumbnail.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", png[16:24])
        self.assertEqual((width, height), (180, 256))

    def test_post_process_validator(self) -> None:
        post = self.ini["print:*common*"]["post_process"]
        self.assertIn("validate_gcode.py", post)
        self.assertIn("C:\\\\Windows\\\\py.exe -3", post)
        self.assertIn("C:\\\\Repos\\\\Machine-profiles\\\\Potterbot\\\\scripts\\\\", post)


    def test_pause_macro_parks_without_homing(self) -> None:
        pause = (ROOT / "reference" / "firmware" / "macros" / "pause.g").read_text(encoding="utf-8")
        commands = [ln.split(";", 1)[0].strip() for ln in pause.splitlines() if ln.split(";", 1)[0].strip()]
        self.assertFalse(any(cmd.upper().startswith("G28") for cmd in commands), pause)
        self.assertIn("G91", pause)
        self.assertIn("G1 Z10 F1000", pause)
        self.assertIn("G1 X420 Y0 F4800", pause)


if __name__ == "__main__":
    unittest.main()
