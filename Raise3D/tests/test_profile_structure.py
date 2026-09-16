"""Checks that the vendor bundle has the expected wizard structure and G-code markers."""

from __future__ import annotations

import configparser
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
VENDOR = ROOT / "vendor" / "Raise3D.ini"
IDX = ROOT / "vendor" / "Raise3D.idx"
BUNDLE = ROOT / "profiles" / "Raise3D-Pro2Plus-HS-0.4-bundle.ini"
ASSETS = ROOT / "vendor" / "Raise3D"

import generate_assets as assets  # noqa: E402


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

    def test_vendor_and_model_sections(self) -> None:
        self.assertTrue(VENDOR.is_file())
        self.assertTrue(IDX.is_file())
        self.assertIn("vendor", self.ini)
        self.assertEqual(self.ini["vendor"]["name"], "Raise3D (experimental)")
        self.assertEqual(self.ini["vendor"]["config_version"], "0.5.51")
        self.assertIn("0.5.51 ", IDX.read_text(encoding="utf-8"))
        self.assertNotIn("printer_model:PRO2PLUS_HS", self.ini)
        self.assertIn("printer_model:PRO2PLUS_HS_DUAL", self.ini)
        self.assertNotIn("printer:Raise3D Pro2 Plus Hyper Speed 0.4 Left", self.ini)
        self.assertEqual(VENDOR.read_text(encoding="utf-8"), BUNDLE.read_text(encoding="utf-8"))

    def test_vendor_assets_for_plater_and_wizard(self) -> None:
        model = self.ini["printer_model:PRO2PLUS_HS_DUAL"]
        # PrusaSlicer 2.9.6 only draws the vendor bed when bed_model AND bed_texture both resolve.
        self.assertEqual(model["bed_model"], "PRO2PLUS_HS_DUAL_bed.stl")
        self.assertEqual(model["bed_texture"], "PRO2PLUS_HS_DUAL_texture.svg")
        self.assertEqual(model["thumbnail"], "PRO2PLUS_HS_DUAL_thumbnail.png")
        for name in (model["bed_model"], model["bed_texture"], model["thumbnail"]):
            self.assertTrue((ASSETS / name).is_file(), name)
        count, (x0, x1), (y0, y1), (z0, z1) = stl_bounds(ASSETS / model["bed_model"])
        self.assertGreater(count, 0)
        # 13.375 x 13 in plate centred on 305 x 305, handle hanging off the front.
        self.assertAlmostEqual(x0, -assets.PLATE_X / 2, places=2)
        self.assertAlmostEqual(x1, assets.PLATE_X / 2, places=2)
        self.assertAlmostEqual(y1, assets.PLATE_Y / 2, places=2)
        self.assertAlmostEqual(y0, -assets.PLATE_Y / 2 - max(assets.HANDLE_DEPTH, assets.TAB_DEPTH), places=2)
        self.assertAlmostEqual(z1, 0.0, places=2)
        self.assertAlmostEqual(z0, -assets.PLATE_THICKNESS, places=2)
        svg = (ASSETS / model["bed_texture"]).read_text(encoding="utf-8")
        self.assertIn('viewBox="0 0 305 305"', svg)
        self.assertNotIn("<text", svg)  # nanosvg does not render text
        self.assertNotIn("<pattern", svg)
        self.assertIn('width="25"', svg)  # T1 keep-out band
        png = (ASSETS / model["thumbnail"]).read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", png[16:24])
        self.assertEqual((width, height), (180, 256))

    def test_print_and_filament_are_tied_to_dual_printer(self) -> None:
        filament = self.ini["filament:PLA Raise3D"]
        printp = self.ini["print:0.20mm Hyper Speed @Raise3D Pro2 Plus HS"]
        cond_f = filament.get("compatible_printers_condition") or self.ini["filament:*common*"][
            "compatible_printers_condition"
        ]
        cond_p = printp.get("compatible_printers_condition") or self.ini["print:*common*"][
            "compatible_printers_condition"
        ]
        self.assertIn("PRINTER_MODEL_PRO2PLUS_HS", cond_f)
        self.assertIn("PRINTER_VARIANT_DUAL", cond_f)
        self.assertIn("PRINTER_VARIANT_DUAL", cond_p)
        self.assertNotIn("PRINTER_VARIANT_LEFT", cond_p)
        self.assertIn(';Filament Name: {"[Raise3D] "}{filament_type[filament_extruder_id]}', self.ini["filament:*common*"]["start_filament_gcode"])
        start = self.ini["printer:Raise3D Pro2 Plus Hyper Speed 0.4 Dual"]["start_gcode"]
        self.assertIn(';Filament Name #1: {"[Raise3D] "}{filament_type[0]}', start)
        self.assertIn(';Filament Name #2: {"[Raise3D] "}{filament_type[1]}', start)
        self.assertNotIn(";Filament Name #1: PLA\n", start)
        self.assertNotIn('{"[Raise3D] PLA"}', start)
        self.assertIn("filament_extruder_id", self.ini["filament:*common*"]["start_filament_gcode"])
        self.assertNotIn("SET_PRESSURE_ADVANCE", self.ini["filament:*common*"]["start_filament_gcode"])
        self.assertEqual(filament["temperature"], "230")
        self.assertEqual(filament["first_layer_temperature"], "230")
        self.assertEqual(filament.get("extrusion_multiplier") or self.ini["filament:*common*"]["extrusion_multiplier"], "1")
        self.assertEqual(filament["first_layer_bed_temperature"], "60")
        self.assertEqual(filament["idle_temperature"], "70")

    def test_dual_printer_preset(self) -> None:
        section = "printer:Raise3D Pro2 Plus Hyper Speed 0.4 Dual"
        self.assertIn(section, self.ini)
        p = self.ini[section]
        self.assertEqual(p["nozzle_diameter"], "0.4,0.4")
        self.assertEqual(p["extruder_offset"], "0x0,0x0")
        self.assertIn("PRINTER_VARIANT_DUAL", p["printer_notes"])
        # Templates.ini checks printer_notes!~/.*NO_TEMPLATES.*/; keeps Generic PLA etc. out of the filament list.
        self.assertIn("\\nNO_TEMPLATES\\n", p["printer_notes"])
        start = p["start_gcode"]
        self.assertIn(";Firmware: Klipper", start)
        self.assertIn('{if filament_type[0]=="PLA"}M221 T0 S94', start)
        self.assertIn('{if filament_type[1]=="PLA"}M221 T1 S94', start)
        self.assertIn("M221 T0 S{extrusion_multiplier[0]*100}", start)
        self.assertNotIn("{max_layer_z}", start)
        self.assertNotIn(";Bounding Box:", start)
        self.assertNotIn("HEIGHT:{", start)
        self.assertIn("is_extruder_used[0]", start)
        self.assertIn("is_extruder_used[1]", start)
        self.assertIn("M104 T1", start)
        self.assertIn("M109 T1", start)
        self.assertIn("T1", start)
        self.assertIn("G1 F200 E10", start)
        self.assertIn("G1 F200 E-11.00", start)
        self.assertIn("G1 X80 Y0 F140 E1", start)
        self.assertNotIn("G1 X80 Y0 F9000", start)
        self.assertNotIn("G1 X20 Y0", start)
        self.assertNotIn("G1 X40 Y0", start)
        self.assertIn("{if is_extruder_used[0]}T0\n{else}T1\n{endif}", start.replace("\\n", "\n"))
        self.assertIn(
            "{else}\nT1\nG92 E0\nG1 F140 E29\nG1 X80 Y0 F140 E1\nG92 E0",
            start.replace("\\n", "\n"),
        )
        self.assertNotIn("G1 F200 E-11.00\nG92 E0\n{endif}", start)
        self.assertIn("M104 T1 S180", start)
        self.assertIn("M83", start)
        self.assertNotIn("M82", start)
        self.assertIn("G28 X0 Y0", start)
        self.assertIn("G28 Z0", start)
        self.assertIn("M1001", start)
        self.assertNotIn("G29", start)
        self.assertNotIn("M92", start)
        self.assertNotIn("M218", start)
        self.assertNotIn(";Extruder Offset #2", start)
        self.assertEqual(p["retract_length_toolchange"], "11,11")
        self.assertEqual(p["deretract_speed"], "25,25")
        self.assertEqual(p["retract_before_wipe"], "100%,100%")
        self.assertEqual(p["wipe"], "1,1")
        self.assertNotIn("M116", p["toolchange_gcode"])
        self.assertNotIn("temperature[previous_extruder]", p["toolchange_gcode"])
        self.assertNotIn("X30.000 Y295.000", p["toolchange_gcode"])
        self.assertNotIn("X96", p["toolchange_gcode"])
        self.assertIn("M104 T0 S180", p["toolchange_gcode"])
        self.assertIn("{if previous_extruder == 0}", p["toolchange_gcode"])
        self.assertIn("M109 T{next_extruder}", p["toolchange_gcode"])
        self.assertIn("ensure_m99123_first.py", p["toolchange_gcode"])
        self.assertIn("M104 T1 S0", p["end_gcode"])
        self.assertIn("M1002", p["end_gcode"])
        self.assertIn("is_extruder_used[0]", p["end_gcode"])
        self.assertIn("is_extruder_used[1]", p["end_gcode"])
        self.assertIn("M104 S0", p["end_gcode"])
        printp = self.ini["print:0.20mm Hyper Speed @Raise3D Pro2 Plus HS"]
        cond = printp.get("compatible_printers_condition") or self.ini["print:*common*"][
            "compatible_printers_condition"
        ]
        self.assertIn("PRINTER_VARIANT_DUAL", cond)
        self.assertEqual(printp.get("wipe_tower") or self.ini["print:*common*"]["wipe_tower"], "1")

    def test_print_matches_ideamaker_hyper_speed(self) -> None:
        p = self.ini["print:*common*"]
        named = self.ini["print:0.20mm Hyper Speed @Raise3D Pro2 Plus HS"]
        self.assertEqual(named.get("inherits"), "*common*")
        self.assertEqual(named.get("alias"), "0.20mm Hyper Speed")
        self.assertEqual(p["perimeters"], "2")
        self.assertEqual(p["skirts"], "0")
        self.assertEqual(p["fill_pattern"], "adaptivecubic")
        self.assertEqual(p["layer_height"], "0.2")
        self.assertEqual(p["first_layer_height"], "0.3")
        self.assertEqual(p["first_layer_speed"], "50")
        self.assertEqual(p["first_layer_infill_speed"], "50")
        self.assertEqual(p["first_layer_extrusion_width"], "0.48")
        self.assertEqual(p["extrusion_width"], "0.4")
        self.assertEqual(p["perimeter_extrusion_width"], "0.4")
        self.assertEqual(p["external_perimeter_extrusion_width"], "0.4")
        self.assertEqual(p["infill_extrusion_width"], "0.4")
        self.assertEqual(p["solid_infill_extrusion_width"], "0.4")
        self.assertEqual(p["top_infill_extrusion_width"], "0.4")
        self.assertEqual(p["bottom_solid_layers"], "4")
        self.assertEqual(p["top_solid_layers"], "4")
        self.assertEqual(p["perimeter_generator"], "arachne")
        self.assertEqual(p["max_print_speed"], "150")
        self.assertEqual(p["perimeter_speed"], "150")
        self.assertEqual(p["external_perimeter_speed"], "150")
        self.assertEqual(p["small_perimeter_speed"], "75")
        self.assertEqual(p["overhang_speed_3"], "50%")
        self.assertEqual(p["infill_speed"], "120")
        self.assertEqual(p["solid_infill_speed"], "120")
        self.assertEqual(p["support_material_speed"], "120")
        self.assertEqual(p["top_solid_infill_speed"], "100")
        self.assertEqual(p["gap_fill_speed"], "100")
        self.assertEqual(p["bridge_speed"], "30")
        self.assertEqual(p["bridge_flow_ratio"], "0.9")
        self.assertEqual(p["travel_speed"], "150")
        self.assertEqual(p["travel_speed_z"], "5")
        self.assertEqual(p["default_acceleration"], "5000")
        self.assertEqual(p["travel_acceleration"], "5000")
        self.assertEqual(p["travel_short_distance_acceleration"], "5000")
        self.assertEqual(p["first_layer_acceleration"], "5000")
        self.assertEqual(p["first_layer_speed_over_raft"], "30")
        self.assertEqual(p["bridge_acceleration"], "2000")
        self.assertEqual(p["perimeter_acceleration"], "5000")
        self.assertEqual(p["external_perimeter_acceleration"], "5000")
        self.assertEqual(p["infill_acceleration"], "5000")
        self.assertEqual(p["solid_infill_acceleration"], "2000")
        self.assertEqual(p["top_solid_infill_acceleration"], "2000")
        self.assertEqual(p["elefant_foot_compensation"], "0.20")
        self.assertLess(int(p["first_layer_speed"]), int(p["perimeter_speed"]))
        self.assertLess(int(p["first_layer_infill_speed"]), int(p["infill_speed"]))
        self.assertEqual(p["wipe_tower"], "1")
        self.assertEqual(p["wipe_tower_cone_angle"], "25")
        self.assertEqual(p["wipe_tower_brim_width"], "3")
        self.assertEqual(p["wipe_tower_bridging"], "8")
        self.assertEqual(p["wipe_tower_extra_spacing"], "150")
        self.assertEqual(p["wipe_tower_x"], "50")
        self.assertEqual(p["wipe_tower_y"], "140")
        self.assertEqual(p["single_extruder_multi_material_priming"], "0")
        self.assertEqual(p["duplicate_distance"], "6")
        self.assertEqual(p["support_material_extruder"], "0")
        self.assertEqual(p["support_material_interface_extruder"], "0")
        self.assertNotIn("wipe_tower_rotation_angle", p)
        self.assertEqual(self.ini["printer_model:PRO2PLUS_HS_DUAL"]["bed_texture"], "PRO2PLUS_HS_DUAL_texture.svg")
        self.assertTrue((ROOT / "vendor" / "Raise3D" / "PRO2PLUS_HS_DUAL_texture.svg").is_file())
        filament = self.ini["filament:PLA Raise3D"]
        self.assertEqual(filament["filament_max_volumetric_speed"], "15")

    def test_xl_style_print_family_removed(self) -> None:
        removed = [
            "print:0.10mm FAST DETAIL @Raise3D Pro2 Plus HS",
            "print:0.15mm SPEED @Raise3D Pro2 Plus HS",
            "print:0.15mm STRUCTURAL @Raise3D Pro2 Plus HS",
            "print:0.20mm SPEED @Raise3D Pro2 Plus HS",
            "print:0.20mm STRUCTURAL @Raise3D Pro2 Plus HS",
            "print:0.25mm SPEED @Raise3D Pro2 Plus HS",
            "print:0.25mm STRUCTURAL @Raise3D Pro2 Plus HS",
            "print:0.28mm DRAFT @Raise3D Pro2 Plus HS",
        ]
        for section in removed:
            self.assertNotIn(section, self.ini)
        print_sections = [s for s in self.ini.sections() if s.startswith("print:") and s != "print:*common*"]
        self.assertEqual(print_sections, ["print:0.20mm Hyper Speed @Raise3D Pro2 Plus HS"])

    def test_wizard_filaments_are_raise3d_named_and_xl_temps(self) -> None:
        names = [
            "PLA Raise3D",
            "PETG Raise3D",
            "TPU Raise3D",
            "ASA Raise3D",
            "PA-CF Raise3D",
            "ABS-GF Raise3D",
        ]
        for name in names:
            section = f"filament:{name}"
            self.assertIn(section, self.ini)
            self.assertNotIn("alias", self.ini[section])
        self.assertNotIn("filament:Generic PLA @Raise3D Pro2 Plus HS", self.ini)
        self.assertEqual(
            self.ini["printer_model:PRO2PLUS_HS_DUAL"]["default_materials"],
            ";".join(names),
        )
        pla = self.ini["filament:PLA Raise3D"]
        self.assertEqual(pla["first_layer_temperature"], "230")
        self.assertEqual(pla["temperature"], "230")
        self.assertEqual(pla["first_layer_bed_temperature"], "60")
        self.assertEqual(pla["extrusion_multiplier"], "1")
        self.assertEqual(pla["full_fan_speed_layer"], "2")
        self.assertEqual(pla["min_fan_speed"], "50")
        self.assertEqual(pla["max_fan_speed"], "100")
        self.assertEqual(pla["min_print_speed"], "100")
        self.assertEqual(self.ini["filament:*common*"]["min_print_speed"], "15")
        self.assertEqual(pla["filament_max_volumetric_speed"], "15")
        pla_start = pla.get("start_filament_gcode") or self.ini["filament:*common*"]["start_filament_gcode"]
        self.assertNotIn("SET_PRESSURE_ADVANCE", pla_start)
        self.assertIn("M221 T{filament_extruder_id} S94", pla_start)
        petg_start = self.ini["filament:PETG Raise3D"].get("start_filament_gcode") or self.ini["filament:*common*"]["start_filament_gcode"]
        self.assertNotIn("SET_PRESSURE_ADVANCE", petg_start)
        self.assertEqual(self.ini["filament:*common*"]["filament_cost"], "100")
        self.assertEqual(self.ini["filament:*common*"]["filament_spool_weight"], "135")
        petg = self.ini["filament:PETG Raise3D"]
        self.assertEqual(petg["filament_type"], "PETG")
        self.assertEqual(petg["first_layer_temperature"], "245")
        self.assertEqual(petg["temperature"], "250")
        self.assertEqual(petg["bed_temperature"], "80")
        self.assertEqual(petg["min_fan_speed"], "30")
        self.assertEqual(petg["full_fan_speed_layer"], "5")
        self.assertEqual(petg["filament_retract_length"], "0.8")
        self.assertEqual(petg["filament_retract_lift"], "0.15")
        self.assertEqual(petg["filament_cost"], "100")
        self.assertEqual(petg["filament_spool_weight"], "245")
        tpu = self.ini["filament:TPU Raise3D"]
        self.assertEqual(tpu["filament_type"], "TPU")
        self.assertEqual(tpu["first_layer_temperature"], "215")
        self.assertEqual(tpu["temperature"], "230")
        self.assertEqual(tpu["extrusion_multiplier"], "1.08")
        self.assertEqual(tpu["filament_density"], "1.22")
        self.assertEqual(tpu["filament_max_volumetric_speed"], "2.5")
        self.assertEqual(tpu["max_fan_speed"], "30")
        self.assertEqual(tpu["min_fan_speed"], "30")
        self.assertEqual(tpu["disable_fan_first_layers"], "3")
        self.assertEqual(tpu["filament_retract_length"], "2.5")
        self.assertEqual(tpu["filament_retract_speed"], "40")
        self.assertEqual(tpu["first_layer_bed_temperature"], "50")
        self.assertEqual(tpu["filament_cost"], "100")
        self.assertEqual(tpu["filament_spool_weight"], "245")
        asa = self.ini["filament:ASA Raise3D"]
        self.assertEqual(asa["first_layer_temperature"], "265")
        self.assertEqual(asa["temperature"], "265")
        self.assertEqual(asa["first_layer_bed_temperature"], "100")
        self.assertEqual(asa["bed_temperature"], "105")
        self.assertEqual(asa["fan_always_on"], "1")
        self.assertEqual(asa["max_fan_speed"], "20")
        self.assertEqual(asa["min_fan_speed"], "20")
        self.assertEqual(asa["disable_fan_first_layers"], "4")
        self.assertEqual(asa["filament_cost"], "100")
        self.assertEqual(asa["filament_spool_weight"], "135")
        pa = self.ini["filament:PA-CF Raise3D"]
        self.assertEqual(pa["filament_type"], "PA")
        self.assertEqual(pa["first_layer_temperature"], "280")
        self.assertEqual(pa["temperature"], "290")
        self.assertEqual(pa["extrusion_multiplier"], "0.97")
        self.assertEqual(pa["filament_max_volumetric_speed"], "8")
        self.assertEqual(pa["disable_fan_first_layers"], "5")
        self.assertEqual(pa["max_fan_speed"], "15")
        self.assertEqual(pa["min_fan_speed"], "10")
        self.assertEqual(pa["filament_abrasive"], "1")
        self.assertEqual(pa["filament_cost"], "250")
        self.assertEqual(pa["filament_spool_weight"], "250")
        abs_gf = self.ini["filament:ABS-GF Raise3D"]
        self.assertEqual(abs_gf["filament_type"], "ABS")
        self.assertEqual(abs_gf["first_layer_temperature"], "265")
        self.assertEqual(abs_gf["temperature"], "270")
        self.assertEqual(abs_gf["first_layer_bed_temperature"], "105")
        self.assertEqual(abs_gf["max_fan_speed"], "15")
        self.assertEqual(abs_gf["min_fan_speed"], "15")
        self.assertEqual(abs_gf["disable_fan_first_layers"], "4")
        self.assertEqual(abs_gf["bridge_fan_speed"], "25")
        self.assertEqual(abs_gf["filament_cost"], "26.99")
        self.assertEqual(abs_gf["filament_spool_weight"], "230")

    def test_klipper_flavor_and_relative_e(self) -> None:
        common = self.ini["printer:*common*"]
        self.assertEqual(common["gcode_flavor"], "klipper")
        self.assertEqual(common["use_relative_e_distances"], "1")
        self.assertEqual(common["remaining_times"], "1")
        self.assertEqual(common["cooling_tube_length"], "0")
        self.assertEqual(common["cooling_tube_retraction"], "0")
        self.assertIn("G92 E0", common["before_layer_gcode"])
        self.assertNotIn(";HEIGHT:{layer_height}", common["before_layer_gcode"])
        self.assertNotIn("HEIGHT:{", common["before_layer_gcode"])
        self.assertNotIn(";HEIGHT:", common["before_layer_gcode"])
        self.assertNotIn("HEIGHT:{", common.get("after_layer_gcode", ""))
        self.assertNotIn("HEIGHT:{", common.get("start_gcode", ""))
        self.assertEqual(common["autoemit_temperature_commands"], "0")
        self.assertEqual(common.get("thumbnails", ""), "")

    def test_print_post_process_runs_hyper_speed_scripts(self) -> None:
        post = self.ini["print:*common*"]["post_process"]
        self.assertIn("ensure_m99123_first.py", post)
        self.assertIn("validate_gcode.py", post)
        self.assertIn("C:\\\\Windows\\\\py.exe -3", post)
        self.assertNotIn("Python313", post)
        self.assertNotIn("Python314", post)
        self.assertIn("C:\\\\Repos\\\\Prusa-Slicer-Print-Profiles\\\\Raise3D\\\\scripts\\\\", post)
        ensure_at = post.find("ensure_m99123_first.py")
        validate_at = post.find("validate_gcode.py")
        self.assertLess(ensure_at, validate_at)


if __name__ == "__main__":
    unittest.main()
