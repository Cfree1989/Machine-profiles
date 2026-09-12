# Potterbot 9 — Cura vs PrusaSlicer audit

Read-only comparison of the experimental PrusaSlicer bundle (**config 0.1.14**) against the official Cura **3D Potter Standard** machine and the Cura 5.12 jobs that actually run on this Duet.

The machine already ran a post-0.1.12 Prusa slice successfully (retract off). **0.1.13** sets print/travel acceleration to **3000 mm/s²** so `M204` matches firmware `M201` / Cura (which never slowed accel). **0.1.14** turns mid-print retract on (80 mm at 80 mm/s, 5 mm hop) and drops to Z10 after `G28`.

## Sources

| Source | What it is |
| --- | --- |
| `reference/cura/3D Potter Standard.3mf` | Official 3D Potter Cura machine (FAQ: Models 9 / Pro 9 / Super 9) |
| `reference/cura/no_bottom__layers.gcode` | Cura 5.12 hollow vase, 5 mm walls, 0 bottoms |
| `reference/cura/Bottom_Layers.gcode` | Same model, 3 bottoms then spiral |
| `reference/cura/CFFFP_Test.gcode` | Lab Cura 5.12 job that printed well (7 mm walls) |
| `vendor/Potterbot.ini` | Generated PrusaSlicer bundle 0.1.14 |
| `reference/firmware/config.g` | Live Duet: 420 × 360 × 400, `M83`, cold extrusion |
| [3D Potter FAQ](https://3dpotter.com/faq/) | Cura is recommended; retract recipe is optional and **disabled** in the official 3mf |
| [Duet G-code dictionary](https://docs.duet3d.com/User_manual/Reference/Gcodes) | On this firmware, **G0 = G1 in FFF mode**; `F` is mm/min |
| Lab rule | Match **line width** to the installed nozzle |

Marketing pages often list Potterbot 9 as 420 × 360 × **480** mm. This board’s `config.g` and the official 3mf are **Z 400**. Super 9 is a taller sibling. Use the Duet config, not the brochure.

Simplify3D jobs in `reference/simplify3d/` are 2019 (`Z` max 200, park `X320 Y70`, absolute E). They are not the current start/end language. Cura is the rollback slicer.

---

## What already matches

These are the values that matter on the ram, and they line up.

| Item | Official Cura 3mf / 5.12 jobs | PrusaSlicer 0.1.14 |
| --- | --- | --- |
| Start custom | `G28 ;Home all` only | Same (plus mode lines; see dialect) |
| End custom | `G91` / `G0 Z10 E-500 F1000` / `G90` / `G28` | Same numbers and order |
| Layer height | 1.5 mm Fine (`layer_height` = `layer_height_0`) | 1.5 mm (1 mm tip is 0.8 mm; see below) |
| Print / wall | 40 mm/s → `F2400` | 40 mm/s → `F2400` |
| Travel | 80 mm/s → `F4800` | 80 mm/s → `F4800` |
| Top/bottom skin | 20 mm/s → `F1200` (`speed_topbottom`) | `solid_infill_speed` / `top_solid_infill_speed` 20 |
| First layer / skirt | 40 mm/s (`speed_layer_0`, `skirt_brim_speed`) | `first_layer_speed` 40 — **not** 20 |
| Mid-print retract | `retraction_enable = False` | `retract_length = 80`, `retract_lift = 5`, `retract_speed = 80` (0.1.14; start drops to Z10) |
| Temps / fan | 0 °C, fan off | 0 °C, `M107`, no heater wait |
| Filament model | 1.75 mm, density 1.24, color `#55aaff` | Same |
| Skirt | 3 loops, 8 mm gap | `skirts = 3`, `skirt_distance = 8` |
| Spiral vase | `magic_spiralize = True` | `spiral_vase = 1` on Vase Hollow / Bottom |
| Line width | Lab rule: equal to nozzle (`wall_thickness` 5 in 3mf, 7 in `CFFFP_Test`) | Each printer variant sets every width to that nozzle |
| Relative E | Jobs emit `M83` (firmware `config.g` also has `M83`) | `use_relative_e_distances = 1`, start `M83` |
| Cold extrusion | Firmware `M302 P1` | Slicer does not emit heat |
| XY acceleration | Firmware `M201` 3000 (no `M204` in jobs) | Print/travel **3000** (`M204 P3000 T3000`); Z still capped at 1000 |

`F` in G-code is **mm/min** on RepRapFirmware. 40 mm/s = 2400, 80 mm/s = 4800, end retract `F1000` = 16.67 mm/s (same as `M203 Z1000`).

---

## Dialect (language the slicer emits)

RepRapFirmware 2.x on this Duet is in **FFF mode**. Duet docs: **G0 and G1 are treated the same**; `F` is honored on both. Cura’s `G0` travels are not “unlimited rapids.”

| Topic | Cura 5.12 jobs | PrusaSlicer 0.1.14 |
| --- | --- | --- |
| Flavor comment | `;FLAVOR:RepRap` / machine `RepRap (RepRap)` | `gcode_flavor = reprapfirmware` |
| Travel moves | `G0 F4800 …` | Almost all `G1` (custom end still uses `G0`) |
| Print moves | `G1 F2400 … E` | `G1 F2400 … E` |
| Units / abs | Not in custom start (`config.g` already `G21`/`G90`) | Emits `G21` and `G90` before and after `G28` |
| Tool / fan | `T0`, then `M107` | `T0`, `M107` (slicer repeats `M107` after start) |
| Heat lines | Engine prepends `M104 S0` / `M109 S0` even though custom start is only `G28` | `autoemit_temperature_commands = 0` — **no** `M104`/`M109` |
| E mode wrappers | `M82` then `M83` at start; `M82` before end custom; `M83` after | `M83` only |
| Accel in file | **None** (no `M204`) — firmware `M201` 3000 mm/s² XY | `M204 P3000` / `T3000` (same XY number; Z still `M201` 1000) |
| Feature comments | `;TYPE:SKIRT`, `WALL-OUTER`, `SKIN`, `;LAYER:0` | `;TYPE:Skirt/Brim`, `External perimeter`, `;LAYER_CHANGE` |
| End comment | `depressurize Extruder slightly` / `G28 ;Home All` | `lift and retract clay` / `G28 ;Home all` |
| Width in file | None | `;WIDTH:7` (etc.) |

Firmware `homeall.g` comments say `;Home All`. Case does not matter. Cura’s extra `M104 S0`/`M109 S0` are harmless on a cold machine with `M302 P1` (this job already ran that way). Prusa omitting them is closer to the **custom** start G-code in the 3mf.

RRF 2.x changelog: `M83` inside `config.g` does **not** stick after boot. Both slicers emitting `M83` in the job is required. That is correct.

---

## Feeds and speeds that still differ

Nominal print/travel mm/s match. Isolated Z hops and a few CuraEngine short-segment F values do not.

### Acceleration

`config.g`: `M201 X3000 Y3000 Z1000 E3000`, jerk `M566` 3000 mm/min (50 mm/s).

Cura 5.12 jobs never send `M204`, so print and travel use those firmware maxima.

PrusaSlicer 0.1.14 sets every print/travel acceleration to **3000** (including first layer and short travel). It still emits `M204 P3000 T3000` because `gcode_flavor = reprapfirmware`. On Duet, P/T are mm/s²; **P3000 T3000 is the same XY accel Cura gets from `M201`**. Z moves remain limited to 1000 by firmware `M201 Z`.

0.1.12 was slower (`P500` first layer, `P1000` print, `T2000` travel, `T500` short travel). Re-import 0.1.13 before comparing corners to Cura.

### Z feed

Firmware cap: `M203 Z1000` → **16.67 mm/s**.

| Situation | Cura | Prusa 0.1.14 |
| --- | --- | --- |
| First approach after `G28` | One `G0 F4800 X… Y… Z1.5` (XY asks 80 mm/s; **Z is firmware-limited to 16.67**, so the whole coordinated move is Z-limited) | Start `G1 Z10 F1000`, then slicer travel/hop from there (`travel_speed_z = 16` → about `F960`) |
| Isolated Z on bottoms | `Bottom_Layers.gcode` has `G0 F600 Z3` (**10 mm/s**) between skin islands | Z travels at 16 mm/s |
| End lift | `G0 Z10 E-500 F1000` (16.67 mm/s, Z+10 and ram together) | Same |

Cura’s 10 mm/s standalone Z is a Cura custom-machine default, not this board’s `M203`. Prusa’s 16 mm/s is closer to firmware. Neither exceeds Z max.

### First-layer vs “bottom” speed

Cura `speed_layer_0 = 40`. `speed_topbottom = 20` is **solid skin**, not the first wall/skirt. Prusa matches that split. The README phrase “20 bottoms” means infill/skin, not the first bead.

`Bottom_Layers.gcode` also has a few odd print feeds (`F1012`–`F1013.9`, ~16.9 mm/s) on short segments after a travel. That is CuraEngine path planning, not a profile number we copied. Prusa will not reproduce those exact F values.

### FAQ retract vs what we ship

[3D Potter FAQ](https://3dpotter.com/faq/) still lists 1000 mm at **1000 mm/s**, 5 mm lift, extra restart −10 mm. The official 3mf **stores** amount/speed 1000 but sets **`retraction_enable = False`**. Known-good Cura jobs never retract mid-print (only the end `E-500`).

`config.g` `M203 E22000` is ~367 mm/s. FAQ 1000 mm/s cannot run on this motor (that stall is already documented). **0.1.14** uses **80 mm at 80 mm/s** and a 5 mm hop, with start G-code `G1 Z10 F1000` after `G28` so the first retract is not at Z400. Extra restart stays 0 (Cura 3mf), not the FAQ −10.

### Other Cura-only / Prusa-only rates

- Cura `speed_slowdown_layers = 1` is in the 3mf; with `speed_layer_0 = 40` equal to print speed it does not change the first skirt `F2400`.
- Prusa `max_print_speed = 85` matches the `config.g` comment (slicer ≤ 85 mm/s). Cura jobs do not declare it; they simply use 40/80.
- Simplify3D lab notes: default **3000 mm/min** (50 mm/s). That is **not** the Cura 40 mm/s Fine profile. Ignore S3D for speed parity.

---

## Positioning and work envelope

After `G28`, `homeall.g` leaves the head at **X max, Y min, Z max** = **X420 Y0 Z400**. Z0 is the bat. Cura and Prusa both use **absolute XYZ**. The first print move must command **Z ≈ 1.5**, not a 5 mm hop as if the nozzle were already on the layer.

| Envelope | Cura 3mf | Firmware | Prusa plater |
| --- | --- | --- | --- |
| X | 420 | 420 | **381** (15″ bat) |
| Y | 360 | 360 | 360 (bat is 381; Y travel is the limit) |
| Z | 400 | 400 | 400 |

Origin is firmware bed corner **X0 Y0**, same as Cura’s custom machine. Operator macro `PRINT START LOCATION.gcode` jogs to **X210 Y180 Z0** (center of **firmware** 420 × 360, not the 381 bat). That macro is not in either slicer’s start G-code.

`validate_gcode.py` **rejects X > 381**. Cura will happily slice to X 420. That is a lab safety choice, not a Cura match. Jobs on the bat (CFFFP max X 313, official vases max X 329) pass both.

1 mm nozzle: Prusa forces **0.8 mm** layer because it will not slice `extrusion_width <= layer_height` or a first layer taller than the hole. Cura would still offer 1.5 mm Fine on a 1 mm tip. Only that variant disagrees.

---

## Start and end sequences (side by side)

Cura 5.12 engine + official custom:

```text
T0
M104 S0
M109 S0
G28 ;Home all
M82
M83
M107
G0 F4800 X… Y… Z1.5    ; first travel includes Z
G1 F2400 … E…          ; skirt
…
M82
G91
G0 Z10 E-500 F1000     ; official comment: depressurize
G90
G28 ;Home All
M83
```

PrusaSlicer 0.1.14 intended:

```text
T0
G21
G90
M83
M107
G28 ;Home all
G1 Z10 F1000               ; drop from Z400 before slicer retract
G21 / G90 / M83 / M107     ; slicer repeat
G1 E-80 …                  ; first retract at Z10, not Z400
G1 … Z6.5 …                ; hop = layer + 5
G1 F2400 … E…              ; skirt at ~Z1.5
…
G91
G0 Z10 E-500 F1000
G90
G28 ;Home all
```

**0.1.11** (do not print) inserted `G1 E-80 F1020` then `G1 Z6.5` while the head was still at Z400. That is the “retract for several seconds then print at the top of Z” failure. 0.1.12 turned retract off. 0.1.14 turns it back on **after** the Z10 drop.

End `E-500` at `F1000` is identical. Time is ram-dominated (~30 s for 500 mm at 16.67 mm/s) with a 10 mm relative Z lift. Cura then homes **all**; Prusa the same. Old Simplify3D ended `Z20`, parked `X320 Y70`, and `G28 Z` only.

---

## Paths, fill, and extra presets

| Topic | Cura | Prusa 0.1.14 |
| --- | --- | --- |
| Hollow vase | 0 bottom, 0 top, spiral on | Vase Hollow: same |
| 3-bottom vase | `bottom_layers = 3`, then spiral; `top_bottom_pattern = concentric` | Vase Bottom: 3 bottoms, spiral on; bottoms **Archimedean chords**, tops **rectilinear** |
| Infill | Official jobs: 0% | Extra **Infill** preset: 15% **grid**, 3 bottoms, 3 tops, spiral **off** |
| Walls | `wall_thickness` = nozzle (one wall) | `perimeters = 1`, widths = nozzle |
| Wall generator | Cura 5.12 default Arachne (3mf is older `setting_version` 9) | `perimeter_generator = arachne` |
| Fuzzy skin | Lab instructions: must be **off** | Not in the bundle (stays off) |
| Sequential objects | Not in official jobs | `complete_objects = 0` (on purpose: tall pots vs nozzle) |

Bottom fill pattern is a real path difference on Vase Bottom / Infill. Hollow spiral walls should look like Cura. Preview in PrusaSlicer still draws round tubes; the G-code pitch is the line width (see `MACHINE_BEHAVIOR.md`).

---

## Naming and UI, not motion

- Cura machine name: **3D Potter Standard**. Wizard vendor: **3D Potter (experimental)**; printers **1mm Nozzle** … **10mm Nozzle**.
- FAQ nozzle range is typically 1–8 mm; this pack also has 9 and 10 mm variants.
- Cura quality container is named **Fine** with 1.5 mm layer. Prusa print names omit the layer height.
- Pause: slicer `M25`. Board `pause.g` runs **`G28`** — do not paste that into the profile (already documented).
- Prime/retract buttons stay Duet macros (`E100000` / `E-100000`). Neither slicer primes the ram.

---

## Residual differences (not bugs unless you want Cura-identical output)

1. **`M204` still present** — values are 3000, same as firmware XY. Cura omits the command. Z stays 1000 via `M201`.
2. **Plater X 381 vs Cura X 420** — intentional bat clip + validator.
3. **No `M104 S0`/`M109 S0`** — safer; Cura still prints with them.
4. **`G1` vs `G0` travel** — same on this firmware.
5. **Archimedean bottoms vs Cura concentric** — only when bottoms exist.
6. **1 mm tip 0.8 mm layer** — PrusaSlicer limit.
7. **Infill preset** — extra; official Cura vase is 0% infill.
8. **Mid-print retract on** — 80 mm / 80 mm/s / 5 mm hop. Official Cura jobs leave it off. Start drops to Z10 first.

---

## Checks on a new Prusa slice

After re-importing 0.1.14, the exported file should look like this:

- After `G28`, the next **motion** is `G1 Z10 F1000`. The first `E-80` must be **after** that drop, not at Z400.
- First bead near **Z1.5** (or 0.8 on the 1 mm tip), not hop height 6.5.
- Skirt/print `F2400`, travel `F4800`, end `G0 Z10 E-500 F1000` then `G28`.
- `M83` present; no `M104`/`M109` with S>0; XY inside 381 × 360.
- Retract length 80 / Lift Z 5 / speed 80 in the printer preset.
- If `M204` appears, **P** and **T** should be **3000**, not 500/1000/2000.

If those hold, remaining mismatch is fill pattern and G0 vs G1 comments, not feeds or XY accel.
