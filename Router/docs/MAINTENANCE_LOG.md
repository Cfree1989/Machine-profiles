# Forest Scientific 4×8 router: maintenance log

Newest entry first. Record what was seen, what was changed, and the old value of every setting before it was changed. The current settings live in `reference/CNC ROUTER MACHINE PROFILE.docx`. Keep that file and this log in agreement.

| | |
| --- | --- |
| Machine | Forest Scientific 4×8 CNC router |
| Control | Velocity CNC 4.5.24, Signal Generator 501A (USB). Manual: `reference/Velocity CNC 4.5 Manual.pdf` |
| Drives | Steppers. X and Y rack and pinion, Z lead screw |
| Spindle | HSD AT/MT 1090, 4.5 kW, 18,000 rpm at 300 Hz, air cooled. AutomationDirect GS2 VFD, 0–10 V from Velocity |
| Fusion post | `forest scientific cnc router 2.cps` |

## 20 November 2026: Velocity contouring settings changed, X axis tightened

Changed in Velocity, Configuration menu:

| Setting | Where | Before | After |
| --- | --- | --- | --- |
| Continuous Contouring Feedrate Tolerance | Feedrate/Ramping | 100 in/min | X 50, Y 50, Z 20 in/min |
| Use Advanced Transitions | Feedrate/Ramping, Advanced | not recorded | On |
| Line Sequence Smoothing Factor | Feedrate/Ramping, Advanced | not recorded (manual default is 0, off) | 1 |
| Corner Delays | Motion Delays | not recorded | None |

Why: Velocity runs two moves as one smooth motion only if every motor's speed change at the join is under the contouring tolerance. Above it, the control ramps down to the Start/Stop feedrate and back up (manual pages 110–111). The manual gives the Start/Stop feedrate as the typical tolerance and warns that higher values lose steps on stepper drives. At 100 in/min, Z could take an instant speed jump of up to 50 in/min at the start of a hill, more than twice its 20 in/min Start/Stop. The new tolerances are the Start/Stop feedrates of each axis.

Mechanical: the X axis was found extremely loose and was tightened. Motion was much smoother afterward.

The settings and the X fix were done the same day, so this log cannot say how much of the improvement came from each.

Still to do:

- Check Y (rack and pinion) and Z (lead screw) for play the same way X was found.
- After a full 3D finish, re-probe Z zero on the plate. If it reads differently, Z is still losing steps. Next would be the Z contouring tolerance or the Z ramp rate, which at 5 in/s² is a quarter of X and Y.
- Step the NINA finish from 200 to 250, then 300 in/min, keeping 0.020 in per tooth (about 6,250 rpm and 7,500 rpm). Record the highest feed that cuts clean here.

## 19 November 2026: violent jerking on a 3D parallel finish in foam

Job: `NINA.nc`, Fusion Parallel finish, 3/8 in ball end mill, foam, 540 in/min at 18,000 rpm. The machine jerked hard enough to feel in the floor, mostly at the start of each hill in the surface. The foam came out gouged. Fusion estimated 14:43. Velocity showed 1 hr 26 min.

Cause: the program asked for more than this machine's configured limits allow. The profile limits are 400 in/min on X and Y, 100 in/min on Z, and 12 in/s² acceleration. At 540 in/min, roughly 700 to 1,640 joins inside the part failed Velocity's contouring check. Each one dropped to the Start/Stop feedrate (50 in/min X and Y, 20 in/min Z) and ramped back up. Z was also clipped at its 100 in/min limit on the steeper slopes. The manual calls Velocity's runtime estimate "very accurate," so the 1 hr 26 min was those stops being counted.

Air-cut tests on the machine, spindle off:

- `AIR-STRAIGHT.nc` and `AIR-CHOPPED.nc`, one 12 in line and the same line in 0.2 in steps: identical, smooth.
- `AIR-ARC.nc` and `AIR-ARCS.nc`, one large XZ arc and the same arc in 40 pieces: identical, smooth.
- `AIR-MICRO.nc`, the 12 in line in 0.001 in steps: paused a couple of seconds after M00, then moved in pulses.

Toolpath changes in Fusion:

- Tolerance 0.001 in, smoothing on, slope limited to 0–70°. Removed about 9,000 moves shorter than 0.001 in from the ends of the passes.
- Fusion Feed Optimization was tried at 150/540 in/min and made the jerking worse. It switched the feed about 1,900 times across the part. Each switch is a speed change Velocity has to ramp through. Leave it off on this machine.
- Final finish: 200 in/min at 5,000 rpm, 0.020 in per tooth (2 flutes). Jerking was much less violent. The surface was still marked, which led to the 20 November changes.

For 3D finishing, do not program a feed above the profile's 400 in/min X and Y limit. Keep the slope of the path in mind against the 100 in/min Z limit: at 200 in/min, a 30° slope already needs 100 in/min on Z.
