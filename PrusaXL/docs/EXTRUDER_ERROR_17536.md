# Prusa XL error 17536: extruder motor is not spinning

Written 1 October 2026 for the two LSU Original Prusa XL 2-tool machines.
This is a field guide, not a Prusa bulletin. Prices and stock are from prusa3d.com on that date.

## The short version

The plastic covers were never going to end this. The red screen is a Trinamic driver fault on the dwarf board of the picked tool. A brief bad contact is enough to set it, and firmware 6.2.0 and later turns that fault into a fatal stop. There is still no resume.

These two printers are a matched early-2025 pair. They are not the 2023 launch batch, and they are almost certainly out of warranty. The connector design that causes this was still shipping in 2025. The purchase date explains the hardware generation. It does not mark a one-off bad week.

Confirmed on these machines: with 6.1.3 installed, the printer kept moving and the extruder put out nothing for nearly an hour. 6.1.3 has no 17536 check, so that run is the motor actually stopped, not a false alarm.

6.4.2 is what was on the red screen. It is not the current XL firmware. Current stable is 6.10.3 (25 Sep 2026). Install that. It still will not repair the cable. The 6.10.2 note "extruder motor not spinning after manual tool change" is a different bug: a tool picked or parked by hand while idle never got its extruder enabled. Update one machine, run the fan and loadcell selftests, then update the other. One 5-tool owner had those tests fail on 6.10.1 and 6.10.2 and went back to 6.4.2.

What to do, in order:

1. Flash 6.10.3 on one machine. If the selftests pass, flash the other. Get off 6.1.3 either way.
2. Log the next failure (section 6): which tool, whether the nozzle LEDs were strobing, and whether the fault follows the head or the dock.
3. Open a Prusa ticket with the serials, the invoice, the 6.1.3 result, and that log. Ask for `cable splitter-dwarf` replacements. Expect to pay.
4. Service the contacts once, including the short motor cable, then replace the long cable on the tools that come back. Stop adding stiffer clamps.

## 1. These machines

| | |
| --- | --- |
| Invoice | Prusa Research, payment ID 1734958507, issued 19 Feb 2025, due 26 Mar 2025 |
| Buyer | Louisiana State University, PO-0000294568, Conrad Freeman, 136 Atkinson Hall |
| What was bought | 2x Original Prusa XL, assembled, 2-tool, no enclosure. Plus 2 textured sheets. Total $6,330.39 |
| Nameplates | Manufactured 2025. SN25027027848 and SN25027027869 (21 serials apart, same run) |
| Firmware on the red screen | XL 6.4.2+12828 |
| Error | `Extruder motor is not spinning on tool 1`, code 17536, help page prusa.io/17536 |

Already tried, and already failed:

