# 3D Potterbot 9 — PrusaSlicer (experimental)

This folder is the Potterbot pack in [PrusaSlicer print profiles](../README.md). Raise3D and later printers are siblings, not mixed in here.

**This is not a production-ready profile.** It is a PrusaSlicer bundle derived from the official Cura **3D Potter Standard** project and two Cura 5.12 jobs on this machine (`no_bottom__layers.gcode`, `Bottom_Layers.gcode`). Validate on the machine before any unattended print. Keep Cura as the rollback slicer.

Printer workflow: join the **3DP-9** Wi-Fi → open Duet Web Control (`192.168.42.14` or the 3DP-D9 shortcut) → **Connect** → slice on the PC → upload `.gcode` in DWC → start from DWC. Prime clay from the Duet **Prime** macro if the ram is not already charged. Line width must match the nozzle on the machine. If you built a clay base by hand, use **Vase Hollow** (0 bottoms / 0 tops). Official Cura Fuzzy Skin stays off.

## What is in this pass

| Preset | Name |
| --- | --- |
| Printer | one machine, **3D Potterbot 9**, with variants **1mm Nozzle** … **10mm Nozzle** (the printer itself never retracts) |
| Filament | **Clay Potterbot** (retract off; offered with the two vase profiles only) and **Clay Potterbot Retract** (80 mm at 80 mm/s, 5 mm hop after layer 0; works with all three). Both are 0 °C, no fan, 1.75 mm volumetric model |
| Print | **Vase Hollow**, **Vase Bottom** (3 Archimedean-chord bottoms then spiral), and **Infill** (15% grid, 3 Archimedean-chord bottoms, 3 Archimedean-chord tops, spiral off; needs Clay Potterbot Retract). Sequential printing is **on** (one object finishes before the next). |

Layer height is the official Fine value: **1.5 mm**, except **0.8 mm** on the 1 mm nozzle (PrusaSlicer will not slice when line width is not greater than layer height, and it also rejects a first layer taller than the tip). Line width equals the nozzle on the machine (lab Cura notes). Bottoms and the visible floor are **Archimedean chords**. Speeds are the official Cura values: **40 mm/s** print, **80** travel, **20** bottoms. Print and travel acceleration is **3000 mm/s²** (firmware `M201` / Cura). There is **no fan and no heaters**; cooling stays off so the ram is never asked to wait for plastic to freeze. Post-processing scales print E to match Cura’s rectangular bead volume and holds **full ram flow** on the first spiral loop (PrusaSlicer would otherwise ramp from zero).

Retraction is a **filament** choice (PrusaSlicer keeps retraction on the printer and filament, never on the print profile). The printer stays at the official Cura setting: retract off, start is `G28` only, then Z comes down with the first travel. **Clay Potterbot Retract** adds PrusaSlicer filament overrides: **80 mm at 80 mm/s** with a **5 mm** Z-hop after layer 0 (not the FAQ 1000 mm/s), and its filament start G-code drops to **Z10** after `G28` so that first retract is not at the top of the column. The skirt unretracts at layer height; hops start on layer 1. Selecting **Infill** with Clay Potterbot loaded makes PrusaSlicer switch to Clay Potterbot Retract, because unretracted clay is only compatible with `spiral_vase==1`. End G-code still lifts Z 10 mm and **retracts E-500**, then homes.

The printer notes carry `NO_TEMPLATES`, so PrusaSlicer's generic Template filaments (Generic PLA and friends) are hidden for this machine and only the two clays are offered.

The plater is the **15×15″ bat** clipped to Y travel: **381 × 360 × 400 mm**, with the two **front corners rounded 12.7 mm** in `bed_shape` like the bat itself (the back edge is straight because the bat continues 21 mm past Y travel). Firmware travel is 420 × 360 × 400; X past 381 is unused so the model stays on the bat. `vendor/Potterbot/` holds the plater and wizard assets: `POTTERBOT9_bed.stl` (the 381 × 381 × 6.35 mm bat with rounded corners, overhanging the 360 mm printable Y by 21 mm at the back; PrusaSlicer draws that unreachable strip in its fixed dark grey), `POTTERBOT9_texture.svg` (grey textured surface with a 10 / 50 mm grid, clipped by PrusaSlicer to the rounded `bed_shape`), and `POTTERBOT9_thumbnail.png` (180 × 256 Configuration Wizard image). PrusaSlicer only draws the vendor plate when both the STL and the SVG are present.

## Install

### Lab PC

Print profiles call `scripts\validate_gcode.py` by **absolute path**. Put this repo at `C:\Repos\Prusa-Slicer-Print-Profiles`. Then install:

