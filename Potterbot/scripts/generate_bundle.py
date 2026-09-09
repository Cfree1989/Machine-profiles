"""Generate Potterbot vendor + importable PrusaSlicer bundles."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Potterbot.ini"
BUNDLE = ROOT / "profiles" / "Potterbot-9-bundle.ini"
IDX = ROOT / "vendor" / "Potterbot.idx"

CONFIG_VERSION = "0.1.13"
NOZZLES = list(range(1, 11))
BED_X = 381  # 15 in bat; firmware X travel is 420
BED_Y = 360  # firmware Y travel (bat is 381)
BED_Z = 400
LAYER_HEIGHT = 1.5  # official Cura 3D Potter Standard / Fine
PRINT_SPEED = 40
TRAVEL_SPEED = 80
BOTTOM_SPEED = 20
SKIRT_COUNT = 3
SKIRT_GAP = 8
END_RETRACT = 500
# Mid-print retract stays off, matching official Cura 3D Potter Standard.
# After G28 the head is at Z400. A slicer retract+Z-hop there pulls the ram
# for seconds at the top of the column, then hops as if Z were already 1.5 mm.
# Do not use the 3D Potter FAQ 1000 mm @ 1000 mm/s recipe (exceeds M203 E).
# Keep a slow ram speed on the printer so a manual enable in the UI is not 1000.
RETRACT_SPEED = 17
# Cura jobs emit no M204, so Duet uses config.g M201 XY/E 3000. Match that.
ACCEL_XY = 3000

HEADER = """\
# 3D Potterbot 9 - experimental PrusaSlicer vendor bundle
# NOT production-ready. Clay ram extruder, Duet 2 WiFi, RepRapFirmware 2.04RC1.
# Speeds and start/end from official Cura 3D Potter Standard + Cura 5.12 jobs.
# Bed is the 15x15 in bat clipped to Y travel (381 x 360 x 400). Firmware travel is 420 x 360 x 400.
# Do not copy pause.g into the slicer (it homes).

