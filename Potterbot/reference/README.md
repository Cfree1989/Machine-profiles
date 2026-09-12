# Potterbot reference files

Sources the PrusaSlicer bundle was derived from. Do not slice from these.

| Path | What it is |
| --- | --- |
| `firmware/config.g` | Live Duet config (420 × 360 × 400, M83, cold extrusion). An older board dump used Z max 200. |
| `firmware/macros/` | Homing, pause/resume/stop as stored on the board |
| `cura/3D Potter Standard.3mf` | Official 3D Potter Cura project (Model 9 / Pro 9 / Super 9) |
| `cura/no_bottom__layers.gcode` | Cura 5.12 vase, 0 bottoms |
| `cura/Bottom_Layers.gcode` | Same model, 3 bottoms then vase |
| `cura/CFFFP_Test.gcode` | Lab Cura 5.12 job that printed well (7 mm walls) |
| `cura/screenshots/` | Lab Cura Fine 1.5 mm print-settings shots |
| `simplify3d/` | 2019 known-good Simplify3D jobs (5 mm nozzle, 6 mm width, 40 mm/s) |
| `duet-macros/` | Operator Prime / Retract / start-location buttons |
| `dwc/` | Duet Web Control screenshots (limits, firmware, workflow) |
| `manual/` | 3DP 9 full manual |

Not kept: Duet firmware `.bin` / IAP images, empty event logs, stock unused `bed.g` (delta example).