1. **PrusaSlicer 2.9.6** (current stable).
2. **Python 3** from [python.org](https://www.python.org/downloads/). Confirm `py -3 --version`.

Required script:

```text
C:\Repos\Prusa-Slicer-Print-Profiles\Potterbot\scripts\validate_gcode.py
```

`validate_gcode.py` first runs `scripts/fix_gcode.py` on the export (Cura volume + full spiral start), then checks the file.

### On the Duet

Upload `reference/firmware/macros/pause.g` over the board’s `pause.g` (DWC → System). The old file homed mid-print. This one lifts 10 mm and parks at X420 Y0. Leave `resume.g` alone.

### A. Configuration Wizard (vendor bundle)

1. Copy `vendor/Potterbot.ini`, `vendor/Potterbot.idx`, and the whole `vendor/Potterbot/` folder (STL, SVG, PNG) to `%APPDATA%\PrusaSlicer\vendor\`, so you end up with `%APPDATA%\PrusaSlicer\vendor\Potterbot\POTTERBOT9_bed.stl` next to `Potterbot.ini`
2. Restart PrusaSlicer
3. **Configuration Wizard** → Other Vendors (under Other FFF) → enable **3D Potter (experimental)** → **3D Potterbot 9** (the wizard shows the machine photo) → pick **1mm Nozzle** through **10mm Nozzle** to match the tip on the machine. The list name is **3D Potter**, not Potterbot.
4. Confirm **Clay Potterbot** and **Clay Potterbot Retract** are the only filaments offered, and Vase Hollow / Vase Bottom / Infill appear. The plater should show the white bat overhanging the back of the 360 mm printable area; a plain grid means the `vendor/Potterbot/` folder did not get copied.

### B. Import Config Bundle

1. **File → Import → Import Config Bundle**
2. Select `vendor/Potterbot.ini` or `profiles/Potterbot-9-bundle.ini`
3. Select **5mm Nozzle**, the clay (Clay Potterbot for vase, Clay Potterbot Retract for Infill), and the matching print profile. The bed model, texture and thumbnail only load through the vendor folder in A, not through an imported bundle.

## Source of truth

- Official Cura machine / start / end: `reference/cura/3D Potter Standard.3mf`
- Hollow vs 3-bottom vase: `reference/cura/no_bottom__layers.gcode`, `reference/cura/Bottom_Layers.gcode`
- Axis limits and relative E: `reference/firmware/config.g`
- Evidence notes: `docs/MACHINE_BEHAVIOR.md`

2019 Simplify3D files in `reference/simplify3d/` are older known-good jobs (6 mm width, park `X320 Y70`). They were not used for start/end in this pass.

## Assumptions you must treat as untested

- 1.75 mm filament diameter matches how this ram’s E steps were calibrated (official Cura and Simplify3D both used it).
- E-500 at the end is enough to stop ooze on your current clay body. The Duet **Retract** button is a much larger pull if you need it.
- **Clay Potterbot** leaves mid-print retract off. **Clay Potterbot Retract** uses **80 mm at 80 mm/s** with a 5 mm hop after layer 0. Official Cura jobs leave retract off until the end `E-500`. Supervised first Retract print: confirm the first `E-` is after the Z10 drop, not at Z400, and that the skirt unretracts at layer height (~1.5 mm), not hop height (6.5 mm).
- The bat in the plater is drawn from a measured 15 × 15 × ¼ in with 12.7 mm corner radii, starting at X0 Y0. The drawing is cosmetic; `bed_shape` (381 × 360) is what PrusaSlicer and `validate_gcode.py` enforce.
- Official docs only publish 1.5 mm layer height (Fine / 3D Potter Standard). That value is used on 2–10 mm nozzles. The 1 mm tip is **0.8 mm** so line width stays above layer height. Line width still follows the installed tip. Tune layer height per clay if 1.5 mm is wrong for a large nozzle.
- Bat origin is X0 Y0 (firmware bed edge). If the bat is shifted on the table, jog and re-zero before trusting the plater.
- `bed_shape` is a polygon (rounded front corners), so Printer Settings → Bed shape shows **Custom** rather than Rectangular. Its bounding box is still 381 × 360; `validate_gcode.py` keeps checking that rectangle.
- `pause.g` on the board must **park**, not home. Replace the Duet file with `reference/firmware/macros/pause.g` (lift 10 mm, move to **X420 Y0**). Slicer pause still emits `M25`, which runs that macro. Resume is unchanged (`resume.g`). Do not paste `pause.g` into the slicer profile.

## Before you print

1. Install the nozzle that matches the selected printer variant. Line width in the profile equals that nozzle.
2. Slice a short vase with **Clay Potterbot**, or **Infill** with **Clay Potterbot Retract**. Post-processing scales clay volume to the Cura jobs, holds full flow on the first spiral loop, then runs `validate_gcode.py` and **aborts export** if it sees heater commands, a retract still at Z400, missing `E-500`, missing `M83`, or moves off the 381 × 360 bat.
3. Read the first and last lines. With Clay Potterbot the start is `G28` only (next move must include Z down from 400). With Clay Potterbot Retract the start is `G28` then `G1 Z10 F1000` from the filament start G-code; the first slicer `E-80` must be after that drop. End is `G0 Z10 E-500 F1000` then `G28`.
4. Charge clay with the Duet Prime macro. Supervised first bead: home, first loop, spiral, end retract. For two pots, add each as its own object (split a multi-body STL) and keep ~40 mm of empty radius so the ram clears the finished one.
5. Do not leave a tall job unattended until that check passes.

## Rollback

Use Cura with **3D Potter Standard** as before. Nothing in this repo is written to the printer’s firmware except the `pause.g` you copy by hand.

## Tests

```text
python -m unittest discover -s Potterbot/tests -v
```

Regenerate the `.ini` files after editing `scripts/generate_bundle.py`:

```text
python Potterbot/scripts/generate_bundle.py
```

Regenerate the plater assets (`vendor/Potterbot/POTTERBOT9_bed.stl` and `POTTERBOT9_texture.svg`) after editing `scripts/generate_assets.py`; it is standard library only:

```text
python Potterbot/scripts/generate_assets.py
```

The wizard thumbnail is a one-off fit of a machine photo into 180 × 256 (PrusaSlicer's size). Only the PNG is committed; to redo it from a new photo:

```text
powershell -File tools\make_thumbnail.ps1 -Source photo.png -Destination Potterbot\vendor\Potterbot\POTTERBOT9_thumbnail.png
```
