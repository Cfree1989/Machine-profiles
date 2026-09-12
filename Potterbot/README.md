# 3D Potterbot 9 — PrusaSlicer (experimental)

This folder is the Potterbot pack in [PrusaSlicer print profiles](../README.md). Raise3D and later printers are siblings, not mixed in here.

**This is not a production-ready profile.** It is a PrusaSlicer bundle derived from the official Cura **3D Potter Standard** project and two Cura 5.12 jobs on this machine (`no_bottom__layers.gcode`, `Bottom_Layers.gcode`). Validate on the machine before any unattended print. Keep Cura as the rollback slicer.

Printer workflow: join the **3DP-9** Wi-Fi → open Duet Web Control (`192.168.42.14` or the 3DP-D9 shortcut) → **Connect** → slice on the PC → upload `.gcode` in DWC → start from DWC. Prime clay from the Duet **Prime** macro if the ram is not already charged. Line width must match the nozzle on the machine. If you built a clay base by hand, use **Vase Hollow** (0 bottoms / 0 tops). Official Cura Fuzzy Skin stays off.

## What is in this pass

| Preset | Name |
| --- | --- |
| Printer | **1mm Nozzle** … **10mm Nozzle** (default 5 mm) |
| Filament | **Clay Potterbot** (0 °C, no fan, 1.75 mm volumetric model) |
| Print | **Vase Hollow**, **Vase Bottom** (3 Archimedean-chord bottoms then spiral), and **Infill** (15% grid, 3 Archimedean-chord bottoms, 3 rectilinear tops, spiral off) |

Layer height is the official Fine value: **1.5 mm**, except **0.8 mm** on the 1 mm nozzle (PrusaSlicer will not slice when line width is not greater than layer height, and it also rejects a first layer taller than the tip). Line width equals the nozzle on the machine (lab Cura notes). Bottoms are **Archimedean chords**. Speeds are the official Cura values: **40 mm/s** print, **80** travel, **20** bottoms. Print and travel acceleration is **3000 mm/s²** (firmware `M201` / Cura). Mid-print retract is **80 mm at 80 mm/s** with a **5 mm** Z-hop (not the FAQ 1000 mm/s). After `G28` the head is at **Z400**; start G-code drops to **Z10** so that first retract is not at the top of the column. End G-code still lifts Z 10 mm and **retracts E-500**, then homes.

The plater is the **15×15″ bat** clipped to Y travel: **381 × 360 × 400 mm**. Firmware travel is 420 × 360 × 400; X past 381 is unused so the model stays on the bat.

## Install

### Lab PC

Print profiles call `scripts\validate_gcode.py` by **absolute path**. Put this repo at `C:\Repos\Prusa-Slicer-Print-Profiles`. Then install:

1. **PrusaSlicer 2.9.6** (current stable).
2. **Python 3** from [python.org](https://www.python.org/downloads/). Confirm `py -3 --version`.

Required script:

```text
C:\Repos\Prusa-Slicer-Print-Profiles\Potterbot\scripts\validate_gcode.py
```

### A. Configuration Wizard (vendor bundle)

1. Copy `vendor/Potterbot.ini` and `vendor/Potterbot.idx` to `%APPDATA%\PrusaSlicer\vendor\`
2. Restart PrusaSlicer
3. **Configuration Wizard** → Other Vendors (under Other FFF) → enable **3D Potter (experimental)** → 3D Potterbot 9 → pick **1mm Nozzle** through **10mm Nozzle** to match the tip on the machine. The list name is **3D Potter**, not Potterbot.
4. Confirm **Clay Potterbot** and a Vase Hollow / Vase Bottom profile appear

### B. Import Config Bundle

1. **File → Import → Import Config Bundle**
2. Select `vendor/Potterbot.ini` or `profiles/Potterbot-9-bundle.ini`
3. Select **5mm Nozzle** (or the tip that is installed), Clay Potterbot, and a vase profile

## Source of truth

- Official Cura machine / start / end: `reference/cura/3D Potter Standard.3mf`
- Hollow vs 3-bottom vase: `reference/cura/no_bottom__layers.gcode`, `reference/cura/Bottom_Layers.gcode`
- Axis limits and relative E: `reference/firmware/config.g`
- Evidence notes: `docs/MACHINE_BEHAVIOR.md`

2019 Simplify3D files in `reference/simplify3d/` are older known-good jobs (6 mm width, park `X320 Y70`). They were not used for start/end in this pass.

## Assumptions you must treat as untested

- 1.75 mm filament diameter matches how this ram’s E steps were calibrated (official Cura and Simplify3D both used it).
- E-500 at the end is enough to stop ooze on your current clay body. The Duet **Retract** button is a much larger pull if you need it.
- Mid-print retract is **80 mm at 80 mm/s** with a 5 mm hop. Official Cura jobs leave retract off until the end `E-500`. Supervised first print: confirm the first `E-` is after the Z10 drop, not at Z400, and that the first bead is at layer height (~1.5 mm), not hop height (6.5 mm).
- Official docs only publish 1.5 mm layer height (Fine / 3D Potter Standard). That value is used on 2–10 mm nozzles. The 1 mm tip is **0.8 mm** so line width stays above layer height. Line width still follows the installed tip. Tune layer height per clay if 1.5 mm is wrong for a large nozzle.
- Bat origin is X0 Y0 (firmware bed edge). If the bat is shifted on the table, jog and re-zero before trusting the plater.
- `pause.g` on the board homes the machine. Slicer pause emits `M25` instead. Do not copy `pause.g` into the profile.

## Before you print

1. Install the nozzle that matches the selected printer variant. Line width in the profile equals that nozzle.
2. Slice a short vase, or use **Infill** for infill / several objects. Post-processing runs `validate_gcode.py` and **aborts export** if it sees heater commands, missing `E-500`, missing `M83`, or moves off the 381 × 360 bat.
3. Read the first and last lines: start is `G28` then `G1 Z10 F1000` (no heat); the first slicer retract must be after that drop, not at Z400; end is `G0 Z10 E-500 F1000` then `G28`.
4. Charge clay with the Duet Prime macro. Supervised first bead: home, first loop, spiral, end retract.
5. Do not leave a tall job unattended until that check passes.

## Rollback

Use Cura with **3D Potter Standard** as before. Nothing in this repo is written to the printer’s firmware.

## Tests

```text
python -m unittest discover -s Potterbot/tests -v
```

Regenerate the `.ini` files after editing `scripts/generate_bundle.py`:

```text
python Potterbot/scripts/generate_bundle.py
```
