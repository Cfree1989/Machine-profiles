# Port review: ideaMaker → PrusaSlicer (bundle 0.5.51)

Review date: 2026-09-17. Reviewed against PrusaSlicer **2.9.6** (installed build) and ideaMaker **5.4.2.8790** sources in `reference/ideamaker/`. This file is the findings list from 0.5.51.

Applied later: **0.5.52** removed dead `wipe_tower_x` / `wipe_tower_y`. **0.5.53** quoted `start_filament_gcode`, wipe 95 %, PLA fan 0/50/100, first-use E11 unretract, idle nozzle stays 180 °C on layer 2. **0.5.54** docs/tests match those values; `validate_gcode.py` rejects non-G-code lines after `M1001`. **0.5.55** sequential skipped `;LAYER:N` + first-layer FLOW on every object; M73 ~30 s preheat; wipe-tower purge stays PrusaSlicer 15 mm³. **0.5.56** Small Features Ø20 mm, tool-change E±11 at 20 mm/s, first bottom-solid accel 5000. **0.5.57** dropped those (no PrusaSlicer setting); keep native Ø13 small perimeters, 40/25 retract, solid accel 2000.

## Scope and method

- Read every file under `Raise3D/`: `profiles/Raise3D-Pro2Plus-HS-0.4-bundle.ini` (identical to `vendor/Raise3D.ini`), `docs/`, `scripts/`, `tests/`, `reference/`.
- Read the four ideaMaker G-code files and all 13 ideaMaker Advanced Settings screenshots (`Standard - Pro2 Plus HS - PLA`).
- Measured the ideaMaker G-code with scripts (per-layer feedrates and accelerations by `;TYPE:`, fan per layer, infill spacing, wipe distances, tool-change sequence, wipe-tower E per layer, preheat lead).
- Sliced test jobs with the PrusaSlicer 2.9.6 CLI from the bundle flattened to flat configs, using a two-object 3MF (20 mm cube on extruder 1, 20 mm cube on extruder 2): dual PLA with wipe tower, dual PETG, sequential (`complete_objects = 1`) with and without tower, and a wipe probe (`retract_before_wipe = 0%`). Compared the output to ideaMaker line by line.
- Existing unit tests: 43 pass.

Overall: the start / end / tool-change **sequences** are a faithful port and are well documented. The problems are a handful of PrusaSlicer settings that do not do what the notes say they do, plus several ideaMaker settings that were not carried over.

## 1. Headline findings (ranked by impact)

### 1.1 `start_filament_gcode` is silently broken (the leading `;` is a vector separator)

Both `[filament:*common*]` and `[filament:PLA Raise3D]` set `start_filament_gcode = ;Filament Name: …\nM221 …`. PrusaSlicer stores `start_filament_gcode` as a per-extruder string vector and splits **unquoted** values on `;`. Config dumps from the exports show the effect:

```
; start_filament_gcode = ;"Filament Name: {\"[Raise3D] \"}…\\nM221 T{filament_extruder_id} S94"   <- CLI/flat: ["", "Filament Name…"]
; start_filament_gcode = ;                                                                       <- GUI export:  ["", ""]
```

- GUI (the real workflow): both extruders get an **empty** string. The filament-name comment and the per-filament `M221` are never emitted.
- CLI / flat config: extruder 1 gets a bare non-G-code line. Wipe-tower path: `Filament Name: [Raise3D] PLA` then `M221 T1 S94`. Sequential path: one line `Filament Name: [Raise3D] PLA\nM221 T1 S94` (literal `\n`), so `M221` never executes there.
- Not fatal today only because `start_gcode` also emits `M221 T0/T1 S94`. `validate_gcode.py` does not flag unknown-command lines and `tests/test_profile_structure.py` (lines ~296–299) only asserts the raw text.
- Fix: quote the value (`"; Filament Name: …"`), as `end_filament_gcode` already is, or remove it because `start_gcode` covers `M221`.

### 1.2 Wipe is disabled, not "wipe after full retract"

`retract_before_wipe = 100%,100%` tells PrusaSlicer to retract everything *before* the wipe, which leaves a wipe length of zero. Every PrusaSlicer export (the checked-in GUI reference and all CLI test slices) contains **0** `;WIPE_START` tags; re-slicing with `retract_before_wipe = 0%` produced 442.

