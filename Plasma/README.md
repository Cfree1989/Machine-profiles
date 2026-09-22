# Plasma

EZ-Router table on Mach3 with a THC301d torch height control and a Hypertherm Powermax 85. SheetCam jobs are grouped by the post that wrote them. The Fusion post is `mach3 plasma.cps`. The tool library is `LSU Plasma.tools`.

## Layout

- `jobs/sheetcam-lscs/` — 40 programs from `LSCS plasma THC with scriber and backlash compensation R1.10.scpost`. This is the post the SheetCam setup sheet says to load.
- `jobs/sheetcam-mp1000/` — 6 older programs from `MP1000-THC.scpost`. These probe with `G28.1` in the file.
- `jobs/sheetcam-other/` — other posts. `Rack.tap` is `ez-Flame.scpost` and is the program that pierced repeatedly without eating the tip. The other three are `Plasma THC300` and Robotshop.
- `jobs/fusion/` — `Fusion Plasma Test.tap`. Mach3 Plasma post with Z output off, pierce height 0, and a 1.0 s delay. No Z words.
- `jobs/drawings/` — the two DXF files that were sitting with the jobs.
- `mach3 plasma.cps` — the Fusion Mach3 Plasma post, revision 44226, edited to read pierce height, cut height, and pierce time from the tool.
- `LSU Plasma.tools` — the Powermax 85 tool library taken from the Hypertherm book.
- `reference/` — Mach3 install note, the SheetCam setup PDF, and `Mach1Lic.dat`.
- `vendor/ez-router-cd/` — the EZ-Router USB image (Mach3, manuals, cut charts, SheetCam tools). Left intact.
- `vendor/sheetcam-library/` — a second copy of the CD's SheetCam tools and posts. Same files except `HyperTherm-85_PlasmaTools.tools`, which is the shop tool table.

The LSCS post processor file itself is not in this folder. The setup PDF says to import it from the EZ-USB stick.

## Pierce

A working pierce rapids to 0.150 in, fires, dwells for the tool's pierce time, then feeds to a 0.060 in cut. `Rack.tap` does that on every start. The THC301d holds cut height after that. It does not lift the torch to pierce height.

`mach3 plasma.cps` reads those three numbers from the tool on each operation. Pick the tool, post with that file, and the pierce is the tool's pierce height, its pierce time, then its cut height. The operation top height no longer has to be typed in as the cut height. A machine in the Fusion machine library should use this post so new setups do not open the generic Mach3 Plasma post.
