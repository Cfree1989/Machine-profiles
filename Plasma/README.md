# Plasma

EZ-Router table running Mach3, programmed in SheetCam, with one Autodesk Fusion test that damages consumables. The comparison is in the notes below. Cut files are grouped by the post processor that wrote them.

## Layout

- `jobs/sheetcam-lscs/` — 40 programs from `LSCS plasma THC with scriber and backlash compensation R1.10.scpost`. This is the post the SheetCam setup sheet says to load.
- `jobs/sheetcam-mp1000/` — 6 older programs from `MP1000-THC.scpost`. These probe with `G28.1` in the file instead of `M200`.
- `jobs/sheetcam-other/` — 3 programs from other posts (`Plasma THC300`, Robotshop), two of them in metric.
- `jobs/fusion/` — `Fusion Plasma Test.tap`. No post name in the file. It never commands Z.
- `jobs/drawings/` — the two DXF files that were sitting with the jobs.
- `reference/` — Mach3 install note, the SheetCam setup PDF, and `Mach1Lic.dat`.
- `vendor/ez-router-cd/` — the EZ-Router USB image (Mach3, manuals, cut charts, SheetCam tools). Left intact.
- `vendor/sheetcam-library/` — a second copy of the CD's SheetCam tools and posts. Same files except `HyperTherm-85_PlasmaTools.tools`, which is the shop tool table (Powermax 85, 45/65/85 A).

The LSCS post processor file itself is not in this folder. The setup PDF says to import it from the EZ-USB stick as `LSCS plasma THC with Scribe and Backlash Compensation`.

## What the files show

SheetCam jobs for 45 A mild steel pierce at 0.150 in, dwell for a thickness-specific delay (0.2 s on 14 ga up to 0.6 s on 1/4 in), drop to a 0.060 in cut height, then cut at a chart feed (about 270 IPM on 14 ga, 43 IPM on 1/4 in). Every LSCS pierce also calls `M200` before the torch fires. That macro is not in the vendor CD.

`Fusion Plasma Test.tap` fires the torch 101 times with `M3`, dwells 1.0 s, and cuts at 190 IPM. It contains no Z word, no touch-off, and no `M200`. A 1 second stationary arc at the wrong height is long enough to blow molten metal back into a 45 A nozzle. Once the orifice is damaged, later pierces stop transferring and the plate is lost. That matches the failure. SheetCam avoids it because height, delay, and feed all change with the tool.

The Fusion feed also does not match a thickness. 190 IPM is slow for the shop's 14 ga tool (270 IPM) and fast for 10 ga (100 IPM) and thicker.
