# Plasma

EZ-Router table on Mach3 with a THC301d torch height control and a Hypertherm Powermax 85. SheetCam jobs are grouped by the post that wrote them. The Fusion post and tool library are in `fusion-setup`.

## Layout

- `jobs/sheetcam-lscs/` — 40 programs from `LSCS plasma THC with scriber and backlash compensation R1.10.scpost`. This is the post the SheetCam setup sheet says to load.
- `jobs/sheetcam-mp1000/` — 6 older programs from `MP1000-THC.scpost`. These probe with `G28.1` in the file.
- `jobs/sheetcam-other/` — other posts. `Rack.tap` is `ez-Flame.scpost` and is the program that pierced repeatedly without eating the tip. The other three are `Plasma THC300` and Robotshop.
- `jobs/fusion/` — `Fusion Plasma Test.tap`. Mach3 Plasma post with Z output off, pierce height 0, and a 1.0 s delay. No Z words.
- `jobs/drawings/` — the two DXF files that were sitting with the jobs.
- `fusion-setup/` — `Fusion to mach3 plasma.cps.txt` and `LSU Plasma.tools` (the Powermax 85 library taken from the Hypertherm book).
- `reference/` — Mach3 install note, the SheetCam setup PDF, and `Mach1Lic.dat`.
- `vendor/ez-router-cd/` — the EZ-Router USB image (Mach3, manuals, cut charts, SheetCam tools). Left intact.
- `vendor/sheetcam-library/` — a second copy of the CD's SheetCam tools and posts. Same files except `HyperTherm-85_PlasmaTools.tools`, which is the shop tool table.

The LSCS post processor file itself is not in this folder. The setup PDF says to import it from the EZ-USB stick.

## Pierce

A working pierce rapids to 0.150 in, fires, dwells for the tool's pierce time, then feeds to a 0.060 in cut. `Rack.tap` does that on every start. The THC301d holds cut height after that. It does not lift the torch to pierce height.

`Fusion Plasma Test.tap` never commands Z, so the torch fires wherever it was left and the THC drives it closer. `LSU Plasma.tools` already has the book heights. The Mach3 Plasma post does not read them. For a 0.060 in cut, the post Pierce Height is 0.090 in (0.150 minus 0.060), Use Z axis is on, and Pierce delay is copied from the tool. The operation top height has to be the 0.060 in cut or the posted cut lands on Z0.