- Prusa's connector-cover replacement, more than once
- The community clamp that locks the plug down hard: [Secure XL Nextruder cable connector](https://www.printables.com/model/1124941-secure-xl-nextruder-cable-connector-solution)
- Isopropyl alcohol and compressed air on the contacts
- Firmware 6.1.3: the print continued, and that tool extruded nothing for nearly an hour

The 6.1.3 run settles the firmware question. That version never raises 17536. The axes kept going because the check did not exist, and the part came out hollow because the extruder had stopped. Covers and alcohol still leave fretted tin, the sandwich end of the long cable, the short dwarf-cheese cable, and the dwarf board itself on the list.

## 2. What the printer is actually measuring

The sentence on the screen is a label. The firmware is not watching the gear and deciding it stopped.

On current firmware the dwarf reads the extruder driver's GSTAT register (TMC register `0x01`) and, if any bit is set, reports `TMC_FAULT`. The main board turns that into red-screen 17536. GSTAT is a grab bag:

- driver error (open coil, short, overtemperature)
- charge-pump undervoltage
- a driver reset flag

An open motor wire and a power dip on the main cable look the same on the LCD. The flag sticks until the board reboots, which is why Reset often lets the next print start and the same job dies again later.

Since firmware 6.2.4 the dwarf only reports this when the tool is picked, not parked, and it waits one second after the pick. That filter is still in the 6.4.x source (`should_check_fault_status` in `src/puppy/dwarf/modbus/ModbusControl.cpp`, commit `aa98570`, ticket BFW-6869). On 6.4.2, "tool 1" means the tool that was picked, not a head sitting in the dock.

The check itself was added in 6.2.0. Before that, the same fault did not abort the print. These machines have already shown that: on 6.1.3 the gantry kept moving and the tool extruded nothing for nearly an hour. A short contact glitch can latch the driver off for the rest of the job, so that hour does not prove the plug stayed open the whole time. It does prove filament stopped. Current firmware still raises 17536 for that fault. Run 6.10.3 so the job stops when it happens.

There is no recovery path. Prusa has said so in the firmware tracker. Enhancement [#5267](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/5267) (open, comments through August 2026) asks for a retry instead of a dead print. It is not in 6.4.2. Power-panic is also a bad escape hatch on this firmware: 6.4.1's release notes still list "power panic resulting in a BSOD," and 6.4.2 did not claim to fix it.

## 3. Where the bad contact actually is

Each tool is its own computer. The dwarf board on the toolhead drives the extruder motor. A 2-tool XL has no splitter board. Tools 3–5 on a 5-tool are what the splitter is for. On these machines the path is:

```text
sandwich board
  -> cable splitter-dwarf          (long textile cable, a Click-Mate at each end)
    -> dwarf board                 (TMC driver lives here)
      -> cable dwarf-cheese        (short cable, another Click-Mate)
        -> extruder motor
```

The cover everyone reprints only touches the toolhead end of the long cable. Four other contacts can throw the same screen:

- the sandwich end of that same long cable
- both ends of the short dwarf-cheese motor cable
- a tired spring in any of those housings
- the dwarf board itself

Official part names and prices checked 1 Oct 2026:

| Part | What it is | Price | Notes |
| --- | --- | --- | --- |
| [Cable splitter-dwarf](https://www.prusa3d.com/product/cable-splitter-dwarf/) | Long tool cable | $25.90 | IDF 26888. Was out of stock that day. This is the cable support keeps sending. |
| [Cable dwarf-cheese](https://www.prusa3d.com/product/cable-dwarf-cheese/) | Short motor cable on the head | $5.49 | Easy to forget. Same pin problem. |
| [Extruder cable cover set](https://www.prusa3d.com/product/extruder-cable-cover-set/) | Current Prusa cover plus screws | $3.59 | IDF 15810. Includes the M3x10 screws and nuts. You already went past this. |
| [Dwarf board](https://www.prusa3d.com/product/dwarf-board/) | Toolhead controller | $52.90 | IDF 10412, board version 08. Replace only after a swap test points at the head. |

The sandwich board is the expensive next part, and only if both tools on one printer fail in a way that stays with the printer after the cables and heads have been swapped.

## 4. Why the covers and the alcohol did not stick

Two different stories are both partly true, and they contradict each other.

Prusa's help page says the fault is extra resistance because the cable and connector are held too firmly. Their instruction is to remove the dwarf-cover-connector, reprint without it, and if that helps, install the newer cover. Article: [EXTRUDER ERROR #17536 (XL)](https://help.prusa3d.com/article/extruder-error-17536-xl_822367). Guide: [How to replace the main cable connector cover (XL)](https://help.prusa3d.com/guide/how-to-replace-the-main-cable-connector-cover-xl_831370).

The community story, including the Printables clamp you installed and [this Reddit lock design](https://www.reddit.com/r/prusa3d/comments/1httjxn/solution_xl_nextruder_motor_stopping/), is that the plug walks out of the housing during tool changes, so it should be clamped harder.

People get a few good weeks from either change, then the error returns. That matches what you saw. A clamp can stop an unseated plug. It cannot repair a contact that has already fretted, and a clamp that cocks the plug makes Prusa's failure mode worse.

The pin plating is the part the covers never touch. The connectors are Molex Click-Mate with tin contacts. Tin on tin survives a single mating cycle because the spring wipes the oxide off. It does not survive thousands of micrometers of motion from tool changes, stepper vibration, and heat. Each slip exposes fresh tin, which becomes tin oxide. The oxide is hard and insulating. People on the firmware tracker call this fretting, and the debris looks like dark dust in the housing. Isopropyl alcohol dissolves grease. It does not scrape off that oxide, and compressed air does not either. Plug-and-unplug cycles do, until the spring itself is tired. Once the female contact has no drag on the pin, cleaning is temporary by definition.

A second, separate problem sits on top of the hardware. Firmware 6.2.0 started treating any GSTAT blip as fatal. Firmware 6.4.0 made a lot of XL owners miserable (phase stepping, layer shifts, tool crashes); Prusa pulled 6.4.0 for the XL in February 2026 and told people to go back to 6.2.6. Several of those people also had 17536, changed nothing mechanical, installed 6.2.6, and finished the job. See [issue #5037](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/5037). You are not on 6.4.0. You are on 6.4.2, which includes the 6.4.1 phase-stepping fix (20 April 2026) and a certificate fix (3 June 2026). Neither release note mentions 17536. So a downgrade is still a fair test. It is no longer the specific fix Prusa published for 6.4.0.

The Reddit thread you linked, [XL downgrade due to extruder motor not spinning](https://www.reddit.com/r/prusa3d/comments/1jxd2rc/xl_downgrade_due_to_extruder_motor_not_spinning/), is that downgrade conversation. The version numbers that are written down in a place that can be checked are the GitHub ones: 6.1.3 hides the check entirely, 6.2.4 stops the parked-tool false alarm, 6.2.6 is the last 6.2 release and the one people used to escape 6.4.0.

Nozzle LEDs are the useful tell:

- A fast strobe before the red screen means the dwarf is browning out or rebooting. That is the long cable or its connectors, not the motor.
- A steady LED, and the motor still faults, points at the short dwarf-cheese cable or the dwarf driver.
- A slow pulse while the hotend is heating is normal. Ignore that one.

## 5. Does February 2025 matter?

A little, and not the way a bad batch would.

Prusa's published warranty, from the [warranty article](https://help.prusa3d.com/article/warranty_2288) and the XL handbook:

- 24 months for consumers in the EU, Liechtenstein, Switzerland, Norway, and Iceland
- 12 months for EU businesses
- 12 months for everywhere else, including the United States
- Optional +1 or +2 years only if it was in the same cart as the printer

This invoice is a US university purchase order. No warranty-extension line is on it. Coverage runs from the day the goods arrived, not from the invoice date. Even if FedEx delivered in March 2025, the 12 months were over before summer 2026. As of October 2026 these printers are about half a year past standard warranty. Confirm the delivery date in case someone bought an extension on a different order. Do not expect a free board on warranty grounds. Do still open the ticket. Support has been shipping cables and dwarf boards for this exact screen, and out-of-warranty they will at least tell you which part they want replaced. The long cable is $26. A failed long print costs more.

On the hardware generation:

- Both plates say Manufactured 2025.
- The serials are 21 apart, and the invoice is two machines on one order. Same build.
- The new cover was already the public fix in January 2025 ([issue #4400](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/4400), guide linked 24 Jan 2025). February 2025 production is the revised-cover era of the same Click-Mate connector, not a new connector.
- The same red screen is documented on 2023 machines, on printers with under 50 hours, on year-old printers, and on 6.4.0 in December 2025 and again in user comments through June 2026. One owner in March 2025 got a new XL, printed fine on 6.1.3, flashed 6.2.0, and had 17536 within an hour. New cables did not stop it. New dwarf boards did not stop it. 6.1.3 printed the same multi-color job cleanly.

So this is not "we bought the bad week." It is the connector Prusa was still using when these were built, plus a firmware check that refuses to continue. Early-2023 machines had extra cable-routing problems on top of that. Yours can still fret the same pins. "It eventually hits every tool" is what a shared connector design looks like. One dead motor or one dead dwarf does not migrate across both heads on both printers.

## 6. Log this before swapping more parts

For the next three failures, write down:

- which serial, which tool number on the screen
- was that tool picked and extruding, or had it just parked
- were the nozzle LEDs steady or strobing in the minute before
- single-tool print, or a tool-change print
- roughly how long the print had been running, and whether the part fan had just come on (the original #4400 report died at the layer the fan started)
- anything you did to clear it, and whether the motor then extruded normally

Then one swap, power off first:

- Trade the two long cables between dock 1 and dock 2 on the same printer. Reprint the failing job.
- If the tool number on the screen stays with the dock, that cable or that sandwich port is the fault.
- If the tool number follows the toolhead, the dwarf, the short motor cable, or the toolhead-side contacts are the fault.
- Do not unplug a tool cable with the printer on. People have killed dwarf boards that way.

How to read the pattern:

| What you see | What it means | Do this |
| --- | --- | --- |
| Only dies on tool-change prints. Single-tool overnight prints are fine. | The long cable is being levered during the dock move. | Slack and routing first, then a new long cable. |
| LEDs strobe, then red screen, on the picked tool. | Power or data dip on the long cable. | Both ends of `cable splitter-dwarf`, then replace that cable. |
| LEDs steady, motor faults, follows the head. | Short motor cable or that dwarf. | Replace `cable dwarf-cheese` on that head. If it follows the head again, replace the dwarf ($52.90). |
| Print continues on 6.1.3 with a long stretch of no extrusion. Already seen here, nearly an hour. | The motor really stopped. | Stay on 6.4.2. Replace cables. Do not print on 6.1.3. |
| Both tools on one printer fail, and the fault stays with the printer after cables and heads move. | Sandwich side. | Then, and only then, talk to support about the sandwich board. |

## 7. The options

### A. Contact support with a real history

Do this even out of warranty. Chat or the form at [Customer support](https://help.prusa3d.com/article/customer-support_2287).

Give them:

- both serials, firmware `6.4.2+12828`, photo of the red screen
- invoice 1734958507 / PO-0000294568, and that it hits every tool over time on both machines
- the covers already fitted, including Printables 1124941, and that IPA did not hold
- the 6.1.3 result: print continued, no extrusion for nearly an hour
- the log from section 6, especially LED behavior and whether it follows the head or the dock

Ask for `cable splitter-dwarf` for the tools that actually fail, not a third cover. If the log says the head moves with the fault, ask about the dwarf and include `cable dwarf-cheese`.

Michele Moramarco from Prusa, on [#4400](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/4400) (14 Mar 2025), listed the pile they were still willing to blame: fatigued cable, dwarf, sandwich, splitter, "or even, rather unexpectedly, other pieces of hardware," and said remaining cases would be handled one by one. The splitter does not exist on a 2-tool. Hold them to the cable and the dwarf until a swap test says otherwise.

### B. Service the contacts

Scrubbing the contacts brought a tool back on 1 Oct 2026. Treat that as maintenance. The oxide grows back, and hard scrubbing wears the tin off faster the next time. Do this with the printer unplugged, on the long cable at both the toolhead and the sandwich, and on the short dwarf-cheese cable.

1. Feel the drag as you unplug. If a pin slides in with no resistance, the spring is done. Replace the cable. Chemicals will not put spring tension back.
2. Look for black or gray dust. That is fretting debris, tin oxide, not iron rust.
3. Spray DeoxIT D5 (the D5S-6 can) on the metal, valve on low, one short burst, and let it sit a minute. Keep it off the dwarf board. CRC electronic cleaner only rinses oil. It does not dissolve this oxide.
4. Agitate with a soft nylon brush, a toothbrush, or 10–20 mate/unmate cycles. A pencil eraser works on a flat pin and leaves rubber crumbs in this housing, so blow those out if you use one. No steel wool, no wire brush, no knife.
5. Leave a thin film of DeoxIT Gold G100L (the G100L-2C 2 ml tube) on the metal and mate the plug while it is still damp with that film. The tube is 100% concentrate, so a pinhead on a toothpick is enough for one connector. Wiping afterward with isopropyl alcohol strips the protection off. Use alcohol only if you flooded the housing and need to remove puddles.
6. Dry the plastic with compressed air before powering on. The metal film stays.
7. Dielectric grease goes on the plastic shell only, and only a wipe, to keep moisture off. Keep it off the pins. It is an insulator, and it does nothing about fretting. Skip it if you cannot keep it off the contacts. DeoxIT Gold on the pins is the protection that matches this failure.

Then fix the routing, which is free. The cable needs enough slack that a tool change does not pry the plug, and not so much that the bundle snags. One shop fixed a stubborn tool by taking the cable the other way around the PTFE tube so it stopped tugging the housing. Watch a tool change in slow motion and see whether the plug housing moves.

Put the official cover back on, seated the way the guide shows, not clamped harder than that. You already proved the secure clamp is not sufficient.

Expect this to last weeks or a couple of months if the springs are still good. It is maintenance, not a redesign. If the LEDs start a faint flicker again, do it before the next long print. Waiting for the red screen wastes the part.

### C. Replace the long cable, then the short one

This is the first part Prusa support actually sends, and it is the right first purchase if the springs feel loose or the LEDs strobe.

- `cable splitter-dwarf`, $25.90 each. Four tools across two printers is about $104 if you do all of them. Start with the tools that fail.
- `cable dwarf-cheese`, $5.49, on any head the fault follows.
- New cables still use the same tin Click-Mate. Owners report a quiet month, then flicker, then 17536 again, because the new pins start fretting too. One person in June 2026 said five new cables plus the new covers held "so far," and also said that if the old cover had already damaged the contacts, a new cover alone cannot save the old cable. Replace the cable and the cover together. Keep the old cable until the new one has survived a long tool-change print.

The long cable was out of stock on the Prusa shop on 1 Oct 2026. Printed Solid and other Prusa parts sellers carry the same IDF. Do not buy the MK4 "Nextruder main cable." That is the Loveboard cable for a different printer. It is about $18 and it will not fit this fault.

### D. Firmware downgrade

Already answered. On 6.1.3 these machines kept printing with a dead extruder for nearly an hour. That is the failure the Reddit downgrade threads hide.

Current XL stable is [6.10.3](https://help.prusa3d.com/changelog/xl) (25 Sep 2026), not 6.4.2. Install 6.10.3. The line in 6.10.2, "Fixed extruder motor not spinning after manual tool change," means a tool picked or parked by hand while the printer was idle did not get its extruder enabled. Prusa's note: a manual tool pick is now handled as a regular tool change. That is not error 17536 mid-print, and it does not touch the connector.

Update one printer first and run the fan test and the loadcell test. On 23 Sep 2026 a 5-tool owner reported both tests failing on 6.10.1 and 6.10.2 and reverted to 6.4.2. These are 2-tool machines without an enclosure, so they may not hit that. If the tests pass, flash the second machine. If they fail, 6.4.2 is the fallback that still aborts on 17536.

6.2.6 is only the old fallback from when Prusa withdrew 6.4.0. Do not use 6.1.3 for a real job.

### E. Replace the dwarf board on a head the fault follows

$52.90, [guide for multi-tool](https://help.prusa3d.com/guide/how-to-replace-a-dwarf-board-xl-multi-tool_549533).

Worth it only after the cables have been swapped and the fault still moves with that head. Support has sent dwarf boards for this error and, in more than one public case, the new boards failed the same way, because the cable was the real source. Replacing every dwarf on both printers is about $210 and does not change the connector.

A dwarf that was hot-unplugged is a different failure. If a tool cable was disconnected while the printer was powered, that board is a legitimate suspect even without the fretting story.

### F. Gold-plated connectors

This is the only change that attacks fretting instead of managing it. Tin oxide grows back. Gold does not, in this duty cycle.

It is also not a Prusa part. Nobody in the public record has posted a drop-in gold Click-Mate harness you can order, and Prusa has not changed the connector. Doing it means cutting and crimping both ends of a cable, on a machine LSU depends on, with a pinout you would have to take off the old cable. Get it wrong and the dwarf or the motor driver is what fails next.

Do this only after a new official cable has fretted again, and only on one tool, and keep the original cable. It will make the next support conversation harder if that tool dies for an unrelated reason. DeoxIT plus a new cable is the practical version of this idea. Gold is the permanent version, and it is a project.

### G. What not to bother with

- Another stiffer clamp, more screws, or hot glue on the plug. You are already past that experiment. Glue also makes the next cable swap worse.
- A new extruder motor as the first part. Support has sent motors for this screen and they did not change the outcome when the fault was the connector.
- A sandwich board, until section 6 says the fault stays with the printer.
- Pulling the power cord to force a power panic. On 6.4.2 that can end in a blue screen, and Prusa says the original fault comes back anyway.
- Unplugging tool cables live.
- Treating Reset as a fix. It clears the driver fault flag. It does not fix the contact that set it.
- Leaving 6.1.3 installed. The next failure will spend another hour laying down nothing.

## 8. What to do this week

Flash 6.10.3 onto one machine and run the selftests before the next job. Flash the second machine after those tests pass. Anything still on 6.1.3 comes off 6.1.3 first.

**On the machine that just printed air**

1. Power off. Do the contact service in section 7B on both tools: long cable at the toolhead and at the sandwich, plus the short dwarf-cheese cable. Count the drag on each pin.
2. Set the cable slack so a tool change does not move the plug housing. Official cover, not the secure clamp.
3. If any pin is loose, or the nozzle LEDs have been strobing, order `cable splitter-dwarf` for that tool now. Add `cable dwarf-cheese` if you are opening the head anyway.
4. Run the next job on 6.10.3. A red screen in the first hour is a failed cable, caught cheaply. An hour of missing plastic is the same failure caught late.

**On the other machine**

Same contact service when you next have it idle. Order cables for any tool that has already thrown 17536. Swap the two long cables between docks before you buy a dwarf board, so you know whether the fault follows the cable or the head.

**Support**

Open one ticket for both serials. Lead with the 6.1.3 result so they do not send you back to a cover reprint. Ask for `cable splitter-dwarf`. Link issue #4400 and the 17536 article.

## 9. Sources

Official:

- [EXTRUDER ERROR #17536 (XL)](https://help.prusa3d.com/article/extruder-error-17536-xl_822367)
- [How to replace the main cable connector cover (XL)](https://help.prusa3d.com/guide/how-to-replace-the-main-cable-connector-cover-xl_831370)
- [XL electronics](https://help.prusa3d.com/article/original-prusa-xl-electronics_686999) (2-tool has no splitter board)
- [Warranty](https://help.prusa3d.com/article/warranty_2288)
- [XL changelog](https://help.prusa3d.com/changelog/xl)
- [Customer support](https://help.prusa3d.com/article/customer-support_2287)

Firmware tracker:

- [#4400 Extruder motor still stops](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/4400) (opened Jan 2025, Prusa's hardware list)
- [#4467 error appeared moving from 6.1.3 to 6.2.0](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/4467)
- [#4576 17536 on a docked tool](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/4576) (fixed for parked tools in 6.2.4)
- [#4579 ask for retry instead of a reboot](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/4579)
- [#4932 ramming skips can trip the same screen](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/4932)
- [#5021 reseat both ends, oxide theory](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/5021)
- [#5037 6.4.0 red-screen, 6.2.6 finished the job](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/5037)
- [#5267 still open, April–August 2026, fretting write-up](https://github.com/prusa3d/Prusa-Firmware-Buddy/issues/5267)
- Commit [aa98570](https://github.com/prusa3d/Prusa-Firmware-Buddy/commit/aa985704bfeec67154790e0f08796e9803a2cb8e), "Dwarf TMC error is check only on selected active tool"
- [6.4.0 withdrawn for XL](https://forum.prusa3d.com/forum/original-prusa-general-discussion-announcements-and-releases/6-4-0-firmware-for-prusa-xl-2/) (5 Feb 2026, phase stepping; fallback 6.2.6)
- [6.4.1 release](https://github.com/prusa3d/Prusa-Firmware-Buddy/releases/tag/v6.4.1) (20 Apr 2026)

Community hardware:

- [Printables 1124941](https://www.printables.com/model/1124941-secure-xl-nextruder-cable-connector-solution), the secure clamp already on these machines
- [Printables 449554](https://www.printables.com/model/449554-xl-printable-parts), official XL printed parts, including the current cover
- [Reddit: XL downgrade](https://www.reddit.com/r/prusa3d/comments/1jxd2rc/xl_downgrade_due_to_extruder_motor_not_spinning/)
- [Reddit: lock the connector](https://www.reddit.com/r/prusa3d/comments/1httjxn/solution_xl_nextruder_motor_stopping/)
- [Forum: 17536 on a docked tool](https://forum.prusa3d.com/forum/original-prusa-xl-tool-changer-hardware-firmware-and-software-help/error-17536-on-a-docked-tool-now-confirmed-as-a-firmware-bug/)
