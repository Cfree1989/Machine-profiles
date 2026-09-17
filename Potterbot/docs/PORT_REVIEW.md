# Port review: Cura → PrusaSlicer (bundle 0.1.18)

Review date: 2026-09-17. Reviewed against PrusaSlicer **2.9.6** (installed build), the Cura **5.12.0** jobs and the Cura **4.3.0** project in `reference/cura/`, and the live `reference/firmware/config.g` (RRF 2.04RC1). This file is the findings list for 0.1.18; nothing in the bundle was changed by the review.

## Scope and method

- Read every file under `Potterbot/`: `vendor/Potterbot.ini` (identical to `profiles/Potterbot-9-bundle.ini`), `vendor/Potterbot.idx`, `README.md`, `docs/`, `scripts/`, `tests/`, `reference/` (firmware macros, Duet macros, the four Cura screenshots, the 3mf containers).
- Measured the three Cura G-code files with scripts: feedrate per `;TYPE:`, E per mm (cross-section), first and last moves, per-layer Z behaviour, skirt geometry, and the `;SETTING_3` profile dump embedded at the end of each file. Unzipped the 3mf and read every container.
- Sliced 13 jobs with the PrusaSlicer 2.9.6 CLI from the bundle flattened to flat printer / print / filament INIs: Vase Hollow, Vase Bottom and Infill on the 5 mm printer with both clays (and with a **quoted** copy of the Retract filament's start G-code), Vase Hollow on the 1 mm and 9 mm printers, a Ø30 mm neck, and one STL containing two separate cylinders. Models: a Ø120→140 × 45 mm cup, a 90 × 70 × 12 mm box, a Ø40 × 16 mm cup for the 1 mm tip. Ran `validate_gcode.py` on every export.
- Existing unit tests: 14 pass.

Overall: the machine dialect (RRF, relative E, cold, `G28` start, `G0 Z10 E-500 F1000` end), the 40 / 80 / 20 mm/s speeds, the 3000 mm/s² acceleration, the skirt (3 loops, 8 mm gap, confirmed at 70.5 / 75.5 / 80.5 mm from the centre of a Ø120 base), the bed clip and the 1 mm-tip layer rule are all correct and match the Cura output. The problems are one broken filament setting that undoes the entire 0.1.14–0.1.17 retract story, a flow-model difference nobody has quantified, and several PrusaSlicer behaviours (internal bridges, spiral start, floor pattern, island handling) that the docs do not describe.

## 1. Headline findings (ranked by impact)

### 1.1 The Retract filament's `G1 Z10` drop is never emitted (unquoted `;` in `start_filament_gcode`)

Both filaments set `start_filament_gcode = ; Clay Potterbot…` **unquoted**. PrusaSlicer stores this key as a per-extruder string vector and splits unquoted values on `;`. The config dump in the export shows what it parsed:

```
; start_filament_gcode = ;"Clay Potterbot Retract\\nG1 Z10 F1000 ";"drop from Z400 before slicer retract"
```

Three elements: `""`, `Clay Potterbot Retract\nG1 Z10 F1000 ` (with a literal `\n`, not a newline) and `drop from Z400…`. The single extruder uses element 0, which is empty. Same mechanism as Raise3D finding 1.1, but here the lost text is a motion command. Actual start of `Vase Hollow + Clay Potterbot Retract` (5 mm) as shipped:

```
G28 ;Home all
G21 / G90 / M83 / M107          <- PrusaSlicer preamble
G1 E-80 F4800 ; retract         <- head is at X420 Y0 Z400
G1 Z1.5 F960 ; lift             <- 398.5 mm plunge beside the bat, ~25 s
G1 X134.005 Y123.494 F4800      <- travel onto the bat at Z1.5
G1 Z1.5 F960
G1 E80 F4800 ; unretract
```

That is the 0.1.11 failure ("retract at the top of the column") that `.idx` 0.1.14–0.1.17 say was fixed. With the value quoted (`"; Clay Potterbot Retract\nG1 Z10 F1000 ;drop…"`) the export becomes `G28` → preamble → `G1 Z10 F1000` → `M107` → `G1 E-80` at Z10 → `G1 Z1.5` → travel → unretract, which is what the docs describe. The `Clay Potterbot` comment is lost the same way (harmless). `validate_gcode.py` **passes** the broken export (see 4); `tests/test_profile_structure.py` only asserts the raw text contains `G1 Z10 F1000`. Only the unretracted path has ever run on the machine (`CURA_VS_PRUSA.md`: "already ran a post-0.1.12 Prusa slice successfully (retract off)").

### 1.2 Even when fixed, the Retract filament approaches the bat at Z1.5 from the home corner

With retraction enabled PrusaSlicer retracts before the first travel and "lifts" to the first-layer Z, so the order is Z-down **then** XY: the plunge to Z1.5 happens at X420 Y0 (39 mm outside the bat) and the nozzle then skims 1.5 mm above the bat to the skirt start. With `Clay Potterbot` the order is XY at Z400 then Z-down over the skirt start. Cura does one coordinated `G0 F4800 X Y Z1.5` (diagonal). The README's hand-built-base workflow ("use Vase Hollow") is therefore only safe with `Clay Potterbot`; with `Clay Potterbot Retract` the approach travel would plough through anything on the bat. Not stated anywhere.

### 1.3 PrusaSlicer deposits 3–17 % less clay per mm than Cura at the same nominal width

Cura's E is rectangular: measured skirt E/mm 3.1181 on all three jobs → **7.500 mm²** = 5 × 1.5. PrusaSlicer uses a rounded-rectangle section, `h·(w − h·(1 − π/4))`: measured skirt E/mm 2.9174 → **7.017 mm²**. The lab's "line width = nozzle" rule was tuned in Cura terms, so the bundle under-deposits relative to every known-good job:

| Nozzle | Layer | Cura mm² | PrusaSlicer mm² | Deficit | `extrusion_multiplier` for parity |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.8 | 0.800 | 0.663 (measured) | 17.2 % | 1.207 |
| 2 | 1.5 | 3.000 | 2.517 | 16.1 % | 1.192 |
| 3 | 1.5 | 4.500 | 4.017 | 10.7 % | 1.120 |
| 4 | 1.5 | 6.000 | 5.517 | 8.0 % | 1.088 |
| 5 | 1.5 | 7.500 | 7.017 (measured) | 6.4 % | 1.069 |
| 6 | 1.5 | 9.000 | 8.517 | 5.4 % | 1.057 |
| 7 | 1.5 | 10.500 | 10.017 | 4.6 % | 1.048 |
| 8 | 1.5 | 12.000 | 11.517 | 4.0 % | 1.042 |
| 9 | 1.5 | 13.500 | 13.017 (measured) | 3.6 % | 1.037 |
| 10 | 1.5 | 15.000 | 14.517 | 3.2 % | 1.033 |

`MACHINE_BEHAVIOR.md` warns not to widen the line to make Preview look solid; that is right about Preview, but the numerical fact is that a 5 mm Cura bead equals a **5.32 mm** PrusaSlicer bead (or 5 mm at multiplier 1.069). Which model is physically closer for clay is a calibration question; the point is that the port silently changed the volume.

### 1.4 Infill profile: the first top layer over sparse infill is printed as a Ø5 mm round bead (2.8× flow)

`Infill @Potterbot 5mm` on the 90 × 70 × 12 box: layer 5 (Z9, first of the 3 tops, over 15 % grid) is `;TYPE:Bridge infill ;WIDTH:5.02 ;HEIGHT:5`, measured **19.8 mm²/mm** against 7.0 for everything else, at `bridge_speed` 40 mm/s. That is 792 mm³/s → **329 mm/s of E**, against `config.g` `M203 E22000` = 367 mm/s (normal printing is 117 mm/s). PrusaSlicer always treats solid over sparse as an internal bridge and `thick_bridges = 0` does not affect internal bridges in 2.9.6; `dont_support_bridges` is irrelevant. Cura prints that layer as ordinary skin. The Infill preset is the only reason the Retract filament exists, and it has never been printed.

Parity value for `bridge_flow_ratio` (normal section ÷ π·w²/4): 1 mm 0.84, 2 mm 0.80, 3 mm 0.57, 4 mm 0.44, **5 mm 0.36**, 6 mm 0.30, 7 mm 0.26, 8 mm 0.23, 9 mm 0.21, 10 mm 0.19.

### 1.5 Spiral start: PrusaSlicer ramps E from zero; Cura runs full flow from the first bead

- Cura `no_bottom__layers.gcode`: the skirt is flat at Z1.5, then the wall on **layer 0** already climbs 1.506 → 3.000 at full flow (E/mm 3.11). With bottoms (`Bottom_Layers.gcode`) layers 0–2 are flat and layer 3 climbs 6.006 → 7.5 at full flow. Cura's spiral layer N climbs from Z\_N to Z\_N+1, so the pot ends one layer above the model (`;MAXZ:255` for 169 × 1.5 mm layers).
- PrusaSlicer: layer 0 is a flat ring at Z1.5; layer 1 is the transition layer, climbing 1.5 → 3.0 with E scaled to the Z fraction: first segment `G1 Z1.508 … E0.02834` for 1.9 mm (E/mm 0.015, 0.5 % of full flow), last `Z3.000 … E5.58518` for 1.9 mm (E/mm 2.92, full). Vase Bottom does the same on layer 3 (`Z4.513 E0.07647`). Top ends at model height.

For a plastic extruder this is fine. For a pressurised ram, a 400 mm loop that asks for 0 → 100 % flow means a starved first spiral loop; Cura's jobs never do this. Not documented.

### 1.6 The visible floor of Vase Bottom is rectilinear, not Archimedean chords

Measured segment directions on the 3 bottom layers of `Vase Bottom + Clay Potterbot`: layer 0 (against the bat) all directions = Archimedean chords; layer 1 dominated by 135° = rectilinear (PrusaSlicer's internal solid infill is always rectilinear); layer 2 (the floor you see inside the pot) is `;TYPE:Top solid infill`, dominated by 45° = `top_fill_pattern = rectilinear` at `top_solid_infill_speed` 20. Only the hidden layer uses `bottom_fill_pattern`. Cura prints all three bottoms concentric (`top_bottom_pattern = concentric` in the 5.12 job). README, `MACHINE_BEHAVIOR.md`, `CURA_VS_PRUSA.md` and the 0.1.5 / 0.1.9 / 0.1.11 changelog debate ("Archimedean vs concentric on wide tips") are about a layer nobody sees.

### 1.7 Spiral vase silently drops every island but one

One STL with two Ø50 mm cylinders 90 mm apart, `Vase Hollow + Clay Potterbot`: the export contains only the right cylinder on all nine layers (0 extrusion points left of centre), no warning in the log, `validate_gcode.py` passes. Two pots in one file (or a merged STL) print as one pot. Two separate objects are governed by PrusaSlicer's rule "Only a single object may be printed at a time in Spiral Vase mode… or enable `complete_objects`", and with `complete_objects = 1` `extruder_clearance_height = 40` limits all but the last object to 40 mm. The docs say `complete_objects = 0` is "on purpose" but never say what happens to a plate with two pots.

### 1.8 Cura's minimum layer time is active; PrusaSlicer's is disabled

The 2020 lab screenshot shows Cura **Minimum Layer Time 5 s / Minimum Speed 10 mm/s** (Cura defaults; applied even with the fan disabled). The reference vases are wide so no slowdown appears in them (every `WALL-OUTER` is `F2400`). PrusaSlicer has `slowdown_below_layer_time = 5` and `min_print_speed = 10` but `cooling = 0` turns the whole cooling logic off, so nothing slows down: the Ø30 neck prints at 2.0 s per layer, the Ø40 cup on the 1 mm tip at 3.1 s. Cura would stretch both to 5 s. Whether the ram wants that is a lab decision; the port changed it without saying so.

### 1.9 `pause_print_gcode = M25` runs `pause.g`, which homes

README and `MACHINE_BEHAVIOR.md` say "pause.g homes the machine. Slicer pause emits M25 instead. Do not copy pause.g into the profile", implying M25 avoids it. On RepRapFirmware an `M25` inside the file is treated as `M226` and **runs `pause.g`** (`G28 F500`), then `resume.g` (`G1 R1 X0 Y0 Z2`, `G1 R1 X0 Y0 Z0`, `G1 E3 F3600`). Homing lifts Z first so it may be survivable, but a slicer pause on this board is a home-and-return, not a park. Not tested on the machine; from the Duet G-code dictionary the docs already cite.

## 2. Cura settings and behaviours not (fully) carried over

Sources: the `;SETTING_3` dumps in the three G-code files, the 3mf containers, `reference/cura/screenshots/`.

| Cura item | Cura value (measured) | Bundle 0.1.18 | Status |
| --- | --- | --- | --- |
| Flow model | rectangular, 7.500 mm² at 5 × 1.5 | rounded rectangle, 7.017 mm² | **Missed** (1.3) |
| Line width | 3mf and all three 2025 jobs: **5 mm** on the 5 mm nozzle. `CFFFP_Test` has `wall_thickness = 7` but its bead is 7.47 mm² = 5 mm; it is not a 7 mm wall. The 2020 screenshot shows Line Width **6** overridden on the 5 mm nozzle (the 2019 S3D "6 mm width"). | width = nozzle | Matches the 2025 jobs; docs misread CFFFP and ignore the 2020 6 mm rule |
| `top_bottom_pattern = concentric` on all bottoms | 3 concentric bottoms | layer 0 Archimedean, 1–2 rectilinear | **Missed** (1.6) |
| Minimum layer time 5 s / min speed 10 | active | present but disabled (`cooling = 0`) | **Missed** (1.8) |
| Spiral from layer 0, full flow, +1 layer at top | see 1.5 | flat layer 0, transition layer ramps E | Different (1.5) |
| Internal bridging | none (skin) | Ø-nozzle round bead | **Missed** (1.4) |
| `retraction_enable = False` | no mid-print `E-` | Clay Potterbot: same. Retract filament: 80 mm / 80 mm/s, 5 mm hop after layer 0, plus a final `G1 E-80` before the end block (580 mm total) | Fine; extra 80 mm undocumented |
| Skirt 3 loops, gap 8, min length 250 | inner loop 11.9 mm from wall centreline | loops at 10.5 / 15.5 / 20.5 mm from the layer-0 hull, `min_skirt_length = 0` | Matches (within 1.4 mm) |
| Layer-change Z move | standalone `G0 F600 Z…` (10 mm/s) | standalone `G1 Z… F960` (16 mm/s) | Fine, documented |
| `speed_layer_0 = 40`, layer-0 skin 20 mm/s | skirt/wall `F2400`, `SKIN` `F1200` on layer 0 | `first_layer_speed 40`, `first_layer_infill_speed 20` | Matches |
| `wall_0_wipe_dist = 2.5` | nozzle/2 wipe on closed walls (bottom layers only) | `wipe = 0` | Minor |
| `M104 S0` / `M109 S0` | emitted | not emitted (`autoemit_temperature_commands = 0`) | Fine, safer |
| `M82` / `M83` wrappers | `M82` then `M83` | `M83` only | Fine |
| `G0` travels | `G0 F4800` | `G1 F4800` | Same on RRF |
| First move | one `G0 F4800 X Y Z1.5` | XY at Z400 then `G1 Z1.5 F960` (Clay); retract, `Z1.5`, XY (Retract) | Fine for Clay; see 1.2 |
| End | `G91 / G0 Z10 E-500 F1000 / G90 / G28` | identical | Matches |

Settings that **do** match, confirmed in the exports: layer 1.5 / first 1.5 (0.8 / 0.8 on the 1 mm tip; the CLI confirms `extrusion_width=1 mm is too low to be printable at a layer height 1 mm`, so the README's reason is right); `;WIDTH:` equals the nozzle on 1 / 5 / 9 mm; 40 mm/s walls and skirt (`F2400`), 20 mm/s solid and top (`F1200`), 80 mm/s travel (`F4800`), 16 mm/s Z (`F960`); `M204 P3000` and `M204 T3000` once each, no `M201` / `M203` / `M566`; `T0 G21 G90 M83 M107 G28` start then the `G21 G90 M83 M107` preamble; no `M104` / `M109` / `M140` / `M190` / `M73`; `;LAYER_CHANGE` per layer; relative E; 5 mm hop only above `retract_lift_above` (`G1 Z8` on layer 1, `G1 Z9.5` on layer 2, `G1 Z17` on the box's layer 7; the skirt→object retract on layer 0 has no hop); `only_retract_when_crossing_perimeters = 1` and `retract_before_travel = 15` give 6 mid-print retracts on the 8-layer box; `ensure_vertical_shell_thickness = 0` loads as `partial` and 2.9.6's spiral-vase requirement dialog (1 perimeter, 0 tops, 0 % fill, no support, `thin_walls` off — checked in `ConfigManipulation.cpp` for 2.9.6) is satisfied, so no prompt; `travel_short_distance_acceleration` is a real 2.9 key; `binary_gcode = 0`; `validate_gcode.py` passes all 13 exports; all bed / STL / SVG / thumbnail asset tests pass.

## 3. Retract-filament assessment

Works: `filament_retract_length = 80` / `filament_retract_lift = 5` overrides are honoured (`G1 E-80 F4800`, `G1 E80 F4800`); the per-printer `retract_lift_above` (1.6 / 0.9) keeps layer 0 flat and hops from layer 1; `retract_lift_below = 0` means no upper bound (hops observed at Z17); Infill's `avoid_crossing_perimeters = 1` slices; `compatible_prints_condition = spiral_vase==1` keeps the unretracted clay off Infill.

Needs attention, in order: 1.1 (no Z10 drop; first `E-80` at Z400 with the head homed), 1.4 (2.8× bridge flow on the very profile this filament exists for), 1.2 (approach at Z1.5 from X420 Y0), the undocumented final `E-80` (total end pull 580 mm), and the `printer_notes` / `filament_notes` / `notes` text on every preset repeating "drops to Z10 after G28".

## 4. Docs and tests accuracy

- README, `CURA_VS_PRUSA.md`, `MACHINE_BEHAVIOR.md`, every `printer_notes`, the Infill `notes` and the Retract `filament_notes`: "drops to Z10 after G28 / first retract is near the bat" is **false** in 0.1.18 (1.1). README "Before you print" step 3 and the `CURA_VS_PRUSA.md` "Checks on a new Prusa slice" list ask the operator to catch it by eye; the shipped bundle fails those checks.
- `CURA_VS_PRUSA.md` "Vase: first travel includes Z" and README "next move must include Z down from 400": the first move is XY at Z400, Z comes in the next move. Safe, but the check as written would fail.
- `CURA_VS_PRUSA.md` labels drift: "config 0.1.16" in the intro and sources table, "0.1.17" in the match table, "0.1.15" in the dialect table; bundle is 0.1.18.
- `CURA_VS_PRUSA.md` "Time is ram-dominated (~30 s for 500 mm at 16.67 mm/s)": on RRF the `F1000` of `G0 Z10 E-500 F1000` applies to the 10 mm Z distance; the extruder is scaled to 833 mm/s and capped by `M203 E22000` (367 mm/s), so the pull takes ≈1.4 s. Same command as Cura, so not a port issue, but the number is wrong. Confirm with a stopwatch.
- `reference/README.md` and `CURA_VS_PRUSA.md`: "CFFFP_Test … 7 mm walls" — the bead is 5 mm (2).
- "Bottoms are Archimedean chords" (README, `MACHINE_BEHAVIOR.md`, print `notes`): true only for the layer on the bat (1.6).
- "Slicer pause emits M25 instead" (1.9).
- "M204 P3000 T3000": two lines (`M204 P3000`, `M204 T3000`). Trivial.
- `validate_gcode.py`: passes the Z400-retract export (1.1) and the 2.8× bridge blobs (1.4) and the dropped island (1.7). The end-retract regex `\bE-?500\b` also accepts `E500` (a 500 mm push). It tracks XYZ from 0,0,0 and never learns the post-`G28` pose, so it cannot see "retract while Z is at 400".
- `tests/test_profile_structure.py::test_two_clay_filaments` asserts `"G1 Z10 F1000" in retract_start` on the raw INI text, which is exactly what PrusaSlicer does not use. `test_gcode_safety.py` has no fixture for a retract before the Z drop.
- `.idx` 0.1.14–0.1.17 describe a fix that is not in the output.

## 5. Suggested changes

1. Quote `start_filament_gcode` in both filament sections (`"; Clay Potterbot Retract\nG1 Z10 F1000 ;drop…"`), as `end_filament_gcode` already is. Add a test that the value starts with `"` (or deserialises like PrusaSlicer), and a fixture `retract_at_z400_rejected.gcode`.
2. `validate_gcode.py`: after the first `G28`, treat Z as unknown and reject any `E-` before a Z move ≤ 20 mm; make the end check `\bE-500\b`; add a flow sanity check (E per XY mm on extrusion moves > 1.5 × median → fail) so bridge blobs and future flow surprises abort the export.
3. Decide flow parity (1.3): either `extrusion_multiplier` per nozzle from the table (per-nozzle filaments, or move the multiplier into the per-nozzle print profiles via width = nozzle + 0.2146·h), or document that PrusaSlicer's bead is 3–17 % leaner than the Cura jobs and re-tune on the machine.
4. Infill: `bridge_flow_ratio` per nozzle from 1.4 (0.36 at 5 mm) so the layer over sparse infill gets normal flow; keep `bridge_speed = 40`. Or drop the Infill preset until it has printed.
5. `top_fill_pattern = archimedeanchords` (or `concentric`) so the visible floor of Vase Bottom / Infill matches Cura's concentric bottoms; note that layer 1 will stay rectilinear.
6. Minimum layer time: if the lab wants Cura's behaviour, `cooling = 1`, `min_fan_speed = 0`, `max_fan_speed = 0`, `fan_always_on = 0`, `slowdown_below_layer_time = 5`, `min_print_speed = 10`, and check the export still contains only `M107`. Otherwise document that narrow sections print faster than in Cura.
7. Retract filament approach (1.2): document that hand-built bases are `Clay Potterbot` only, or accept a layer-0 hop (`retract_lift_above = 0`) so the approach runs at first layer + 5 mm — that reverses 0.1.16. Document the extra `E-80` at the end.
8. Docs: fix every item in 4; add the spiral-vase island rule (1.7) and the two-object / `complete_objects` / 40 mm clearance consequence; describe the transition-layer flow ramp (1.5); state that M25 homes via `pause.g`; align the version labels in `CURA_VS_PRUSA.md`.
9. Optional: `host_type = duet` already allows a Physical Printer entry for direct upload to `192.168.42.14` instead of the manual DWC upload in the README; `filament_type = FLEX` has no effect and could be `PLA`-agnostic or left; `filament_density = 1.24` makes the "[g]" total meaningless for clay (harmless).

## Reproduction

Scratch scripts kept outside the repo in `%TEMP%\pb_review\`: `flatten.py` (resolves `inherits` in `vendor/Potterbot.ini` into flat printer / print / filament INIs, plus a quoted copy of the Retract filament), `make_stl.py` (cup, narrow neck, box, two-cylinder, small cup), `slice_all.ps1` (13 × `prusa-slicer-console.exe --export-gcode --center 190,180 --load printer.ini --load print.ini --load filament.ini model.stl`), `analyze_cura.py` and `analyze_ps.py` (feedrate per `;TYPE:`, E per mm, retracts, lifts, spiral Z per layer, layer times, `M204`, tails, `validate_gcode.py` result). The Cura settings came from the `;SETTING_3` lines and the unzipped 3mf; the 2.9.6 spiral-vase requirement check was read from `src/slic3r/GUI/ConfigManipulation.cpp` at tag `version_2.9.6`.
