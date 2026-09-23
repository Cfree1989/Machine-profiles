# Reference files

Known-good **ideaMaker** output lives in `ideamaker/`. PrusaSlicer start/end G-code, tool changes, and Hyper Speed behavior are derived from those files only. Do not replace them with generic Klipper or Prusa examples.

| Path | What it is |
| --- | --- |
| `ideamaker/` | Authoritative Hyper Speed ideaMaker jobs (left / right / dual) plus `Compensation Test.gcode` for accel / FLOW |
| `ideamaker/Settings/` | ideaMaker **Standard - Pro2 Plus HS - PLA** Advanced Settings tabs |
| `prusaslicer/` | Current Dual profile export — compare only, not a source of start/end G-code |
| `community/extracted/` | 2022 Prusa forum configs; **not** Hyper Speed machine evidence |

`.data` files are binary metadata only and were not modified.

## Authoritative (this machine)

| File | Role |
| --- | --- |
| `ideamaker/LeftonlyExtruder.gcode` + `.data` | Hyper Speed, left `T0`, `[Raise3D] PLA` |
| `ideamaker/RightonlyExtruder.gcode` + `.data` | Hyper Speed, right `T1`, `[Raise3D] PLA` |
| `ideamaker/MulticolorRaise3d.gcode` + `Multicolor.data` | Hyper Speed, dual / two-color `T0`+`T1`, `[Raise3D] PLA` |
| `ideamaker/Compensation Test.gcode` + `.data` | Accel 5000 walls/infill/first vs 2000 solid/top; PLA FLOW numbers |

## This profile’s export (not start/end evidence)

- `prusaslicer/Raise3DTest_0.4n_0.2mm_PLA_PRO2PLUS_HS_DUAL_3h2m.gcode` — Dual profile export (2026-09-02)
- `prusaslicer/Base_0.4n_0.2mm_PLA_PRO2PLUS_HS_DUAL_2h0m.gcode` — later Dual export of the Base part (2026-09-23). Same profile; not a new start/end source.

## Community-derived (not Hyper Speed evidence)

From [Prusa Slicer Profile for Raise3D Pro2 dual head printer](https://forum.prusa3d.com/forum/prusaslicer/prusa-slicer-profile-for-raise3d-pro2-dual-head-printer/). Extracted INIs are in `community/extracted/`.

| Extracted folder | Author / date | What it is | Do not copy blindly |
| --- | --- | --- | --- |
| `Raise3D-PRO2-Plus` | rmeister, Jan 2022 | PrusaSlicer 2.4: left-only and dual-head, **0.6 mm**, PETG, `gcode_flavor = marlin`, `pause_print_gcode = M601`, printer_model leftover `MK3S` | Marlin, wrong nozzle, PETG, pre-Hyper Speed |
| `RaisePro2_v1_2202.02.18_PrusaSlicer_config_bundle` | izumi5188, 2022-02-18 | Left-extruder Pro2 (300 mm Z) Marlin bundle | Pro2 not Plus; expanded bed; Marlin |
| `RaisePro2_v1.1_2202.02.25_PrusaSlicer_config-izumi5188` | izumi5188, 2022-02-25 | Dual Pro2 Marlin bundle, `M2000` pause, `M1001`/`M1002` added | Dual/toolchange unverified on Hyper Speed Klipper |

Useful community facts (still not a substitute for ideaMaker):

- RaiseTouch may parse `;Dimension: … 0.400 0.400` for nozzle matching.
- `;Filament Name #1:` must match the name loaded on the printer.
- Hyper Speed firmware is Klipper; 2022 Marlin profiles are outdated for this conversion.
- `M600` is reported not to work; `M2000` is the community pause command.

## Missing evidence

- Short 20–30 minute PLA ideaMaker file
- ideaMaker printer/filament/template exports
- RaiseTouch version screenshot
- Pause / runout reference file
- Measured PLA flow, temp, and volumetric-speed results

## Do not include

Passwords, API keys, network credentials, serial numbers, or other private information.
