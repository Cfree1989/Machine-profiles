# Potterbot 9 machine behavior

Evidence for the PrusaSlicer bundle. Labels are from files in `reference/`.

## Controller

- Duet 2 WiFi, RepRapFirmware **2.04RC1** (2019-07-14). DWC screenshots in `reference/dwc/`.
- `config.g` names the machine **3DP-D9**. Absolute XYZ, **relative E** (`M83`), cold extrusion (`M302 P1`), bed heater off (`M140 H-1`).
- Drive limits: X 0–420, Y 0–360, Z 0–400. Home: X max, Y min, Z max. After `G28` the head is at **X420 Y0 Z400**.
- Max feed (mm/s): XY 100, Z 16.67, E 366.67. Accel XY/E 3000, Z 1000. `config.g` comment: keep slicer speeds ≤ 85 mm/s. The Prusa bundle uses print/travel acceleration **3000** so emitted `M204` matches Cura jobs that rely on these `M201` values.
- An older board dump used the same `config.g` with Z max 200 (short-column setup). Live config is Z 400.

## Official slicer settings

From `reference/cura/3D Potter Standard.3mf` (Cura machine) and the Cura 5.12 jobs:

| Setting | Value |
| --- | --- |
| Start | `G28` |
| End | `G91` / `G0 Z10 E-500 F1000` / `G90` / `G28` |
| Nozzle / line width | 5 mm / 5 mm (`wall_thickness = 5`) |
| Layer | 1.5 mm |
| Speeds | print 40, travel 80, bottom 20 mm/s |
| Skirt | 3 loops, 8 mm gap |
| Spiral vase | on |
| Infill / top | 0 / 0 |
| Retract during print | off (Clay Potterbot filament); 80 mm / 80 mm/s / 5 mm hop (Clay Potterbot Retract filament) |
| Temps / fan | 0 / off |
| Filament diameter | 1.75 mm (volumetric model for the ram) |

`no_bottom__layers.gcode` has `bottom_layers = 0`. `Bottom_Layers.gcode` has `bottom_layers = 3`. Both spiralize after the base.

Lab notes say to match **line width** to the nozzle on the machine. It does not scale layer height with the tip. 3D Potter does not publish a layer-height-to-nozzle percentage. This bundle keeps **1.5 mm layer** on 2–10 mm nozzles and sets line width equal to the selected nozzle. The 1 mm tip is **0.8 mm layer** because PrusaSlicer rejects `extrusion_width <= layer_height` and also rejects first-layer height greater than nozzle diameter. Print profile names omit the layer height. Sparse infill is **grid**, solid bottoms are **Archimedean chords**, and solid tops are **rectilinear**. Infill overlap is **15%** so bottoms meet the wall.

PrusaSlicer Preview draws each move as a rounder tube than the real 1.5 mm × nozzle ribbon. On a 9 mm tip the G-code pitch is the flow spacing (~8.7 mm) with **WIDTH:9** and a 0.3 mm overlap; the dark grid between rings is the viewer, not missing clay. Confirm from the `;WIDTH:` lines and centerline spacing, or a short skirt on the machine. Do not keep widening line width to make Preview look solid — that would over-extrude.

## Retraction

Official Cura **3D Potter Standard** stores `retraction_amount = 1000` / `retraction_speed = 1000` but sets `retraction_enable = False`. Known-good Cura jobs never retract mid-print. After `G28` the head is at **X420 Y0 Z400**. Cura’s first move is a single `G0 … Z1.5` from that pose.

The [3D Potter FAQ](https://3dpotter.com/faq/) mid-print recipe (1000 mm at 1000 mm/s) exceeds `config.g` `M203 E22000` (367 mm/s) and is what stalled the ram motor in Cura.

This bundle puts retraction on the **filament** (0.1.17; 0.1.15–0.1.16 used a second set of “Retract” printers). The single printer, **1mm–10mm Nozzle**, keeps mid-print retract **off** (`retract_length = 0`, `retract_lift = 0`) and the official Cura start (`G28` only); it carries `retract_speed = 80`, `deretract_speed = 80`, and `retract_lift_above` = first layer + 0.1 mm (**1.6** on 1.5 mm Fine, **0.9** on the 1 mm tip) so that the values are ready when a filament turns retraction on. **Clay Potterbot** adds nothing, so it is byte-identical to Cura’s unretracted behaviour, and its `compatible_prints_condition = spiral_vase==1` keeps it off the Infill profile. **Clay Potterbot Retract** sets `filament_retract_length = 80` and `filament_retract_lift = 5` (PrusaSlicer filament overrides) so layer 0 / the skirt does not hop; extra restart **0**, wipe **off**. Not the FAQ 1000 mm/s. Its `start_filament_gcode` is `G1 Z10 F1000`, which PrusaSlicer emits right after the printer start G-code and before the first travel, so the first slicer retract is near the bat. 0.1.11’s `E-80` hop without that drop ran the ram at Z400, then treated `G1 Z6.5` as a hop from layer height. End G-code is still `G0 Z10 E-500 F1000` for both clays.

## Bed vs bat

Official Cura machine is **420 × 360 × 400** (firmware travel). The physical bat is **15×15″ (381 × 381 mm)**. This bundle uses **381 × 360 × 400** so the plater matches the bat and does not ask for Y past firmware travel.

The plater draws the real bat from `vendor/Potterbot/POTTERBOT9_bed.stl` (381 × 381 × 6.35 mm, 12.7 mm corner radius, placed so its front-left corner is bed X0 Y0 and it overhangs the printable Y by 21 mm at the back) with `POTTERBOT9_texture.svg` stretched over the 381 × 360 printable area. PrusaSlicer 2.9.6 draws a vendor plate only when both `bed_model` and `bed_texture` resolve in `%APPDATA%\PrusaSlicer\vendor\Potterbot\`; otherwise it silently falls back to the plain grid. `scripts/generate_assets.py` regenerates both.

## Macros (do not paste blindly)

- `reference/duet-macros/PRIME.gcode` — `G1 E100000 F30000` (charge the ram).
- `reference/duet-macros/RETRACT.gcode` — `G1 E-100000 F20000`.
- `reference/duet-macros/PRINT START LOCATION.gcode` — center of firmware travel (`X210 Y180`).
- `reference/firmware/macros/pause.g` — **homes** (`G28`). Not used as slicer pause (`M25` instead).
