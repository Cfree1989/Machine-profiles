# Firmware / slicer notes from supplied files

## Confirmed from ideaMaker G-code

- ideaMaker **5.4.2.8790**
- `;Printer Type: RAISE3D Pro2 Plus - Hyper Speed`
- `;Firmware: Klipper`
- Hyper Speed marker: First line is `M99123` plus payload
- ideaMaker accel from `Compensation Test.gcode` (5.5.0.8810): `SET_VELOCITY_LIMIT ACCEL=5000` on walls/infill/first layer, `2000` on later solid/top. Older `MulticolorRaise3d.gcode` was 2000 print / 5000 travel because that job was solid-heavy. PrusaSlicer 2.9.6 Klipper flavor writes `M204 S` instead; `scripts/ensure_m99123_first.py` converts it and inserts next-tool `M104` before swap `M109`.
- `;Dimension: 305.000 305.000 605.000 0.400 0.400`

## Dual (experimental)

- Two nozzles: `nozzle_diameter = 0.4,0.4`
- Slicer `extruder_offset = 0x0,0x0` (printer hardware holds ~25 mm X)
- Tool change: `T0` / `T1` (electronic lift in firmware) plus `M109` wait
- Do not emit `M218`, `M116`, or Marlin `T… P0`

## Not present in supplied files

- RaiseTouch version
- ideaMaker Hyper Speed template export
- Screenshots of the selected printer / filament / template
- PLA ideaMaker slice (present: `[Raise3D] PLA` at 230 °C / 94% flow). PrusaSlicer PLA Raise3D is 215 °C first / 225 °C later / 100% flow (operator Ellis EM).

Add screenshots or notes here when available.