ideaMaker wipes **0.20 mm at 60 mm/s** on outer walls only (1,372 wipes in `LeftonlyExtruder.gcode`, distances 0.2 / 0.138 / 0.06 mm on short walls). PrusaSlicer wipe length ≈ (remaining retract ÷ retract speed) × 0.8 × travel speed, so `retract_before_wipe = 95%` gives ≈ 0.22 mm. PETG (`filament_retract_before_wipe = 20%`) does wipe.

### 1.3 Fan schedule is not ideaMaker's 0 / 50 / 100

ideaMaker (Cooling tab and G-code): layer 1 `M106 S0`, layer 2 `M106 S128`, layer 3+ `M106 S255`, fixed; the only variation is overhang-shell bursts to `S255` on layer 2. PrusaSlicer output: layer 2 at `S229.5` (90 %) on the 20 mm cubes, and 50–100 % varying per layer with layer time in the GUI export (`S186`, `S194`, `S199`, `S209`, `S255`).

Two causes: `full_fan_speed_layer = 2` with `disable_fan_first_layers = 1` produces **no** ramp (PrusaSlicer ramps only while `layer_id + 1 < full_fan_speed_layer`; layer 2 needs `full_fan_speed_layer = 3` to get 50 %), and `min_fan_speed = 50` / `fan_below_layer_time = 100` make the fan layer-time-modulated between 50 and 100 %. `min_fan_speed = max_fan_speed = 100`, `disable_fan_first_layers = 1`, `full_fan_speed_layer = 3` reproduces ideaMaker exactly.

### 1.4 Dual: T1's start-G-code retraction is invisible to PrusaSlicer, so T1's first use is 11 mm under-primed

Dual start (copied from `MulticolorRaise3d.gcode`): `T1 … G1 F200 E10 … G1 F200 E-11.00 … T0 … G1 F200 E10`. ideaMaker re-primes `E11` after **every** `T`; PrusaSlicer only unretracts what it retracted itself (`retract_length_toolchange`). In the exports:

- Wipe tower: tool change #1 (to T1) has **no** `G1 E11`; every later change does (`G1 E11 F1500`). The first purge is only 9.65 mm of E, so it is entirely consumed re-priming and T1's first tower loops start starved.
- Sequential, no tower: object 2's first layer starts ≈ 11 mm (≈ 26 mm³, ≈ 180 mm of 0.48 × 0.3 mm line) in the air.

Fix options: drop the `G1 F200 E-11.00` from the dual start block and let `retract_length_toolchange = 11` own it, or prime 11 mm on the first T1 use.

### 1.5 Dual, non-PLA filaments: the layer-2 temperature transition wakes the idle nozzle

Because the printer is not single-extruder-multi-material and `ooze_prevention = 0`, PrusaSlicer emits `temperature` for **every used extruder** at the layer 1 → 2 transition whenever it differs from `first_layer_temperature`. Dual PETG export, at `;LAYER:1`:

```
1153: M104 S250 T0 ; set temperature   <- T0 had been parked at 180 (line 292)
1154: M104 S250 T1 ; set temperature
```

The idle tool then sits at 250 °C (oozing) until its next tool change resets it to 180. PLA is unaffected (230 / 230). PETG, TPU, PA-CF and ABS-GF are affected.

Related: `toolchange_gcode` uses `M109 T{next_extruder} S{temperature[next_extruder]}`, so on layer 1 PETG is re-targeted from 245 to 250 immediately after the start block heated it to 245. `{if layer_num == 0}{first_layer_temperature[next_extruder]}{else}{temperature[next_extruder]}{endif}` would fix that.

### 1.6 `wipe_tower_x = 50` / `wipe_tower_y = 140` are dead keys in 2.9.6

The wipe-tower position moved from the print profile to the project (3MF) in PrusaSlicer 2.9. The GUI config dump has no `wipe_tower_x` / `wipe_tower_y`; the CLI slice placed the tower at PrusaSlicer's built-in default **X180 Y140** (footprint X177–243, Y135–150). README, `docs/`, `printer_notes` and `tests/test_profile_structure.py` ("default X50 Y140, past T1 keep-out") are not true in this version. T1 keep-out safety rests entirely on the user dragging the tower and on `validate_gcode.py`.

### 1.7 Sequential printing