"""


def nln(text: str) -> str:
    return text.replace("\n", "\\n")


def fmt_num(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def start_gcode() -> str:
    return nln(
        "; EXPERIMENTAL PrusaSlicer Potterbot 9 - not production-ready\n"
        "; Start matches official Cura 3D Potter Standard (G28 only; first travel includes Z)\n"
        "T0\n"
        "G21\n"
        "G90\n"
        "M83\n"
        "M107\n"
        "G28 ;Home all"
    )


def end_gcode() -> str:
    return nln(
        "G91\n"
        f"G0 Z10 E-{END_RETRACT} F1000 ;lift and retract clay\n"
        "G90\n"
        "G28 ;Home all"
    )


def layer_for_nozzle(nozzle: int) -> float:
    # Official Fine is 1.5 mm. PrusaSlicer also requires:
    #   first_layer_height <= nozzle_diameter
    #   extrusion_width > layer_height  (equal fails: "too low to be printable")
    # Line width equals the nozzle, so layer must stay strictly below the tip.
    return min(LAYER_HEIGHT, 0.8 * float(nozzle))


def printer_notes(nozzle: int) -> str:
    layer = layer_for_nozzle(nozzle)
    if layer < LAYER_HEIGHT:
        layer_note = (
            f"Layer height is {fmt_num(layer)} mm (below the nozzle so PrusaSlicer will slice; "
            "official 1.5 mm Fine is taller than this tip). "
        )
    else:
        layer_note = "Layer height is the official 1.5 mm Fine value. "
    return (
        "Don't remove the following keywords! These keywords are used in the compatible printer condition of the print and filament profiles.\\n"
        "PRINTER_VENDOR_POTTERBOT\\n"
        "PRINTER_MODEL_9\\n"
        "EXPERIMENTAL\\n"
        f"Not production-ready. 3D Potterbot 9, Duet 2 WiFi, RRF 2.04RC1, {nozzle} mm nozzle. "
        f"Clay is cold (no heaters). {layer_note}"
        "Match line width to the nozzle on the machine. "
        "Bed is the 15x15 in bat (381 mm) clipped to Y 360. After G28 the head is at X420 Y0 Z400."
    )


def vendor_block() -> str:
    lines = [
        HEADER.rstrip(),
        "",
        "[vendor]",
        "repo_id = non-prusa-fff",
        "name = 3D Potter (experimental)",
        f"config_version = {CONFIG_VERSION}",
        "",
        "[printer_model:POTTERBOT9]",
        "name = 3D Potterbot 9 (experimental)",
        "variants = " + ";".join(str(n) for n in NOZZLES),
        "technology = FFF",
        "family = Potterbot",
        "default_materials = Clay Potterbot",
        "",
        "[printer:*common*]",
        "printer_technology = FFF",
        "autoemit_temperature_commands = 0",
        "before_layer_gcode =",
        "between_objects_gcode =",
        "color_change_gcode =",
        'default_filament_profile = "Clay Potterbot"',
        "default_print_profile = Vase Hollow @Potterbot 5mm",
        f"deretract_speed = {RETRACT_SPEED}",
        "extruder_colour = #C4A574",
        "extruder_offset = 0x0",
        "extruder_clearance_height = 40",
        "extruder_clearance_radius = 40",
        "gcode_flavor = reprapfirmware",
        "host_type = duet",
        "layer_gcode =",
        "machine_limits_usage = time_estimate_only",
        "machine_max_acceleration_e = 3000,3000",
        "machine_max_acceleration_extruding = 3000,3000",
        "machine_max_acceleration_retracting = 3000,3000",
        "machine_max_acceleration_travel = 3000,3000",
        "machine_max_acceleration_x = 3000,3000",
        "machine_max_acceleration_y = 3000,3000",
        "machine_max_acceleration_z = 1000,1000",
        "machine_max_feedrate_e = 366.67,366.67",
        "machine_max_feedrate_x = 100,100",
        "machine_max_feedrate_y = 100,100",
        "machine_max_feedrate_z = 16.67,16.67",
        "machine_max_jerk_e = 50,50",
        "machine_max_jerk_x = 50,50",
        "machine_max_jerk_y = 50,50",
        "machine_max_jerk_z = 16.67,16.67",
        "machine_min_extruding_rate = 0,0",
        "machine_min_travel_rate = 0,0",
        "pause_print_gcode = M25",
        "remaining_times = 0",
        "retract_before_travel = 15",
        "retract_before_wipe = 0%",
        "retract_layer_change = 0",
        "retract_length = 0",
        "retract_length_toolchange = 0",
        "retract_lift = 0",
        "retract_lift_above = 0",
        "retract_lift_below = 0",
        "retract_restart_extra = 0",
        "retract_restart_extra_toolchange = 0",
        f"retract_speed = {RETRACT_SPEED}",
        "silent_mode = 0",
        "single_extruder_multi_material = 0",
        "thumbnails =",
        "thumbnails_format = PNG",
        "toolchange_gcode =",
        "use_firmware_retraction = 0",
        "use_relative_e_distances = 1",
        "use_volumetric_e = 0",
        "variable_layer_height = 0",
        "wipe = 0",
        "z_offset = 0",
        f"start_gcode = {start_gcode()}",
        f"end_gcode = {end_gcode()}",
        "",
    ]

    bed = f"0x0,{BED_X}x0,{BED_X}x{BED_Y},0x{BED_Y}"
    for nozzle in NOZZLES:
        name = f"{nozzle}mm Nozzle"
        lines.extend(
            [
                f"[printer:{name}]",
                "inherits = *common*",
                "printer_model = POTTERBOT9",
                f"printer_variant = {nozzle}",
                f"bed_shape = {bed}",
                f"max_print_height = {BED_Z}",
                f"nozzle_diameter = {nozzle}",
                f"max_layer_height = {fmt_num(max(layer_for_nozzle(nozzle), float(nozzle)))}",
                "min_layer_height = 0.2",
                f"default_print_profile = Vase Hollow @Potterbot {nozzle}mm",
                f"printer_notes = {printer_notes(nozzle)}",
                "",
            ]
        )

    post = (
        r'"C:\\Windows\\py.exe -3 C:\\Repos\\Prusa-Slicer-Print-Profiles\\Potterbot\\scripts\\validate_gcode.py"'
    )
    lines.extend(
        [
            "[print:*common*]",
            "avoid_crossing_perimeters = 0",
            "bottom_fill_pattern = archimedeanchords",
            "bottom_solid_min_thickness = 0",
            f"bridge_acceleration = {ACCEL_XY}",
            "bridge_flow_ratio = 1",
            "bridge_speed = 40",
            "brim_separation = 0",
            "brim_width = 0",
            "clip_multipart_objects = 1",
            "compatible_printers_condition = printer_notes=~/.*PRINTER_VENDOR_POTTERBOT.*/ and printer_notes=~/.*PRINTER_MODEL_9.*/",
            "complete_objects = 0",
            "duplicate_distance = 12",
            f"default_acceleration = {ACCEL_XY}",
            "dont_support_bridges = 1",
            "elefant_foot_compensation = 0",
            "enable_dynamic_overhang_speeds = 0",
            "ensure_vertical_shell_thickness = 0",
            f"external_perimeter_acceleration = {ACCEL_XY}",
            f"external_perimeter_speed = {PRINT_SPEED}",
            "external_perimeters_first = 0",
            "extra_perimeters = 0",
            "fill_angle = 45",
            "fill_density = 0%",
            "fill_pattern = grid",
            f"first_layer_acceleration = {ACCEL_XY}",
            "first_layer_acceleration_over_raft = 0",
            f"first_layer_infill_speed = {BOTTOM_SPEED}",
            f"first_layer_speed = {PRINT_SPEED}",
            "first_layer_speed_over_raft = 30",
            "gap_fill_enabled = 0",
            f"gap_fill_speed = {PRINT_SPEED}",
            "gcode_comments = 1",
            "gcode_label_objects = 0",
            "gcode_resolution = 0.1",
            f"infill_acceleration = {ACCEL_XY}",
            "infill_anchor = 0",
            "infill_anchor_max = 0",
            "infill_every_layers = 1",
            "infill_extruder = 1",
            "infill_overlap = 15%",
            f"infill_speed = {PRINT_SPEED}",
            "max_print_speed = 85",
            "max_volumetric_speed = 0",
            "min_skirt_length = 0",
            "notes = EXPERIMENTAL. Clay profiles for Potterbot 9. Layer height 1.5 mm from official 3D Potter Fine except the 1 mm nozzle (0.8 mm so extrusion width stays above layer height). Line width equals the installed nozzle. Bottoms are Archimedean chords; tops are rectilinear; sparse infill is grid. 15% infill overlap so bottoms meet the wall. PrusaSlicer Preview draws flat clay beads as rounder tubes — the dark grid is the viewer, not missing clay. Speeds from official Cura (40 mm/s print, 80 travel, 20 bottom). Print/travel acceleration 3000 mm/s² matches firmware M201 (Cura jobs emit no M204). Mid-print retract and Z-hop are off (official Cura). After G28 the head is at Z400; the first travel must include Z down to the layer. End G-code lifts Z 10 mm and pulls E-500.",
            f"layer_height = {fmt_num(LAYER_HEIGHT)}",
            f"first_layer_height = {fmt_num(LAYER_HEIGHT)}",
            "only_retract_when_crossing_perimeters = 1",
            "ooze_prevention = 0",
            "output_filename_format = {input_filename_base}_{layer_height}mm_{printer_variant}n_{print_time}.gcode",
            "overhangs = 0",
            f"perimeter_acceleration = {ACCEL_XY}",
            "perimeter_extruder = 1",
            "perimeter_generator = arachne",
            f"perimeter_speed = {PRINT_SPEED}",
            "perimeters = 1",
            f"post_process = {post}",
            "raft_layers = 0",
            "resolution = 0",
            "seam_position = nearest",
            "single_extruder_multi_material_priming = 0",
            f"skirts = {SKIRT_COUNT}",
            f"skirt_distance = {SKIRT_GAP}",
            "slice_closing_radius = 0.049",
            f"small_perimeter_speed = {PRINT_SPEED}",
            f"solid_infill_acceleration = {ACCEL_XY}",
            "solid_infill_below_area = 0",
            "solid_infill_every_layers = 0",
            "solid_infill_extruder = 1",
            f"solid_infill_speed = {BOTTOM_SPEED}",
            "spiral_vase = 1",
            "support_material = 0",
            "support_material_auto = 0",
            "thick_bridges = 0",
            "thin_walls = 0",
            "top_fill_pattern = rectilinear",
            f"top_solid_infill_acceleration = {ACCEL_XY}",
            f"top_solid_infill_speed = {BOTTOM_SPEED}",
            "top_solid_layers = 0",
            "top_solid_min_thickness = 0",
            f"travel_acceleration = {ACCEL_XY}",
            f"travel_short_distance_acceleration = {ACCEL_XY}",
            f"travel_speed = {TRAVEL_SPEED}",
            "travel_speed_z = 16",
            "wipe_tower = 0",
            "xy_size_compensation = 0",
            "",
        ]
    )

    for nozzle in NOZZLES:
        w = fmt_num(float(nozzle))
        cond = (
            "printer_notes=~/.*PRINTER_VENDOR_POTTERBOT.*/ and "
            "printer_notes=~/.*PRINTER_MODEL_9.*/ and "
            f"nozzle_diameter[0]=={nozzle}"
        )
        shared = [
            f"compatible_printers_condition = {cond}",
            f"extrusion_width = {w}",
            f"external_perimeter_extrusion_width = {w}",
            f"first_layer_extrusion_width = {w}",
            f"infill_extrusion_width = {w}",
            f"perimeter_extrusion_width = {w}",
            f"solid_infill_extrusion_width = {w}",
            f"top_infill_extrusion_width = {w}",
            f"support_material_extrusion_width = {w}",
        ]
        layer = layer_for_nozzle(nozzle)
        if layer < LAYER_HEIGHT:
            shared.extend(
                [
                    f"layer_height = {fmt_num(layer)}",
                    f"first_layer_height = {fmt_num(layer)}",
                ]
            )
        hollow = f"Vase Hollow @Potterbot {nozzle}mm"
        bottom = f"Vase Bottom @Potterbot {nozzle}mm"
        infill = f"Infill @Potterbot {nozzle}mm"
        lines.extend(
            [
                f"[print:{hollow}]",
                "inherits = *common*",
                "alias = Vase Hollow",
                "bottom_solid_layers = 0",
                *shared,
                "",
                f"[print:{bottom}]",
                "inherits = *common*",
                "alias = Vase Bottom",
                "bottom_solid_layers = 3",
                *shared,
                "",
                f"[print:{infill}]",
                "inherits = *common*",
                "alias = Infill",
                "spiral_vase = 0",
                "fill_density = 15%",
                "fill_pattern = grid",
                "bottom_solid_layers = 3",
                "top_solid_layers = 3",
                "avoid_crossing_perimeters = 1",
                "infill_overlap = 15%",
                "notes = EXPERIMENTAL. Infill / multi-object clay. 15% grid infill, 3 Archimedean-chord bottoms, 3 rectilinear tops. Mid-print retract off like the vase profiles (official Cura). Raise infill % on the plater if you need it. Sequential printing (complete objects) is off so a tall pot cannot hit the nozzle; turn it on only if objects are short and spaced.",
                *shared,
                "",
            ]
        )

    lines.extend(
        [
            "[filament:*common*]",
            "compatible_printers_condition = printer_notes=~/.*PRINTER_VENDOR_POTTERBOT.*/ and printer_notes=~/.*PRINTER_MODEL_9.*/",
            "cooling = 0",
            'end_filament_gcode = "; Filament-specific end gcode"',
            "extrusion_multiplier = 1",
            "filament_cost = 0",
            "filament_density = 1.24",
            "filament_diameter = 1.75",
            "filament_soluble = 0",
            "filament_spool_weight = 0",
            "filament_vendor = 3D Potter",
            "min_print_speed = 10",
            "slowdown_below_layer_time = 5",
            "start_filament_gcode = ; Clay Potterbot",
            "",
            "[filament:Clay Potterbot]",
            "inherits = *common*",
            "bed_temperature = 0",
            "bridge_fan_speed = 0",
            "disable_fan_first_layers = 1",
            "fan_always_on = 0",
            "fan_below_layer_time = 0",
            "filament_colour = #55AAFF",
            "filament_max_volumetric_speed = 0",
            'filament_notes = "EXPERIMENTAL. Official 3D Potter Clay material: 1.75 mm volumetric model, 0 C, no fan. Mid-print retract is off (official Cura). End G-code retracts E-500. Prime clay from Duet macros if the ram is not already charged."',
            "filament_type = FLEX",
            "first_layer_bed_temperature = 0",
            "first_layer_temperature = 0",
            "idle_temperature = 0",
            "full_fan_speed_layer = 0",
            "max_fan_speed = 0",
            "min_fan_speed = 0",
            "temperature = 0",
            "",
        ]
    )
    return "\n".join(lines)


def idx_text() -> str:
    return (
        "min_slic3r_version = 2.9.0\n"
        "0.1.0 Initial experimental Potterbot 9 clay bundle. "
        "Official Cura 3D Potter Standard start/end and 40/80 mm/s speeds. "
        "1-10 mm nozzles. Vase Hollow (0 bottom) and Vase Bottom (3 bottoms). "
        "Bed is the 15x15 in bat clipped to Y travel. Not production-ready.\n"
        "0.1.1 Layer height is the documented 1.5 mm Fine value on every nozzle. "
        "Line width equals the installed nozzle (lab Cura notes). Stopped scaling layer height as 30% of nozzle.\n"
        "0.1.2 Add 1.5mm Infill Retract print profile and Clay Potterbot Retract filament "
        "(80 mm @ 17 mm/s, 5 mm Z-hop). Vase profiles stay unretracted. Not the FAQ 1000 mm/s recipe.\n"
        "0.1.3 Retract and 5 mm Z-hop are printer settings on every profile. "
        "Dropped the separate retract filament. Infill print profile renamed 1.5mm Infill.\n"
        "0.1.4 Drop 1.5 mm from print profile names (layer height is still 1.5 mm). "
        "Bottoms concentric, tops rectilinear, sparse infill grid.\n"
        "0.1.5 Bottom fill pattern is Archimedean chords instead of concentric.\n"
        "0.1.6 Printer presets are named 1mm Nozzle through 10mm Nozzle.\n"
        "0.1.7 Use repo_id non-prusa-fff so the Configuration Wizard can list 3D Potter under Other Vendors.\n"
        "0.1.8 Infill print profile has 3 rectilinear top layers to match the 3 bottoms.\n"
        "0.1.9 Bottoms are concentric again (Archimedean chords gap more as the spiral grows on wide tips). "
        "1 mm nozzle layer height is 1 mm so PrusaSlicer will slice.\n"
        "0.1.10 1 mm nozzle layer is 0.8 mm (width must be greater than height). "
        "Arachne + 15% infill overlap so concentric bottoms do not open up on wide tips.\n"
        "0.1.11 Bottoms are Archimedean chords again. The Preview grid on wide tips is the viewer, not that fill pattern.\n"
        "0.1.12 Mid-print retract and Z-hop off (official Cura). After G28 the head is at Z400; "
        "a slicer E-80 hop was retracting at the top of the column before the first layer.\n"
        f"{CONFIG_VERSION} Print/travel acceleration 3000 mm/s² to match firmware M201 / Cura jobs (no slower M204 P500).\n"
    )


def main() -> None:
    text = vendor_block()
    VENDOR.parent.mkdir(parents=True, exist_ok=True)
    BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    IDX.parent.mkdir(parents=True, exist_ok=True)
    VENDOR.write_text(text, encoding="utf-8", newline="\n")
    BUNDLE.write_text(text, encoding="utf-8", newline="\n")
    IDX.write_text(idx_text(), encoding="utf-8", newline="\n")
    print(f"Wrote {VENDOR}")
    print(f"Wrote {BUNDLE}")
    print(f"Wrote {IDX}")


if __name__ == "__main__":
    main()
