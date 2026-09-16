# PrusaSlicer print profiles

One folder per printer. Each folder is self-contained: vendor bundle, importable profiles, scripts, tests, and the G-code that profile was derived from.

| Folder | Machine | Status |
| --- | --- | --- |
| [Raise3D](Raise3D/README.md) | Pro2 Plus Hyper Speed, 0.4 mm dual | Experimental PrusaSlicer bundle |
| [Potterbot](Potterbot/README.md) | 3D Potterbot 9 (Duet 2 WiFi) | Experimental PrusaSlicer bundle (one printer, 1–10 mm nozzles; Clay / Clay Retract filaments; vase hollow / vase bottom / infill) |

Add a new printer as a sibling folder with the same layout (`vendor/`, `profiles/`, `docs/`, `reference/`). Do not put printer-specific G-code or post-process scripts at the repo root.

Each `vendor/<Vendor>/` folder carries the PrusaSlicer plater and wizard assets for that bundle: `<MODEL>_bed.stl`, `<MODEL>_texture.svg`, and `<MODEL>_thumbnail.png`. Copy the folder to `%APPDATA%\PrusaSlicer\vendor\` alongside the `.ini`/`.idx`; PrusaSlicer needs both the STL and the SVG to draw the plate. `tools/make_thumbnail.ps1` (PowerShell, `System.Drawing`) fits a photo into the 180 × 256 wizard size for any printer.

## Lab PC path

Clone or copy this repo to:

```text
C:\Repos\Prusa-Slicer-Print-Profiles
```

Raise3D print profiles call post-process scripts by that absolute path. If the folder lives anywhere else, edit `post_process` in `Raise3D/vendor/Raise3D.ini` (and the matching bundle) before slicing.

## Tests

```text
python -m unittest discover -s Raise3D/tests -v
python -m unittest discover -s Potterbot/tests -v
```