- With two tools and the profile default `wipe_tower = 1`, `complete_objects = 1` is a hard error: *"The Wipe Tower is currently not supported for multimaterial sequential prints."* The user must turn the tower off first.
- Without the tower it slices. Observed sequence: T0 cube complete → `G1 Z20.1` → travel to object 2 origin → `M107` → `G1 E-9.5 F2400` → `M104 T0 S180` / `M109 T1 S230` / `T1` → bare `Filament Name…` line (1.1) → `G1 E-1.5` → `G1 Z.3` → print. There is no purge; the nozzle swap (electronic lift) happens over the bare bed where object 2 will start; the prime deficit from 1.4 applies.
- Post-processing (`ensure_m99123_first.py`, 0.5.55): synthesizes the skipped `;LAYER:N` on each later object's first layer, and applies 90 % first-layer FLOW whenever Z is still the first-layer height (not only before `;LAYER:1`). The `M104 T1 S230` preheat is inserted on object 1's last layer (~30 s of `M73` remaining time). There is still no purge between objects.
- `extruder_clearance_height = 80` / `extruder_clearance_radius = 90` are operator measurements (see `MACHINE_BEHAVIOR.md`). The CLI did not reject a 40 mm edge gap between the cubes; confirm the collision circles in the GUI before relying on it.

## 2. ideaMaker settings not (fully) carried over

Source: `reference/ideamaker/Settings/*.png` (`Standard - Pro2 Plus HS - PLA`) and the G-code files.

| ideaMaker setting | ideaMaker value (measured in G-code) | Profile | Status |
| --- | --- | --- | --- |
| Slow Down First Few Layers = 3 | walls 50 → 75 → 100 → 125 → 150; solid 50 → 67 → 85 → 102 → 120; tower and gap fill follow the same ramp (layers 1–4) | layer 1 = 50, layer 2+ = full speed | Not portable natively; documented. Could be baked in by scaling `F` on layers 2–4 in post-process. |
| Solid Fill Layers 6 / Top Surface Solid Fill Layers 2 | top of the Compensation cube: 4 × `SOLID-FILL` @ 120 mm/s, then 2 × `TOP-SURFACE` @ 100 mm/s with 106 % flow (layers 144–149) | `top_solid_layers = 4` (0.8 mm); only one layer is `Top solid infill`, so only one layer gets 106 % | **Missed**: 4 vs 6 top layers; 1 vs 2 top-surface layers. Bottom 4 matches. |
| Infill 20 % Grid, overlap 10 %, anchor 0 % | Left / Dual jobs: grid at 4.0 mm spacing = **20 %**; Compensation Test: 5.33 mm = 15 % | `fill_density = 15%`, `fill_pattern = adaptivecubic`, `infill_overlap = 15%`, `infill_anchor = 2` / `infill_anchor_max = 12` | Pattern from neither source; density from the calibration cube, not the production jobs. The checked-in GUI export was still `grid`. |
| Elephant Foot Compensation | **off** (0.00) | `elefant_foot_compensation = 0.20` | Deviation introduced in 0.5.47; notes acknowledge holes open ≈ 0.2. Not from ideaMaker. |
| Layer Start Point: Fixed (0, 0) | seams pulled to the corner nearest the origin | `seam_position = aligned` | Cosmetic; `rear` is the closest fixed-direction analogue. |
| Small Features Ø 20 mm at 50 % | small walls at 75 mm/s | `small_perimeter_speed = 75`. Threshold is fixed at radius 6.5 mm (Ø13) | **Skipped (0.5.57)** — no PrusaSlicer size control. |
| Overhang Shells > 30° at 50 mm/s, fan 100 % | `WALL-OUTER` 50 mm/s segments; `M106 S255` bursts | `enable_dynamic_overhang_speeds` 15 / 25 / 30 / 50 %; `bridge_fan_speed = 100` also covers overhang perimeters | Different slowdown model; fan parity is fine. |
| Enable Bridging Detection | **off** (bridges printed as 120 mm/s infill) | bridges detected: 30 mm/s, 0.9 flow, accel 2000 | Documented deviation; PrusaSlicer always detects bridges. |
| Minimal Travel of Retraction 0.60 mm | travels 0.6–1 mm are mostly retracted | `retract_before_travel = 1` | Minor. |
| Extruder-switch retract / restart 20 mm/s | `G1 F1200 E-11` / `G1 F1200 E11` | 11 mm at 40 mm/s out / 25 mm/s in (`retract_speed` / `deretract_speed`) | **Skipped (0.5.57)** — no separate tool-change speed. |
| Base / Bottom Solid Fill accel 5000; gap fill | `SOLID-FILL` at 5000 on layers 0–3; `GAP-FILL` mostly at 2000 | `solid_infill_acceleration = 2000` for all solid; gap fill uses `default_acceleration` 5000 | **Skipped (0.5.57)** — one solid-infill accel in PrusaSlicer. |
| Cool Down Inactive Extruder → Move to Park Position X30 Y295 | `G0 F9000 X30.000 Y295.000` before all 294 tool changes | not copied (intentional, documented) | Fine for tower prints; see 1.7 for sequential. |
| Wipe Tower: min 20 mm³, 3 loops / extruder, octagon Ø 50 → 25, 150 mm/s, brim 2 | 46 mm E on layer 0, then 28 → 13.7 mm/layer (≈ 33 mm³) at one change per layer | 60 mm rectangle, purge lines 40–55 mm/s (16–23 on layer 1), structure 150 mm/s, `wipe_tower_brim_width = 3`, ≈ 11.7 mm/layer (≈ 28 mm³) | Volumes comparable. Purge = `filament_minimal_purge_on_wipe_tower` 15 mm³ (PrusaSlicer default, not set in the bundle); `multimaterial_purging = 140` is irrelevant for a two-nozzle printer. |
| Dual skirt at 15 mm/s (`F900`) | present in `MulticolorRaise3d.gcode` | `skirts = 0` | Documented. |
| Maximum Volumetric Speed | 0 (none) | `filament_max_volumetric_speed = 15` | Never binds: 150 × 0.4 × 0.2 = 12 mm³/s. |
| Outer Shell Wipe 0.20 mm at 60 mm/s | 1,372 wipes | none in output (1.2) | **Missed.** |
| Fan points 1: 0 %, 2: 50 %, 3: 100 % | fixed | time-modulated (1.3) | **Missed.** |
| Minimal Segment Length 0.012 | — | `gcode_resolution = 0.008` | Fine. |

