"""Checks the Potterbot vendor bundle structure."""

from __future__ import annotations

import configparser
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Potterbot.ini"
IDX = ROOT / "vendor" / "Potterbot.idx"
BUNDLE = ROOT / "profiles" / "Potterbot-9-bundle.ini"


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

    def test_vendor_and_model(self) -> None:
        self.assertEqual(self.ini["vendor"]["name"], "3D Potter (experimental)")
        self.assertEqual(self.ini["vendor"]["repo_id"], "non-prusa-fff")
        self.assertEqual(self.ini["vendor"]["config_version"], "0.1.13")
        self.assertEqual(self.ini["printer_model:POTTERBOT9"]["variants"], "1;2;3;4;5;6;7;8;9;10")
        self.assertEqual(self.ini["printer_model:POTTERBOT9"]["default_materials"], "Clay Potterbot")

    def test_printer_common_is_cold_rrf(self) -> None:
        common = self.ini["printer:*common*"]
        self.assertEqual(common["gcode_flavor"], "reprapfirmware")
        self.assertEqual(common["host_type"], "duet")
        self.assertEqual(common["autoemit_temperature_commands"], "0")
        self.assertEqual(common["use_relative_e_distances"], "1")
        self.assertEqual(common["retract_length"], "0")
        self.assertEqual(common["retract_lift"], "0")
        self.assertEqual(common["retract_layer_change"], "0")
        self.assertEqual(common["retract_speed"], "17")
        self.assertEqual(common["pause_print_gcode"], "M25")
        start = common["start_gcode"].replace("\\n", "\n")
        end = common["end_gcode"].replace("\\n", "\n")
        self.assertIn("G28 ;Home all", start)
        self.assertNotIn("M104", start)
        self.assertNotIn("M109", start)
        self.assertIn("G0 Z10 E-500 F1000", end)
        self.assertIn("G28 ;Home all", end)

    def test_bed_is_bat_clipped_to_y_travel(self) -> None:
        p = self.ini["printer:5mm Nozzle"]
        self.assertEqual(p["bed_shape"], "0x0,381x0,381x360,0x360")
        self.assertEqual(p["max_print_height"], "400")
        self.assertEqual(p["nozzle_diameter"], "5")

    def test_ten_nozzle_variants_and_two_vase_modes(self) -> None:
        common = self.ini["print:*common*"]
        self.assertEqual(common["layer_height"], "1.5")
        self.assertEqual(common["first_layer_height"], "1.5")
        for nozzle in range(1, 11):
            self.assertIn(f"printer:{nozzle}mm Nozzle", self.ini)
            printer = self.ini[f"printer:{nozzle}mm Nozzle"]
            layer = min(1.5, 0.8 * float(nozzle))
            self.assertGreaterEqual(float(printer["max_layer_height"]), layer)
            self.assertLess(layer, float(printer["nozzle_diameter"]))
            self.assertIn(f"print:Vase Hollow @Potterbot {nozzle}mm", self.ini)
            self.assertIn(f"print:Vase Bottom @Potterbot {nozzle}mm", self.ini)
            self.assertIn(f"print:Infill @Potterbot {nozzle}mm", self.ini)
            hollow = self.ini[f"print:Vase Hollow @Potterbot {nozzle}mm"]
            bottom = self.ini[f"print:Vase Bottom @Potterbot {nozzle}mm"]
            self.assertEqual(hollow["bottom_solid_layers"], "0")
            self.assertEqual(bottom["bottom_solid_layers"], "3")
            self.assertEqual(hollow.get("spiral_vase") or common["spiral_vase"], "1")
            expected_layer = str(int(layer)) if layer.is_integer() else f"{layer:g}"
            self.assertEqual(hollow.get("layer_height") or common["layer_height"], expected_layer)
            self.assertEqual(hollow["extrusion_width"], str(nozzle))
            self.assertGreater(
                float(hollow["extrusion_width"]),
                float(hollow.get("layer_height") or common["layer_height"]),
            )
            if layer < 1.5:
                self.assertEqual(hollow["layer_height"], "0.8")
                self.assertEqual(hollow["first_layer_height"], "0.8")
            else:
                self.assertNotIn("layer_height", hollow)
            self.assertIn(f"nozzle_diameter[0]=={nozzle}", hollow["compatible_printers_condition"])

    def test_official_cura_speeds_and_shell(self) -> None:
        p = self.ini["print:*common*"]
        self.assertEqual(p["perimeter_speed"], "40")
        self.assertEqual(p["travel_speed"], "80")
        self.assertEqual(p["solid_infill_speed"], "20")
        self.assertEqual(p["first_layer_speed"], "40")
        self.assertEqual(p["fill_density"], "0%")
        self.assertEqual(p["fill_pattern"], "grid")
        self.assertEqual(p["bottom_fill_pattern"], "archimedeanchords")
        self.assertEqual(p["top_fill_pattern"], "rectilinear")
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

    def test_mid_print_retract_off_like_cura(self) -> None:
        infill = self.ini["print:Infill @Potterbot 5mm"]
        self.assertEqual(infill["spiral_vase"], "0")
        self.assertEqual(infill["fill_density"], "15%")
        self.assertEqual(infill.get("fill_pattern") or self.ini["print:*common*"]["fill_pattern"], "grid")
        self.assertEqual(infill["bottom_solid_layers"], "3")
        self.assertEqual(infill["top_solid_layers"], "3")
        self.assertEqual(infill["avoid_crossing_perimeters"], "1")
        printer = self.ini["printer:*common*"]
        self.assertEqual(printer["retract_length"], "0")
        self.assertEqual(printer["retract_lift"], "0")
        self.assertEqual(printer["retract_layer_change"], "0")
        self.assertEqual(printer["retract_restart_extra"], "0")
        self.assertEqual(printer["retract_speed"], "17")
        self.assertEqual(printer["deretract_speed"], "17")
        self.assertLess(float(printer["retract_speed"]), 85)
        self.assertNotEqual(printer["retract_speed"], "1000")
        self.assertNotEqual(printer["retract_length"], "1000")
        self.assertNotIn("filament:Clay Potterbot Retract", self.ini)
        start = printer["start_gcode"].replace("\\n", "\n")
        self.assertNotIn("E-80", start)
        self.assertIn("G28 ;Home all", start)

    def test_clay_filament_is_cold(self) -> None:
        f = self.ini["filament:Clay Potterbot"]
        self.assertEqual(f["temperature"], "0")
        self.assertEqual(f["first_layer_temperature"], "0")
        self.assertEqual(f["bed_temperature"], "0")
        self.assertEqual(f["max_fan_speed"] if "max_fan_speed" in f else self.ini["filament:*common*"].get("max_fan_speed", "0"), "0")
        diameter = f.get("filament_diameter") or self.ini["filament:*common*"]["filament_diameter"]
        self.assertEqual(diameter, "1.75")

    def test_post_process_validator(self) -> None:
        post = self.ini["print:*common*"]["post_process"]
        self.assertIn("validate_gcode.py", post)
        self.assertIn("C:\\\\Windows\\\\py.exe -3", post)
        self.assertIn("C:\\\\Repos\\\\Prusa-Slicer-Print-Profiles\\\\Potterbot\\\\scripts\\\\", post)


if __name__ == "__main__":
    unittest.main()