Settings that **do** match, confirmed in the exported G-code: layer 0.20 / first 0.30; widths 0.40 / 0.48; walls 150, infill / solid 120, top 100, gap 100, first layer 50 mm/s; accel 5000 walls / infill / first, 2000 solid / top, travel 5000; jerk 10 (`SET_VELOCITY_LIMIT` after post-process); retract 1.5 mm at 40 mm/s, unretract 25 mm/s, retract on layer change, Z-hop 0; 230 / 60 °C; `M221 S94` at start and `S100` at end; cooling floor 100 mm/s below 10 s; 2 shells, inner → outer → infill order; `M99123` on line 1, homing order, `M1001` / `M1002`, per-tool shutdown, relative retract and park move; standby 180 °C and `M109` wait at the swap; `is_extruder_used` gating for left-only, right-only and dual; 11 mm tool-change retract; RaiseTouch `;PRINTING_TIME:` / `;REMAINING_TIME:` comments; `validate_gcode.py` passes on all exports.

## 3. Dual-color assessment

Works: tool-change temperatures (`M104 T{prev} S180`, `M109 T{next} S230`), standby, `T` emitted by the slicer, purge volume in the same range as ideaMaker, preheat insertion (145–403 lines ahead, median 228; ideaMaker 64–2,200, median 755 ≈ 30 s — the `ensure_m99123_first.py` docstring says "~285 lines", the measured median is 755), end sequence identical to the ideaMaker dual file.

Needs attention, in order: 1.4 (T1 first-use prime), 1.5 (non-PLA layer-2 wake-up and first-layer temperature), 1.1 (garbage line at each T1 swap in flat configs / silent no-op in the GUI), 1.6 (tower position claim). Preheat lead is time-based in 0.5.55. PrusaSlicer also emits `M107`, `M220 S100` and `G4 S0` around each swap (harmless).

Test artifact worth knowing: in the CLI runs PrusaSlicer crashed (`-1073741819`) after writing the G-code, reporting "gcode path conflicts found between WipeTower and Cube_T1". That happened because the tower defaulted onto the second test cube (see 1.6), not because of the profile.

## 4. Docs and tests accuracy

- `reference/prusaslicer/Raise3DTest_0.4n_0.2mm_PLA_PRO2PLUS_HS_DUAL_3h2m.gcode` was exported from an older profile revision (`fill_pattern = grid`, `elefant_foot_compensation = 0`, `min_print_speed = 15`, empty `start_filament_gcode`) and is a **single-tool** print (no `T1`). There is no real dual GUI export checked in.
- README / `GCODE_MAPPING.md` / `MACHINE_BEHAVIOR.md` (fixed 0.5.52–0.5.54): PLA fan **is** 0 / 50 / 100; wipe-tower position is a project setting (2.9.6 default around X180 Y140), not X50 Y140.
- `idle_temperature = 70` is inert (`ooze_prevention = 0`); harmless but misleading next to "standby 180".
- Tests (fixed 0.5.53–0.5.55) lock `retract_before_wipe = 95%`, `full_fan_speed_layer = 3`, no `wipe_tower_x`, no `filament_minimal_purge_on_wipe_tower`. `validate_gcode.py` rejects non-G-code lines after `M1001` (the broken `start_filament_gcode` dump).

## 5. Suggested changes

1. Quote `start_filament_gcode` in both filament sections, or drop it because `start_gcode` already emits `M221`. **Done (0.5.53).**
2. `retract_before_wipe = 95%,95%` for the ≈ 0.2 mm outer-wall wipe. **Done (0.5.53).**
3. PLA: `min_fan_speed = 100`, `full_fan_speed_layer = 3` (keep `disable_fan_first_layers = 1`, `max_fan_speed = 100`). **Done (0.5.53).**
4. Remove `G1 F200 E-11.00` from the dual start block (or add a first-use 11 mm prime) so PrusaSlicer's retraction accounting matches the physical state. **Done (0.5.53):** kept start `E-11`; post-process emits first-use `G1 E11 F1500` (PrusaSlicer deretract 25 mm/s).
5. `toolchange_gcode`: use `first_layer_temperature` when `layer_num == 0`. Consider `ooze_prevention = 1` with `idle_temperature = 180` so PrusaSlicer owns standby and stops re-heating the idle tool at layer 2 (test that its behaviour on this firmware is acceptable), or strip the layer-2 `M104 … T{idle}` in post-process. **Done (0.5.53):** first-layer wait on layer 0; post-process strips idle `M104 S{print} T{idle}`.
6. `top_solid_layers = 6` / `top_solid_min_thickness = 1.2` to match; optionally `fill_pattern = grid`, `fill_density = 20%`, `infill_overlap = 10%` to match the production jobs. **Skipped** (keep 4 layers / 15% adaptive cubic).
7. Decide on `elefant_foot_compensation` (ideaMaker had none). **Skipped** (keep 0.20).
8. Remove the dead `wipe_tower_x` / `wipe_tower_y` keys and update docs and tests; document that the tower position lives in the project. **Done (0.5.52 / 0.5.54).**
9. For sequential use: document "turn off the wipe tower", synthesize `;LAYER:N` for later first layers, apply first-layer FLOW to every object's layer 0, and verify the clearance circles in the GUI. **Done (0.5.55)** for the G-code gaps and the wipe-tower-off note; clearance circles still need a GUI check.
10. Optional: time-based preheat lead (derived from `M73`) instead of 400 lines; explicit `filament_minimal_purge_on_wipe_tower = 20` to mirror ideaMaker's minimal tower volume. **Preheat done (0.5.55)** (~30 s from `M73`, 400-line fallback). **Purge floor skipped** — keep PrusaSlicer's default 15 mm³ (key not set in the bundle).

## Reproduction

The measurements above came from scratch scripts kept outside the repo (`%TEMP%\r3d_dualtest\` and `%TEMP%\r3d_analyze*.py`): a flattener that turns the bundle into flat printer / print / filament INIs plus a two-cube 3MF with per-object extruder assignment, then `prusa-slicer-console.exe --export-gcode --dont-arrange --load printer.ini --load print.ini --load pla.ini two_cubes.3mf`, and inspection scripts that count `;WIPE_START`, `M106` per layer, `CP TOOLCHANGE` purge E, `G1 E11` after each `T`, and `M104` / `M109` around `;LAYER:1`.
