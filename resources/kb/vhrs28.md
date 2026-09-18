# Etnyre Variable Width Hopper ChipSpreader VHRS28 — Voice Agent Knowledge Base

**Source Documents:** M-215-16 (Operation, Maintenance and Safety Manual, S/N K6975 and Up) + M-218-11R/M-218-19 (Troubleshooting Guide for ChipSpreaders)
**Manufacturer:** Etnyre International (E. D. Etnyre & Co.) | 1333 S. Daysville Road, Oregon, IL 61061 | Phone: 815-732-2116 | Toll-Free Parts/Service: 888-586-1899 | CustomerService@etnyre.com | www.Etnyre.com
**Controller:** RC 36 (also compatible with RC 28 — see wiring pin-out section)
**Purpose:** FAQ and troubleshooting reference for customer service voice agents answering inbound support calls about the Etnyre Variable Hopper ChipSpreader VHRS28
**Date Compiled:** 2026-08-07

---

## Section 1 — How to Use This Knowledge Base

This knowledge base is structured for voice agents handling inbound calls from equipment operators, site supervisors, and fleet managers using the Etnyre Variable Width Hopper ChipSpreader VHRS28. Every troubleshooting section is written as a step-by-step telephone walkthrough. Walk the caller through each numbered step completely before moving to the next. Ask the caller to confirm what they see or hear after each step. If a problem cannot be resolved by telephone, direct the caller to contact the Etnyre Service Department at 888-586-1899 or 815-732-2116.

Do not skip steps. The order matters: each step narrows the problem so later steps are only performed if earlier ones do not resolve it.

---

## Section 2 — Product Overview

### What the Machine Does
The Etnyre Variable Width Hopper ChipSpreader VHRS28 is a self-propelled, hydrostatic-drive chip spreading machine designed to apply aggregate (stone chips) to freshly emulsified road surfaces in a precise, controlled layer. It is used in chip seal (surface treatment) road construction and maintenance.

### Key Differentiator: Variable Hopper System
Unlike fixed-hopper models, the VHRS28 has two independently extendable front hoppers (left and right) that slide in and out to adjust the effective spread width. This allows a single machine to cover a full lane in one pass, do shoulder work with one hopper retracted, or patch small areas. Each hopper has its own gate, spread roll, auger, and conveyor system, all independently controlled and calibrated.

### Spread Width
The hoppers can be extended to cover a full road width or retracted for shoulder/patch work. Individual gate selector switches allow 1-foot increment control at the outer ends of each fully extended hopper.

### Aggregate Sizes Supported
Sand, 1/4" Chips, 3/8" Chips, 3/8" Gravel, 5/8" Chips, 1" Chips

### Controller
RC 36 (current production, S/N K6975 and up). Earlier units may have RC 28 controller — pin-outs for both are in Section 17.

### Drive System
Hydrostatic ground drive. Engine powers hydraulic pumps; hydrostatic motors drive front and rear axles. All machine functions except power steering and service brakes are electrically controlled. Turning the ignition key OFF while moving results in a violent stop.

### Major Systems on the Machine
1. Hydrostatic drive system (engine → pumps → front/rear drive motors)
2. Front variable-width hopper system — left hopper (gate, spread roll, auger, conveyor, hopper position)
3. Front variable-width hopper system — right hopper (gate, spread roll, auger, conveyor, hopper position)
4. Individual air-actuated gate system (1-foot increments, both hoppers)
5. RC 36 electronic controller and computer display
6. Hydraulic system — two variable-displacement auxiliary pumps (front and rear) + fixed-displacement gear pump
7. Air system (compressor, reservoir, oiler, water separator, valve banks for individual gates)
8. Hydrostatic parking brake system
9. Hydraulic seat positioner (optional)
10. Batwing hopper (optional)
11. Vibrator system (optional)
12. Traction boost system (optional)
13. Traction control / 4-wheel drive system
14. Engine cooling and DEF (Tier V) system
15. Truck hitch and hitch height system

### Engine
Cummins diesel engine (electronic, Tier III/IV/V depending on serial number). Minimum recommended speed: 900 RPM. High idle required for hydrostatic work. 12-volt electrical system; alternator output 13.5–15.0 V.

### Tire Pressures
Front: 55–60 PSI. Rear: 60–65 PSI. Never exceed maximum pressure indicated on the tire sidewall.

### Alarm Thresholds (Computer Monitored)
| Parameter | Alarm Point |
|---|---|
| Engine coolant temperature high | 240°F |
| Hydraulic oil temperature high | 180°F |
| Fuel level low | 10% (~7 gallons) |
| Battery voltage low | 12 V |
| Battery voltage high | 15 V |

---

## Section 3 — Warranty

**Coverage:** E. D. Etnyre & Co. warrants its new product to the original Purchaser to be free from defects in material and workmanship for a period of **twelve (12) months** after date of delivery to the original Purchaser.

**Remedy:** The Company's obligation is limited to repairing or replacing any defective part returned to the Company. The Company will NOT be responsible for consequential damages or any further loss by reason of such defect.

**Excluded Warranties:** The Company excludes all implied warranties of merchantability and fitness for a particular purpose. There are no warranties, express or implied, which extend beyond the description of the goods.

**What is NOT covered:**
1. Normal start-up services, normal maintenance services, or adjustments usually performed by the selling dealer, factory service representative, or customer personnel.
2. Any product purchased or subjected to rental use.
3. Any product or part showing improper operation, improper maintenance, abuse, neglect, damage, or modification after shipment from the factory.
4. Any product or part damaged or lost in shipment. Inspect for damage before accepting delivery and signing any documents.

**Transferability:** Not transferable — warranty is to the original Purchaser only.

**Transportation:** The warranty does not obligate the Company to bear the cost of machine transportation for warranty repair or replacement.

**Unauthorized Repairs:** Parts on which unauthorized repairs or alterations have been made are not covered. Components not manufactured by Etnyre are covered only to the extent of the original manufacturer's warranty.

**Shipping Address for Warranty Parts:**
E. D. Etnyre & Co.
1333 South Daysville Road
Oregon, Illinois 61061-9778
Phone: 800-995-2116 | Fax: 800-521-1107

---

## Section 4 — System Startup

### Pre-Start Checklist (Complete Before Every Engine Start)

1. Inspect tires for correct pressure — front 55–60 PSI, rear 60–65 PSI.
2. Check engine coolant level (refer to engine operator's manual).
3. Check engine oil level (refer to engine operator's manual).
4. Check hydraulic oil level — sight eye on hydraulic reservoir tank.
5. Check fuel level — display shows percentage; refuel if low.
6. Check Diesel Exhaust Fluid (DEF) level if Tier V engine (see Appendix E of M-215-16).
7. Grease all fittings per the Lubrication Chart (see Section 12 Maintenance Schedule).
8. Inspect machine for fluid leaks, loose bolts, improper hose routings.
9. Inspect conveyor belts for proper tension and tracking.
10. Verify hopper gate adjustment — 1/16" clearance between gate and spread roll when gate is closed.
11. Verify front hoppers are unlatched (or latched with safety chains if traveling).
12. Verify all guards, shields, and covers are in place.
13. Install locking control box cover if machine will be left unattended.
14. Chock wheels if on a grade.
15. Confirm all personnel are clear of the machine.

> **CAUTION:** Before operating the Chipspreader, make an inspection of the machine to be sure that the machine is in a safe condition to operate.

> **CAUTION:** Always place the mode selector switch in the "Park" position when the chipspreader is stopped to avoid accidental movement of the machine.

### Step-by-Step Startup Sequence

1. Verify Park/Drive switch (item 2 on panel) is in the **PARK** position. The engine will not start if the switch is in the Drive position.
2. Verify the Speed/Direction joystick (item 9) is in the **neutral** position. If started without the joystick in neutral, the machine will not move until the joystick is returned to neutral.
3. Turn the Throttle Run/Idle switch (item 37) to the **IDLE** position.
4. Turn the Power/Ignition switch (item 1) to the **ON** position to supply power to all systems.
5. Rotate the ignition switch further right to the **START** position to engage the starter. Release when the engine fires.
6. Observe computer display — the main screen should appear showing application rate setpoint, aggregate size, and speed setpoint.
7. Allow engine to idle for a brief warm-up (especially in cold weather).
8. Move Throttle Run/Idle switch (item 37) to the **RUN** position to bring engine to high idle. The hydrostatic system is designed to operate at high idle.
9. Before moving, move Park/Drive switch to **DRIVE**, then verify the joystick responds correctly.

> **WARNING:** Turning the ignition switch to "off" results in a violent stop. SHUT MACHINE OFF AND WAIT FOR ALL MOVEMENT TO STOP BEFORE LEAVING OPERATOR'S SEAT OR SERVICING. FAILURE TO DO SO COULD RESULT IN UNEXPECTED MOVEMENT AND CAUSE SERIOUS INJURY OR DEATH.

> **WARNING:** Selecting "park" while the chipspreader is moving results in a violent stop. Do not select "Park" unless the chipspreader is at a full stop.

### After Hydrostatic System Work — Special Startup Procedure

If any work was done that opened the hydrostatic circuit:
1. Jack the machine up and support securely on stands with all four wheels off the ground.
2. Disconnect the 50-pin connector at the engine so engine can only be cranked, not started.
3. Disconnect pump stroker at the pump.
4. Install 600 PSI gauge in port "G" on the drive pump.
5. Verify gate valve in suction tube is fully OPEN (counterclockwise). Do NOT attempt to start with gate valve closed — this causes cavitation damage.
6. Crank engine with starter until 40–60 PSI charge pressure is seen on gauge. Do NOT crank for more than 30 seconds. Wait at least 2 minutes before cranking again.
7. Reconnect the 50-pin connector.
8. Start engine normally; allow to idle for 10 minutes. Charge pressure may surge 50–500 PSI as system fills; this is normal. Pressure should settle to a steady reading.
9. Shut down engine; remove gauges; replace all plugs and caps. Recheck fluid levels after 15 minutes.

> **CAUTION:** Do not crank engine with gate valve closed. Doing so will cause damage to the hydraulic pumps.

---

## Section 5 — Operating Procedures

### Important Operating Rules Before Starting a Pass

1. Front hoppers should be fully closed and latched with safety chains when traveling between job sites. This avoids damage to the outer ends of the hoppers.
2. Keep machine on road or relatively uniform surface at all times to avoid loss of traction and possible damage to hoppers or conveyors.
3. Place truck gearshift in neutral as soon as the truck is connected to the spreader.
4. Under most conditions, the Chipspreader should tow the truck — not the reverse. On steep upgrades the truck may assist, but the Chipspreader must always be pulling the truck.
5. Do NOT push the Chipspreader with the truck.
6. Avoid roading (traveling) the machine with material in the hoppers if at all possible.
7. Always have a clearly understood means of communication (radio, hand signals, horn) between the Chipspreader operator and truck driver.

### Normal Chip Spreading Work Cycle (Making a Pass)

**Setup before the pass:**
a. Set the Aggregate Size switch (item 4) to the size of aggregate to be spread (Sand / 1/4" / 3/8" Chips / 3/8" Gravel / 5/8" Chips / 1" Chips). This must be set before calibrating or setting application rate.
b. Set the Application Rate switch (item 5) to the desired rate in lbs/yd². Or press a Memory button (items 33) to restore a preset.
c. Set the Speed Set Toggle Switch (item 3) to the desired spread speed in FPM.
d. Confirm the Gate/Spread Roll switch (item 10) is OFF (left side depressed).
e. Turn Left Gate Power switch (item 27) and Right Gate Power switch (item 29) ON to connect both hoppers.
f. Turn Left Spread Roll switch (item 28) and Right Spread Roll switch (item 30) ON.
g. Turn Left Auger Selector (item 31) and Right Auger Selector (item 32) to desired mode (ON/AUTO/OFF).
h. Turn Left Conveyor Selector (item 21) and Right Conveyor Selector (item 20) to desired mode.
i. Set hopper width using Left Hopper Position switch (item 25) and Right Hopper Position switch (item 26) — push left to extend left hopper; push right to extend right hopper. Use Individual Gate Selector switches (items 52, 53) for fine width adjustment.
j. Turn Individual Gates Master switch (item 51) ON and all Individual Gate Selector switches ON for normal full-width operation. Turn off outboard gate switches for shoulder work (each switch controls approximately 1-foot increments at the outer end).

**Making the pass:**
1. Move Park/Drive switch to DRIVE.
2. Push Speed/Direction joystick (item 9) smoothly to the full forward position to accelerate to the speed setpoint.
3. Upon reaching the starting line of spreading, depress the RIGHT side of the Gate/Spread Roll switch (item 10) fully to open the gates and start spreading.
4. The computer automatically adjusts gate opening to maintain the application rate as speed varies.
5. During the pass, monitor the aggregate level in the hopper. Use conveyors and augers to maintain even material distribution.
6. To clear a gate jam, depress the Left Gate Override (item 23) or Right Gate Override (item 24) pushbutton — this momentarily fully opens that gate. Release the button to return to set position.
7. Speed adjustments can be made mid-pass using the Speed Toggle switch; the application rate is automatically maintained.

**Ending the pass:**
1. Upon reaching the ending line, depress the LEFT side of the Gate/Spread Roll switch (item 10) fully to close the gates.
2. Return the joystick to neutral. The parking brake is automatically applied when the speed sensor reads zero.
3. If ending on a grade, use the brake pedal (item 56) to hold the machine while the parking brake sets.

### Variable Hopper Width Adjustment

- **Left hopper extension/retraction:** Left Hopper Position switch (item 25, main panel) — push LEFT to extend, push RIGHT to retract. Also available at front control box (item 57).
- **Right hopper extension/retraction:** Right Hopper Position switch (item 26, main panel) — push RIGHT to extend, push LEFT to retract. Also available at front control box (item 58).
- **Individual gate control:** With the Hopper at full extension, turning off Individual Gate Selector switches at the outboard end disables 1-foot gate increments. This allows precise width control for shoulder work without retracting the entire hopper.
- **Shoulder work tip:** When spreading only part of the hopper width, consider turning the spread roll off for the inactive portion to avoid unnecessary wear.

### Connecting to / Releasing the Supply Truck

**Connecting:**
1. Momentarily depress the Hitch Release Pushbutton (item 17 or 61 at front) to open the hitch.
2. Back the Chipspreader into the truck.
3. The hitch automatically closes and locks when it contacts the truck.

**Releasing:**
1. While driving forward, push the Hitch Release Pushbutton and simultaneously pull the joystick slightly rearward to create slack.
2. Push the joystick forward again while still holding the Hitch Release Pushbutton until the truck separates.
3. Release the Hitch Release Pushbutton.
4. If stopped with no slack: back up slightly to create slack, then drive forward while pressing the Hitch Release Pushbutton.

> **CAUTION:** The Traction Boost switch (item 55), if active, will prevent the Hitch Release from functioning. Deactivate Traction Boost before releasing hitch.

### Conveyor Operation

The rear conveyor gates should be set to deliver as much material as possible into the conveyor without spillage. The conveyor speed (adjustable 10%–99%) should be set to deliver slightly more aggregate to the front hopper than the amount being spread. When properly adjusted, conveyors should run approximately 80% of the time with the hopper at maximum width and the Chipspreader at maximum speed.

- **Manual (ON):** Conveyor runs continuously.
- **AUTO:** Power goes to the auto diaphragm switch on top of the conveyor hood. When the switch senses material, the conveyor shuts off; when it no longer senses material, the conveyor starts. This automatically maintains material level in the hopper.
- **OFF:** Conveyor stopped.

Both conveyors are independently controlled. Conveyor speed can be adjusted independently from the calibration screens.

---

## Section 6 — Control Panels and Controller

### Main Control Console (Items 1–55, Figure 1)

| Item | Control Name | Function |
|---|---|---|
| 1 | Power/Ignition Switch | OFF/ON/START. Rotating to OFF while moving causes violent stop. Engine will not start with Park/Drive in Drive position. |
| 2 | Mode Selector — Drive/Park | Park: disables joystick and applies parking brake. Drive: releases parking brake when joystick moves from neutral. Never select Park while moving. |
| 3 | Speed Set Toggle Switch | Sets the Chipspreader speed setpoint in FPM. Toggle up = increase; toggle down = decrease. Displays setpoint while stopped, actual speed while moving. |
| 4 | Aggregate Size Switch | Selects aggregate size: Sand, 1/4" Chips, 3/8" Chips, 3/8" Gravel, 5/8" Chips, 1" Chips. Must be set before calibrating material. |
| 5 | Application Rate Switch | Sets gate opening setpoint in lbs/yd². Toggle up = increase; toggle down = decrease. |
| 6 | Circuit Breakers | Light, Conveyor, Controller (accessory-powered). Horn, Gate, Motor (ignition-powered). Computer: separate 30-amp inline fuse, accessory-powered. |
| 7 | Computer Display Screen | 4-operator screens + calibration + setup screens. Shows application rate, aggregate size, speed, engine data, hours, and alarms. |
| 8 | Screen Scroll Switch | Scrolls through display screens. Push down = advance to next screen; push up = return to previous screen. |
| 9 | Speed/Direction Control Handle (Joystick) | Controls direction (forward/neutral/reverse) and speed. Full forward = 100% of setpoint speed. Full reverse = up to 1300 FPM. Neutral applies parking brake. |
| 10 | Gate/Spread Roll Switch (Thumb Switch) | Right side = opens gates/activates spread rolls (ON). Left side = closes gates/deactivates spread rolls (OFF). Gates close automatically below 30 FPM. |
| 11 | Turn Signal Selector | Push right for right turn, left for left turn. NOT self-canceling. |
| 12 | Left Turn Signal Indicator | Confirms left turn signal active. |
| 13 | Right Turn Signal Indicator | Confirms right turn signal active. |
| 14 | Hazard Flasher Switch | Push up = ON; push down = OFF. |
| 15 | Headlight Switch | Pull out = ON; push in = OFF. |
| 16 | Seat Shift Switch (Optional) | Hold right/left to move operator seat for convenience during chipping. |
| 17 | Hitch Release Pushbutton | Releases the truck hitch. Requires slack in hitch to operate. |
| 18 | Strobe Switch (Optional) | Push up = ON; push down = OFF. |
| 19 | Application Rate Computer | Inside control panel. Receives speed pickup and gate position feedback; controls gates to maintain set application rate. |
| 20 | Right Conveyor Selector | Bottom = ON (runs continuously). Middle = AUTO (diaphragm switch controls). Top = OFF. |
| 21 | Left Conveyor Selector | Same as item 20 for left conveyor. |
| 22 | Hitch Height Switch | Push up = raise hitch; push down = lower hitch. Cylinder holds height with spring float for vertical articulation. |
| 23 | Left Gate Override Switch | Depress to momentarily fully open left gate (clears jam). Release = returns to setpoint. |
| 24 | Right Gate Override Switch | Depress to momentarily fully open right gate (clears jam). Release = returns to setpoint. |
| 25 | Left Hopper Position Switch | Push LEFT to extend left hopper; push RIGHT to retract left hopper. |
| 26 | Right Hopper Position Switch | Push RIGHT to extend right hopper; push LEFT to retract right hopper. |
| 27 | Left Gate Power Switch | Connects/disconnects left hopper gate from Gate/Spread Roll thumb switch (item 10). |
| 28 | Left Spread Roll Switch | Connects/disconnects left spread roll from Gate/Spread Roll thumb switch (item 10). |
| 29 | Right Gate Power Switch | Connects/disconnects right hopper gate from Gate/Spread Roll thumb switch (item 10). |
| 30 | Right Spread Roll Switch | Connects/disconnects right spread roll from Gate/Spread Roll thumb switch (item 10). |
| 31 | Left Auger Selector | Bottom = ON. Middle = AUTO (auto switch at outboard end of left hopper controls auger). Top = OFF. |
| 32 | Right Auger Selector | Bottom = ON. Middle = AUTO (auto switch at outboard end of right hopper). Top = OFF. |
| 33 | Memory Selector Buttons (1–5) | Restores a saved preset combination of speed, application rate, aggregate size. |
| 34 | Memory Save Button | Press after adjusting values; then select a memory location (1–5) to save the preset. |
| 35 | Calibrate Switch | Used to calibrate material. Toggle up/down to adjust calibration values; press Save to store. |
| 36 | Traction Control Switch | Engages front axle torque transfer. Joystick must be in neutral to engage. Limits speed to 200 FPM while active. |
| 37 | Throttle Run/Idle Switch | IDLE position for engine start. RUN position for high idle (required for all work). |
| 38 | Throttle Increase/Decrease Switch | Fine RPM adjustment. Press up to increase RPM; press down to decrease. Minimum recommended speed: 900 RPM. Also scrolls engine fault codes when Engine Diagnostics switch (item 44) is ON. |
| 39 | Horn | Signals truck driver or warns of danger. |
| 40 | Batwing Switch | Push up = raise batwings; push down = lower. |
| 41 | Warning Light | Illuminates when any monitored function reaches its alarm point (high coolant temp, high hydraulic oil temp, low oil pressure, low voltage, low fuel). The display shows the specific alarm. |
| 42 | Filter Indicator (Charge Filter) | Lit when the charge pressure filter is clogged. Service immediately. |
| 43 | Auxiliary 12V Power | "Cigarette lighter" style port. Active when ignition is in ON or accessory position. |
| 44 | Engine Diagnostics On/Off Switch | With engine off and ignition ON, activates fault code reading. Stop light (47) flashes a code; warning light (48) illuminates when code is complete. Use throttle switch (38) to scroll additional codes. |
| 45 | Vibrator Auto Select Switch (Optional) | Places vibrators in auto mode — they cycle ON with gate activation for a set time (1–10 seconds, adjustable on timer inside panel) then shut off. |
| 46 | Vibrator Manual On/Off Switch (Optional) | Hold up to activate vibrators; automatically returns to OFF when released. |
| 47 | Engine Diagnostics Stop Light | If illuminated, shut down the engine immediately. Access fault code and call Cummins dealer. |
| 48 | Engine Diagnostics Warning Light | Indicates an engine issue to be investigated soon. |
| 49 | Emergency Stop Switch | Brings the Chipspreader to a controlled stop regardless of joystick position. Stops engine while maintaining electrical power. Reset by turning knob clockwise. Foot brake (56) remains active with E-stop engaged. |
| 50 | Computer Reset Switch | BOTH reset switches must be pressed simultaneously to reset the computer. Do NOT press while moving — violent stop will result. Bring machine to stop, place Park/Drive in Park, joystick in neutral before pressing. |
| 51 | Individual Gates Master Switch | Connects selected individual air gates to the thumb switch (item 10). Must be ON for gates to respond to thumb switch. |
| 52 | Left Hopper Gate Selector Switches | Selects which individual gates on the left hopper are active when thumb switch is ON. Controls approximately 1-foot-wide gate increments at the outer end of the hopper. |
| 53 | Right Hopper Gate Selector Switches | Same function for right hopper individual gates. |
| 54 | Hopper Raise/Lower Switch | Push up = raise hopper; push down = lower hopper. |
| 55 | Traction Boost Switch (Optional) | Activates a cylinder that pushes up on the hitch, increasing rear-wheel traction when attached to a truck. Do not activate when not connected to a truck. Hitch Release does NOT function while Traction Boost is active. |
| 56 | Brake Pedal | Service brake pedal. Assists hydrostatic braking. When applied while moving, destrokes pump — machine decelerates. Speed at moment of release becomes new setpoint. On grade, hold machine until parking brake sets. |

> **CAUTION:** Traction Boost may reduce braking efficiency of the truck.

### Computer Display Screens (Normal Operator Mode)

**Screen 1 — Main Operator Screen:**
```
20.0       3/8      400
lb/yd²     Chip     fpm
```
Application rate setpoint | Aggregate size | Speed setpoint (stopped) or actual speed (moving)

**Screen 2 — Engine Data:**
```
100°F      60 PSI      15%
WATER      OIL         FUEL
```
Engine coolant temperature | Engine oil pressure | Fuel remaining

**Screen 3 — Hydraulic and Electrical Data:**
```
100°F      2200 RPM    13.8 V
HYD OIL    ENGINE      BATTERY
```
Hydraulic oil temperature | Engine RPM | System voltage (battery when not running; alternator output when running — should be 13.5–15.0 V)

**Screen 4 — Hours and Distance:**
```
120.8         7550 FT
ENGINE        CHIPPED
```
Engine hours | Feet chipped (accumulates while gate thumb switch is active)

**Calibration Screens:** Accessed by pressing Calibrate switch (item 35) up or down. Shows LEFT CAL and RIGHT CAL screens for independent hopper calibration. See Section 8.

### Front Operator Control Box (Items 57–65, Figure 7)

| Item | Control | Function |
|---|---|---|
| 57 | Left Hopper Switch | Push left = extend; push right = retract left hopper. |
| 58 | Right Hopper Switch | Push right = extend; push left = retract right hopper. |
| 59 | Left Conveyor Pushbutton | Press = turns left conveyor ON independently. Release = returns control to Left Conveyor Selector. |
| 60 | Right Conveyor Pushbutton | Press = turns right conveyor ON independently. Release = returns control to Right Conveyor Selector. |
| 61 | Hitch Release Pushbutton | Same function as item 17 on main panel. |
| 62 | Left Auger Pushbutton | Press = turns left auger ON independently. Release = returns control to Left Auger Selector. |
| 63 | Right Auger Pushbutton | Press = turns right auger ON independently. Release = returns control to Right Auger Selector. |
| 64 | Left Gate Override Switch | Momentarily fully opens left gate to clear jam. |
| 65 | Right Gate Override Switch | Momentarily fully opens right gate to clear jam. |

> **WARNING:** Auger may start automatically at any time! Do not attempt to clear any jam with the engine running.

### Automatic Conveyor System (Ultrasonic/Diaphragm Switches)

In AUTO mode, a diaphragm switch on top of each conveyor hood senses material level in the hopper. If material is present, conveyor shuts off; when material level drops, conveyor starts. The switching distance can be adjusted:
1. Turn conveyor selector to AUTO position.
2. Hold A1 button until red light flashes.
3. Place object at desired switch-off distance from switch.
4. Press A1 button to save.
5. Repeat steps 2–4 for A2 button.

> **CAUTION:** Setting switching point too close or changing mode from desired setting may cause automatic switches to function improperly.

---

## Section 7 — Calibration

### Why Calibration Matters

The RC 36 computer controls gate opening based on the selected aggregate size and Chipspreader speed to deliver the set application rate. If the actual material applied on the ground differs from the setpoint, calibration corrects the computer's density factor for that aggregate type. Calibration is permanent (stored in non-volatile memory). Calibrating one aggregate type (e.g., 3/8" chips) updates ALL memory presets that use that aggregate.

### When to Recalibrate

- Before starting a new job with a different aggregate.
- When the application rate on the ground visually differs from the setpoint.
- After replacing a gate transducer (requires computer setup recalibration, not just material calibration).
- After replacing the joystick (requires joystick calibration in setup screens).
- The calibration process may need to be repeated for very accurate results (±2.0 lbs requires at least three averaged samples).

### Material Calibration Procedure (Left and Right Hoppers Independently)

**Before calibrating:** Verify both spread rolls are turning at 96 RPM. Set the aggregate size. Set the application rate setpoint (e.g., 20 lb/yd²). Set speed setpoint to approximately 300 FPM.

1. Place the supplied canvas on a flat surface with enough run-up distance for the Chipspreader to reach set speed.
2. With the control handle in full forward position for constant speed, maneuver the Chipspreader toward the canvas.
3. Activate the gate thumb switch approximately 10 feet before the material will hit the canvas (to ensure the gate is fully open).
4. Deactivate the thumb switch once the canvas is covered.
5. Weigh the material and canvas together. Weigh the empty canvas. Subtract to get lbs/yd².
6. Repeat a minimum of 3 times and average the values.

**Entering calibration values — Right Hopper:**
- Press the Calibrate switch up or down to access calibration screens.
- The screen reads: `0.0 lb/yd² / 95.6% / RIGHT CAL`
- If right hopper weighed 18.0 lbs and setpoint is 20.0 lbs (2.0 lbs light): Press and hold Cal switch UP (+) until lb/yd² reads 2.0. The RIGHT CAL percentage decreases as rate increases.
- Press SAVE to store. The screen resets to zero.

**Entering calibration values — Left Hopper:**
- Press Scroll switch DOWN to access LEFT CAL screen.
- The screen reads: `0.0 lb/yd² / 95.6% / LEFT CAL`
- If left hopper weighed 23.5 lbs at setpoint of 20.0 (3.5 lbs heavy): Press and hold Cal switch DOWN (−) until lb/yd² reads −3.5.
- Press SAVE to store.

**To exit calibration screens:** Press Scroll switch UP twice to return to main operator screen. The calibration only changes when the Save button is pressed — pressing Scroll exits without saving.

**Fine-tuning during work:** While chipping, if one side appears heavier or lighter, press the Cal switch, scroll to that side's calibration screen, adjust by 1–2 lbs, and press Save. The change takes effect immediately on the ground.

### Conveyor Speed Calibration (Computer Screens)

From main screen, press Cal switch to enter calibration screens, then Scroll DOWN past the hopper calibration screens:

- **Left Conveyor Speed:** Adjust with Cal switch (+5% or −5% per press). Normal range 10%–99%; typical use ~75–80% at maximum hopper width.
- **Right Conveyor Speed:** Same procedure.

### Auger Speed Calibration (Computer Screens)

Same screen navigation as conveyor speed, one screen below:
- **Left Auger Speed:** Adjust with Cal switch (+5% or −5% per press). Normal use ~75%.
- **Right Auger Speed:** Same procedure.

### Gate Transducer Calibration (Computer Setup Screens)

Access by holding Cal switch DOWN while turning ignition key ON:

**Right Gate NULL (closed position):**
- Must read 0.00 inches with gate fully closed.
- If not 0.00, set to 0.00 using Cal switch.

**Right Gate SCALE (full open position):**
- Must read 4.00 inches while right gate override is held depressed.
- If not 4.00, visually verify gate is fully open, then hold override and press Cal switch to set to 4.00 inches.
- When override is released, screen must go back to 0.00.

**Left Gate NULL and Left Gate SCALE:** Same procedure as right gate.

**Gate Open/Close Current Settings (Setup Screens):**
- RIGHT OPEN, RIGHT CLOSE, LEFT OPEN, LEFT CLOSE — all should be set to 0.900–0.950 amps.
- Too high: gates hunt (flutter) around desired opening.
- Too low: gates stop before reaching desired opening (inconsistent material delivery).

**Gate Open/Close Hold Distance (Variable Hopper Only):**
- GATE OPEN HOLD and GATE SHUT HOLD: Set to 18.0 inches. This delays the right gate opening/closing until the Chipspreader travels 18 inches, achieving a straight starting line.
- Adjustable to achieve a straight starting and stopping line. Left gate is not affected by this setting.

**Joystick Calibration (Setup Screens):**
1. Joystick in neutral → screen reads 0.0%. Press Cal switch.
2. Screen changes to "SETUP: JOYSTICK — Neutral — 2.4 volts." Press Cal to calibrate neutral.
3. Push joystick full forward (~4.4 V). Press Cal to calibrate forward.
4. Pull joystick full reverse (~0.7 V). Press Cal to calibrate reverse.
5. Press Scroll to move to next screen.

**After any setup change:** Scroll to SETUP: SAVE AND EXIT and press Save button to store all changes.

### Spreadroll Speed Adjustment (96 RPM Target)

**Right Spreadroll:**
1. Park/Drive switch in PARK. Right Gate and Right Spreadroll power switches ON.
2. Engine at high idle, push joystick slightly out of neutral, depress right side of thumb switch.
3. Time the spreadroll with stopwatch or tachometer to determine RPM.
4. To adjust: loosen jam wheel on spreadroll flow control valve (between conveyors). Turn adjusting knob clockwise to decrease RPM, counterclockwise to increase.
5. Re-tighten jam wheel.

**Left Spreadroll:** Same procedure using left gate and left spreadroll power switches and left spreadroll flow control valve.

---

## Section 8 — Troubleshooting — Machine Systems

### Q: The machine won't start / starter doesn't crank

Work through these checks in order:

**Step 1 — Check Park/Drive switch position:**
The engine will not start with the Park/Drive switch (item 2) in the DRIVE position. Confirm the switch is in PARK. This is the most common reason the starter does not crank.

**Step 2 — Check Emergency Stop button:**
The Emergency Stop button (item 49) may be pressed. Look for the large red mushroom-shaped button on the control panel. If it is depressed, twist the knob clockwise to reset it. Attempt to start again.

**Step 3 — Check circuit breakers and fuses:**
Check all circuit breakers on the control panel. Check the 30-amp inline fuse for the computer (accessory-powered). Check fuses for the Cummins Engine ECM controller — located near the power and ground distribution hub at the right rear corner of the Cummins engine (up to 4 fuses depending on engine size). Verify fuse size matches schematic. Replace with same size fuse only.

**Step 4 — Check inline fuse holders (if yellow rubber type):**
If equipped with yellow rubber-insulated inline fuse holders with glass fuses: pull the holder apart and confirm the ring is over the END of the fuse, not just touching the metal tip. A ring only touching the metal part of the fuse allows 12 VDC until a load is applied, then loses power. Ensure ring is tight with a good solder joint.

**Step 5 — Contact Etnyre:**
If starter still does not crank after checks above, there may be a failed relay or disconnected wire. Contact Etnyre service at 888-586-1899.

---

### Q: The starter cranks but the engine won't start

**Step 1 — Check display for ENGINE CAN message:**
Look at the computer display. If it shows "ENGINE CAN" or "NO CAN COMMUNICATION," the engine ECM is not communicating with the display computer. Proceed to Step 2.

**Step 2 — Verify Tier 4/5 monitor engine data (if equipped):**
Check if the Tier 4 monitor is receiving engine data from the Cummins ECM. If NO data is shown, proceed to Step 3 (fuse check). If data IS showing, proceed to Step 4.

**Step 3 — Check Cummins engine ECM fuses:**
Fuses are located near the power and ground distribution hub at the right rear corner of the Cummins engine. Check all (up to 4) fuses. Verify size and connections per schematic. Replace with identical size fuse. Inspect all connections — clean, repair, or replace as needed.

**Step 4 — Check E-stop switch and fuel solenoid:**
Inspect the Emergency Stop switch connections. Check for an issue with the fuel solenoid portion of the E-stop switch. A failed fuel solenoid on the switch or on the Cummins engine will prevent fuel from reaching the engine.

**Step 5 — Check engine fuel solenoid/pump:**
Contact Etnyre service at 888-586-1899 for further diagnosis of the Cummins fuel solenoid or fuel pump.

---

### Q: The machine will not move / won't drive

**Step 1 — Check start latch:**
The computer has a start-latch safety that prevents movement after computer startup. Place the Park/Drive switch in PARK, then place the joystick in neutral. Move Park/Drive switch to DRIVE. Now move the joystick — the machine should respond.

**Step 2 — Check speed setpoint:**
The speed setpoint may be set too low. Raise the setpoint by pushing the Speed Toggle Switch up or by pressing a Memory button. The display shows the new setpoint while changing.

**Step 3 — Check brake pressure switch:**
The brake pressure switch may be stuck or failed. To test: Turn machine off. Unplug the electrical connector on the brake pressure switch (located on the hose from the foot pedal). Start the machine and attempt to move. WARNING: with the brake pressure switch unplugged, the service brake alone will not stop the machine. If the machine moves after unplugging, replace the brake pressure switch.

**Step 4 — Check for Joystick Fault:**
Check the display for "ALARM: JOYSTICK FAILURE." If shown, see the Joystick Fault section below.

**Step 5 — Check for pump solenoid fault:**
If the machine moves forward but the display shows "PUMP REVERSE SOL FAILURE" when attempting reverse, there is an electrical disconnect between the computer and pump or between pump and ground. If it moves reverse but shows "PUMP FORWARD SOL FAILURE," same diagnosis. Find and repair the loose or broken connection.

**Step 6 — Check charge pressure:**
Install a 1000 PSI gauge in port "G" on the drive pump. With engine at low idle, charge pressure should read approximately 400 PSI. If reading is near 0 PSI, the charge pump has failed. Contact Etnyre service at 888-586-1899.

---

### Q: Machine speed is limited to 200 FPM and I can't increase it

**Step 1 — Check Traction Control switch:**
The Traction Control switch (item 36) is a maintained switch that may have been left ON unknowingly. This limits speed to 200 FPM whenever the machine is next stopped. Turn the Traction Control switch OFF. Attempt to increase speed above 200 FPM.

**Step 2 — Check right spreadroll switch connector:**
Turn the right spreadroll switch OFF. If speed can now be raised above 200 FPM, there is an internal connector problem — the traction control and right spreadroll switch inputs are adjacent to each other in the computer connector. Remove the computer connectors completely, reconnect them, and check again. If problem persists: remove the input pins for the traction control switch and right spreadroll switch. Inspect wire crimps for loose strands. Reinstall pins securely.

---

### Q: Machine speed is limited to 400 FPM (4WD) or 600 FPM (2WD) — can't go faster

These limits indicate one of three fault conditions:

**Step 1 — Check for ENGINE CAN alarm:**
Scroll the display to the engine screen. If engine is running but RPM shows 0, there is a lost connection between the engine ECM and the computer. Check the engine CAN communication harness for a broken connection or wire.

**Step 2 — Check for FRONT MOTOR SOL FAILURE alarm:**
Enter the service screens (hold Scroll switch while turning ignition ON). Scroll to "SERVICE: Front Motor." The status should read approximately 0.40 amps. If it reads 0.00 amps, there is a disconnection between the computer and the front drive motor solenoid. For 4WD units, also check "SERVICE: Rear Motor."

**Step 3 — Check for SPEED SENSOR FAILURE alarm:**
See the speed sensor failure section below.

---

### Q: The speed sensor alarm is showing / machine comes to a stop with a speed error

When a speed sensor fault occurs, the machine comes to a stop. The operator must bring the joystick to neutral and move it out of neutral to resume at the reduced speed. The computer must be reset and the fault corrected to resume normal operation.

**Step 1 — Check circuit breakers:**
Reset any tripped circuit breakers on the control panel.

**Step 2 — Inspect the speed sensor connector:**
The speed pickup is located on the front drive motor. Check the connector for looseness or corrosion. Inspect all wiring between the speed pickup and the computer.

**Step 3 — Check voltage at speed sensor connector (connector disconnected):**
- Wire #1: 12 VDC
- Wire #2: Ground
- Wire #3: Speed signal — check continuity
- Green/Yellow wire: Direction signal — check continuity

**Step 4 — Check voltage at control box (connector connected):**
- Wire #1: 12 VDC
- Wire #2: Ground
- Wire #3: Speed signal — should read 4–7 VAC while machine is moving
- Green/Yellow wire: Direction signal — 0 VDC forward, 12 VDC reverse

**Step 5 — Check wiring at computer connector:**
RC 36 computer:
- Speed signal: pin 2-13
- Direction signal: pin 1-41

---

### Q: The machine keeps shutting off unexpectedly / Uncommanded Motion Detection (UCMD) alarm

**UCMD Direction error (engine shuts down, fast alarm beeping, "ENGINE CAN" displayed):**
The speed pickup shows the machine moving in the opposite direction from what the computer is commanding. This is usually caused by the speed pickup being wired incorrectly or a broken connection. Correct or repair the electrical connections at the speed pickup. See the pin-out section for correct wiring.

**UCMD Speed error (engine shuts down when slowing to a stop):**
1. The joystick may be out of calibration. Enter setup screens and recalibrate the joystick.
2. The joystick neutral microswitch may need adjustment. When the machine slows to stop, the computer commands a stop. But if the neutral microswitch on the joystick holds the parking brake off, the machine continues moving. When the computer detects this motion, it shuts down the engine. Solution: Remove the joystick from the housing. Adjust the microswitch away from the notched plate.

---

### Q: Joystick fault alarm is showing

**Step 1 — Check circuit breakers:**
Reset any tripped circuit breakers. The joystick requires both supply power (+5 V) and a clean ground.

**Step 2 — Check joystick calibration:**
Enter setup screens (hold Cal switch while turning ignition ON). Navigate to SETUP: JOYSTICK. Recalibrate the neutral, full forward, and full reverse positions as described in the Calibration section.

**Step 3 — Check reverse switch wires:**
The computer must see the reverse switch signal within 2 seconds of moving in reverse. If it does not, a joystick fault is triggered. Also, if the reverse switch signal is present when moving forward, a fault is triggered. Check the reverse switch wire connections.

---

### Q: The conveyor won't move

**Step 1 — Check for stalled conveyor belt:**
You should hear noise from the hydraulic pump if the belt is jammed. Turn conveyor speed to 100%, then cycle the conveyor switch ON and OFF several times rapidly to break the belt free. If belt is off-center, re-center it on the head and tail pulleys. Lower the cutoff plate in the rear hopper if material bridging is the cause.

**Step 2 — Check conveyor speed setting:**
Adjust the conveyor speed to a higher percentage on the calibration screen. Normal use is around 75%.

**Step 3 — Check for start latch:**
Move the joystick to neutral and place the Park/Drive switch in PARK. The conveyor switch should now function properly.

**Step 4 — Check auto switch (if in AUTO mode and conveyor won't start):**
- Ensure material is not present in the conveyor hood blocking the auto switch from sensing an empty state.
- Check the auto switch distance setting (it may be set too far or too close).
- Check that the electrical signal from the auto switch is returning to the computer (inspect wiring connections).
- The auto switch may need to be reset: follow the ultrasonic switch reset procedure in the Operations section.

**Step 5 — Check for conveyor solenoid failure:**
There may be an electrical disconnect between the computer and the conveyor solenoid. Find and repair the loose or broken connection.

---

### Q: The auger won't move

**Step 1 — Check for stalled auger:**
You should hear noise from the hydraulic pump if the auger is jammed. Turn auger speed to 100%, then cycle the auger switch ON and OFF several times to break it free. WARNING: Do NOT attempt to clear a jam manually with the engine running.

**Step 2 — Check auger speed setting:**
Adjust auger speed to a higher percentage on the calibration screen. Normal use is around 75%.

**Step 3 — Check for start latch:**
Move the joystick to neutral and place the Park/Drive switch in PARK. The auger should now function properly.

**Step 4 — Check auto switch (if in AUTO mode):**
- Check the auto diaphragm switch for holes in the diaphragm (most common failure).
- Ensure material is not touching the switch.
- Check that the electrical signal from the auto switch is returning to the computer — inspect connections.

---

### Q: The gates won't open or operate

**Step 1 — Check gate arming switches:**
Confirm that the Left Gate Power switch (item 27) and Right Gate Power switch (item 29) are turned ON. These switches connect the gates to the thumb switch. Without them ON, the thumb switch cannot open the gates.

**Step 2 — Check all circuit breakers:**
Check all circuit breakers on the control panel. Also confirm there is power to both sides of the circuit breaker assembly. Check the Gate circuit breaker specifically.

**Step 3 — Test gate with override button:**
Depress the Gate Override pushbutton (item 23 for left, item 24 for right).
- If the gate DOES move with override: the problem is electrical — go to Step 6.
- If the gate does NOT move with override: the problem is hydraulic — go to Step 5.

**Step 4 — Check computer output commands:**
Enter the Service Screens (hold Scroll switch while turning ignition ON) to monitor gate switch inputs in real time. The service screen for each gate will show "Activated" or "De-activated" to confirm whether the computer is receiving and responding to gate commands.

**Step 5 — Check hydraulic gate valve (if no movement even with override):**
Manually override the gate solenoid valve spool to test hydraulic operation.
- If gate moves with mechanical override: problem is electrical — go to Step 6.
- If gate does NOT move with mechanical override: problem is hydraulic. Check hydraulic pressure per the procedures in the Hydraulic Pressure Adjustment section of M-215-16 Appendix D.

**Step 6 — Check gate transducer:**
Refer to the Gate Transducer check procedure below. An out-of-range or misadjusted transducer will prevent gate operation.

**Step 7 — Check gate null/scale calibration:**
Enter computer setup screens and verify RIGHT GATE NULL = 0.00" and RIGHT GATE SCALE = 4.00" (left gate same). Recalibrate if needed per the Calibration section.

**Step 8 — Check joystick center roller microswitch:**
Confirm the thumb switch (gate/spread roll switch on top of joystick handle) is activating properly.

**Note on right gate hold feature:**
The right-hand gate uses a gate hold feature (set to 18 inches in setup). If the FPM reading is malfunctioning, the gate hold feature may prevent the right gate from opening. To operate in manual mode (e.g., for cleanout or hand work), set GATE OPEN HOLD and GATE SHUT HOLD to 0 in the computer setup screens.

---

### Q: The gates are hunting / unsteady / fluctuating and not holding position

**Step 1 — Check gate current settings:**
Enter computer setup screens. Find: RIGHT GATE OPEN, RIGHT GATE CLOSE, LEFT GATE OPEN, LEFT GATE CLOSE. All values should be set between 0.9 and 1.0 amp using the CAL switch.
- Too high (above 1.0 amp): Gates flutter and cannot find the desired position.
- Too low (below 0.9 amp): Gates stop before reaching the setpoint — material delivery becomes inconsistent.
- Ideal: Highest value that still allows the gate to settle on the desired opening without hunting.

---

### Q: The gates are making a very loud noise when the gate master power is turned on or off

This indicates the air gates are out of adjustment relative to the hydraulic buss bar:

**Step 1 — Identify whether it's an air gate problem or hydraulic buss arm problem:**
- If air gate out of adjustment: follow Step 2.
- If hydraulic buss arm not operating: follow Step 3.

**Step 2 — Adjust air gates:**
a. Back off hydraulic gate arm adjustment screws between all hydraulic gate buss arms and air gates.
b. Adjust air gate adjustment screws to achieve a uniform 1/16" gap across the spreadroll. Ensure air pressure is applied to the gate, forcing it closed, during this adjustment.
c. Check all buss arm assembly bolts — tighten any loose bolts; replace bent or broken bolts.
d. Calibrate gate (null/scale) in computer setup.
e. With machine running and hydraulic pressure applied to buss arm, turn gate master power ON and all individual air gate switches ON, allowing air gates to open to the hydraulic buss arm.
f. Adjust hydraulic gate buss arm adjustment screws, forcing air gates closed until the air gate adjustment screws touch the stop. Do NOT force screws past contact with the stop — this will change the gate transducer setting.
g. Verify null is still 0.00 and scale is still 4.00.

**Step 3 — Adjust hydraulic gate buss arm:**
a. Calibrate gate (null/scale) in computer setup.
b. Refer to the Gate Transducer checking procedure and adjust transducer if needed.

---

### Q: The spread roll speed is fluctuating

**Step 1 — Check auxiliary standby pressure:**
If standby pressure is too low, the pump will not come on stroke quickly enough, causing insufficient pressure and flow to the spread roll. The standby pressure target is 400 PSI. Check and adjust per the procedure in M-215-16 Appendix D.

**Step 2 — Check and adjust spread roll RPM at flow control cartridge:**
On variable width hopper units, the flow control cartridge is in the auger/spread roll manifolds. Left and right spreadrolls have separate cartridges (see Figure 31). Target is 96 RPM. Adjust per the spreadroll speed adjustment procedure in the Calibration section.

**Step 3 — Remove and inspect spread roll flow control cartridge:**
Remove the cartridge and inspect for contamination or debris. Clean or replace as needed.

**Step 4 — Monitor standby pressure while spread roll runs:**
Watch whether spread roll speed follows pressure changes. If speed decreases as pressure decreases, proceed to Step 5.

**Step 5 — Check load sense check valves:**
Remove the two load sense check valves located on top of the auger/conveyor/spreadroll manifold. Inspect for contamination, debris, worn spring, or pitted seat assembly. Replace if needed.

---

### Q: The hydraulic pressure is fluctuating / standby pressure is unsteady on the gauge

This occurs when the volume of oil in the load sense system is too great, caused by a missing or contaminated orifice or load sense check valve.

**Step 1 — Check the orifice in the load sense line fitting:**
The orifice fitting is attached to the auxiliary hydraulic pump(s) load sense compensator valve. It is a set screw installed in a side fitting with a 0.040-inch hole drilled through it. Verify:
a. Orifice is installed in the fitting.
b. Orifice is not clogged.
c. Orifice size is correct (0.040 inch).

**Step 2 — Check compensator operation:**
Ensure pressure responds to hydraulic system demand. Check and set standby pressure per the operations manual procedure.

**Step 3 — Isolate and test load sense lines:**
With engine off, remove the load sense lines from the compensators and cap them. Set standby pressure. If standby pressure is now steady, proceed to Step 4.

**Step 4 — Identify the problematic manifold block:**
Reconnect load sense lines one at a time. When reconnecting a line causes pressure to fluctuate, that manifold block contains the contaminated or bad load sense check valve. Remove and inspect the check valve. Replace if needed.

---

### Q: The hydraulic oil is overheating

**Step 1 — Verify actual temperature:**
Use a laser probe or mechanical thermometer to confirm hydraulic oil temperature is actually above 180°F. The display shows the computed temperature from the sender — use an independent reference to confirm.

**Step 2 — Check oil level:**
Check the hydraulic oil level at the sight eye on the reservoir tank. Low oil level causes overheating.

**Step 3 — Clean the hydraulic oil cooler:**
Inspect the front of the cooler for accumulated debris, dust, or asphalt. Clean to allow maximum airflow.

**Step 4 — Check fan speed and airflow:**
With engine at full throttle and hydraulic oil hot, unplug the fan valve electrical connector.
- If fan speed INCREASES: there is an electrical problem. Check the temperature switch in the hydraulic tank — this switch should close (activating the fan valve) when tank temperature is above 140°F. Check the temperature switch wires in the engine harness.
- If fan speed does NOT increase: there is a hydraulic problem. Check: (a) fan valve not shifting completely; (b) damaged gear pump; (c) damaged fan motor. Contact Etnyre at 888-586-1899.

**Step 5 — Check for filter restriction:**
The pop-up indicator is located on top of the filter head. If it has popped up, the return filter is clogged and must be replaced.

**Step 6 — Check pump orifice in load sense line:**
If the orifice screen in the load sense line is plugged, the pump will remain at high pressure and generate heat. On variable hopper machines, hold the hopper-in switch until the pump is heard at high pressure. This noise should decrease quickly when released. If it does not, see the "Auxiliary Hydraulic Pressure Will Not Relieve" section below.

**Step 7 — Check standby and high pressure:**
Check standby pressure (target 400 PSI) and high pressure (target 3000 PSI) per M-215-16 Appendix D procedures. Pressures above specification generate excessive heat.

---

### Q: Auxiliary hydraulic pressure will not relieve / engine is hard to start after shutdown

**Step 1 — Shut off machine and close main suction valve.**

**Step 2 — Locate and cap the case drain at the pump.**

**Step 3 — Remove the compensator from the hydraulic pump(s).**

**Step 4 — Remove the load sense compensator cartridge.**

**Step 5 — Locate the 2mm Allen head orifice inside the compensator housing.**

**Step 6 — Remove the orifice and clean it:**
Use a strand of primary wire or a torch cleaning kit (if small enough) to clean the orifice passage. DO NOT enlarge the orifice.

**Step 7 — Reinstall orifice, cartridge, and compensator.**

**Step 8 — Uncap and reinstall the case drain hose.**

**Step 9 — Open the suction valve.**

**Step 10 — Pressurize the hydraulic tank:**
Install an air regulator to the hydraulic tank through the vent filter connection. Apply 3–5 PSI to push out any trapped air. Start the machine and operate all hydraulic functions to circulate oil. Check and adjust pressures per M-215-16 Appendix D.

---

### Q: The display says "ETNYRE NO COMMUNICATION" or is showing nothing

**Display shows "ETNYRE NO COMMUNICATION":**
The signal from the computer is not reaching the display.
- Check the green and yellow wire connections between computer and display.
- Check the fuse to the computer (30-amp inline fuse, accessory circuit).
- Check power (+12 V) and ground connections to the computer.

**Display shows nothing (completely blank):**
- Check power and ground to the display unit itself.
- Check the ignition switch position (must be in ON).

---

### Q: The fuel level alarm keeps going off but the tank isn't empty

**Step 1 — Confirm actual fuel level:**
Visually check the fuel tank. If tank is not low, proceed to Step 2.

**Step 2 — Check for metallic debris on sending unit:**
Metallic debris lying on top of the sending unit can alter its resistance reading, causing a false alarm.

**Step 3 — Check wiring connections:**
Check for loose or bad connections, including any frayed wire that may be touching ground.

**Step 4 — Disconnect the wire from the sending unit:**
- If the alarm STOPS when the wire is disconnected: the sender or its wiring has a problem. Measure sender resistance at empty/full positions per the calibration table:
  - Empty: 240–260 ohms
  - Full: 27.5–39.5 ohms (nominal 33.5 ohms)
- If the alarm CONTINUES when the wire is disconnected: proceed to Step 5.

**Step 5 — Check wiring between sender and computer:**
Inspect the full wire run for damage, shorts, or loose connections.

**Step 6 — Check computer connections:**
Check for loose connectors at the computer. Check terminal P2-PIN19 specifically.

---

### Q: Water temperature alarm is showing / engine is overheating

**Step 1 — Verify temperature with independent gauge:**
Use a laser probe or mechanical thermometer to confirm coolant is actually exceeding 240°F. This confirms the alarm is not a sender problem.

**Step 2 — Clean the radiator:**
Inspect and clean the front of the radiator fins. Accumulated debris severely reduces cooling capacity.

**Step 3 — Check engine coolant level:**
Check the coolant reservoir and radiator. Low coolant level is the most common cause of overheating.

**Step 4 — Check for coolant leaks:**
Inspect all hoses, clamps, and fittings for leaks. Look for dried coolant residue indicating a past leak.

**Step 5 — Check fan operation:**
With the water temperature hot and engine at full throttle, unplug the connector at the fan valve.
- If fan speed does NOT increase to full speed: there is a hydraulic problem — valve not shifting, damaged gear pump, or damaged fan motor. Contact Etnyre at 888-586-1899.

**Step 6 — Investigate radiator/engine further:**
If overheating persists after all above checks, contact Etnyre at 888-586-1899 or a Cummins dealer.

---

### Q: I see error codes on the display — what do they mean?

**WARNING: ENGINE CAN**
Computer lost connection with engine ECM. Machine stops. Setpoint limited to 400 FPM. Press Scroll to clear error. Move joystick to neutral, then out of neutral to resume at limited speed. Correct connection and reset computer (both Reset buttons simultaneously while stopped, Park/Drive in Park) to resume normal operation.

**ALARM: PUMP FWD SOL FAILURE**
Computer lost connection with pump forward coil. Machine stops if moving forward. Machine can still move in reverse. Machine will not move forward until error is corrected and computer is reset. Check electrical connections between computer and forward pump solenoid.

**ALARM: PUMP REV SOL FAILURE**
Same as above but for reverse coil. Machine will not move in reverse until corrected and computer is reset.

**ALARM: SPEED SENSOR FAILURE**
Computer is not receiving expected speed pickup feedback. Machine stops. Setpoint limited to 400 FPM. Press Scroll to clear; move joystick to neutral and back out to resume at limited speed. See speed sensor troubleshooting steps above.

**ALARM: FRONT MOTOR SOL FAILURE**
Computer electrically disconnected from front motor solenoid. Machine stops. Setpoint limited to 400 FPM. Press Scroll to clear; resume at limited speed. Correct electrical connection and reset computer to resume normal operation.

**ALARM: REAR MOTOR SOL FAILURE**
Same as above for rear motor (4WD machines only).

**ALARM: JOY STICK FAILURE**
Joystick center tap voltage out of range, OR reverse switch signal mismatch. Machine stops. Error can be cleared but machine will not move until error is resolved and computer is reset. See Joystick Fault troubleshooting above.

**WARNING: FUEL LEVEL LOW**
Fuel below 10%. Error can be cleared with Scroll switch. Warning returns after 5 minutes or if computer is reset, while condition persists. Refuel immediately.

**ALARM: HYDRAULIC OIL HOT**
Hydraulic oil temperature above 180°F. See hydraulic overheating troubleshooting above.

**ALARM: ENGINE COOLANT HOT**
Engine coolant temperature above 240°F. See water temperature alarm troubleshooting above.

**ALARM: BATTERY VOLTAGE LOW**
Computer supply voltage below 11 V. Check charging system, battery, and all ground connections.

**ALARM: BATTERY VOLTAGE HIGH**
Computer supply voltage above 15 V. Check alternator voltage regulator.

**EMERGENCY: SHUTDOWN UCM SPEED**
Computer detects movement from speed pickup when not commanding movement. Engine shuts down immediately. Fast audible alarm sounds. "WARNING: ENGINE CAN" displays after a few seconds. Reset computer (both Reset switches simultaneously, stopped, Park in Park, joystick neutral) to clear audible alarm. See UCMD Speed troubleshooting above.

**EMERGENCY: SHUTDOWN UCM DIRECTION**
Computer detects 12 VDC on direction wire from speed pickup when commanding forward movement (or 0 VDC when commanding reverse). Engine shuts down. Same recovery as UCMD Speed. Check speed pickup wiring connections and direction signal wire.

---

### Q: Machine has no gradability / can't climb hills

**Step 1 — Verify the grade is within the machine's capability:**
Maximum combined weight (ChipSpreader + dump truck + aggregate): 80,000 lbs.
Engine RPM: 2200 | Speed setpoint: 200 FPM
- 2-Wheel Drive: 6–8% grade maximum
- 4-Wheel Drive (160 cc motors): 12–18% grade maximum
Motor size (cc) is stamped on the tag attached to the top of the drive motor. If the grade exceeds these limits, the machine cannot be expected to climb it.

**Step 2 — Test with motor servo connectors disconnected (2WD):**
Disconnect the electrical connector on the front drive hydraulic motor servo (secure the wire). Test the machine on the grade at full load. If the machine now climbs the grade: one of the motor servos is receiving a voltage signal that is repositioning the internal swash plate of the hydraulic motor, reducing its displacement. Reconnect the servo and verify.

**Step 3 — Test with all servo connectors disconnected (4WD):**
Disconnect both front and rear drive motor servo connectors. Test at full load. If machine climbs the grade: reconnect servos one at a time and test to identify which motor servo is causing the problem.

**Step 4 — Check hydrostatic pressure override (POR):**
If disconnecting servo connectors does not improve performance, check and verify the hydrostatic pump POR hydraulic pressure per M-215-16 Appendix D procedures.

**Step 5 — Check hydrostatic main pressure:**
Check and verify forward high pressure (target 7000 PSI at high-pressure cross-port relief valve MA). Check and verify reverse high pressure (relief valve MB, also 7000 PSI). Contact Etnyre at 888-586-1899 if pressure adjustment is required.

---

## Section 9 — Troubleshooting — Output / Product Quality Problems

### Q: There is a streak or void down the center of the road when both hoppers are fully extended

**Cause:** The inner ends of the left and right hoppers are not meeting correctly, leaving a gap.

**Step 1 — Adjust the gate cut-off plate outward:**
Slide the cut-off plate outward (away from center) in both hoppers to widen the material flow at the inner edge. Adjust both sides evenly.

**Step 2 — Adjust the hopper cylinder if cut-off plate is at maximum:**
If the cut-off plate cannot be adjusted any further outward, adjust the hopper extend/retract cylinder at the rod end. This changes the maximum extended position of the hopper. Adjust both sides evenly.

---

### Q: There is an overlap or heavy streak in the center of the road when hoppers are fully extended

**Cause:** The inner ends of the hoppers are overlapping, depositing too much material in the center.

**Step 1 — Adjust the gate cut-off plate inward:**
Slide the cut-off plate inward (toward center) in both hoppers to narrow the material flow at the inner edge. Adjust both sides evenly.

---

### Q: The material application is uneven — one side heavier than the other

**Step 1 — Verify spread roll speeds are equal:**
Both spread rolls should be running at 96 RPM. An imbalanced spreadroll speed causes uneven application. Adjust using the flow control cartridges per the Spreadroll Speed Adjustment procedure.

**Step 2 — Calibrate individual hoppers:**
Use the calibration procedure (Section 7) to measure actual application from each hopper independently and adjust the LEFT CAL and RIGHT CAL values to match the setpoint.

**Step 3 — Check hopper gate wear plates:**
Worn or misaligned gate wear plates cause inconsistent gate openings. Inspect and adjust per the maintenance adjustment procedure — wear plate should extend 1/32" past the gate edge across the full gate width.

**Step 4 — Verify gate transducer accuracy:**
A faulty or misadjusted gate transducer will cause the computer to open the gate more or less than commanded. Check the transducer per the gate transducer checking procedure.

---

### Q: Spread roll speed is incorrect or inconsistent (application rate off)

Refer to the Spreadroll Speed Fluctuating section in Section 8 above. Target is 96 RPM on both left and right spreadrolls, verified with a stopwatch or tachometer.

---

### Q: Material is bridging in the hopper and not flowing through the gate

**Step 1 — Check aggregate moisture:**
Wet or clumped aggregate bridges in hoppers. Allow material to dry or break up clumps before loading.

**Step 2 — Use the gate override to clear:**
Press the Gate Override button (item 23 or 24) to momentarily fully open the gate, allowing the bridge to break. Release to return to setpoint.

**Step 3 — Use the vibrator (if equipped):**
Activate the Vibrator switch (item 46) momentarily to vibrate the hopper and break up bridged material.

---

## Section 10 — Troubleshooting — Application-Specific Problems

### Shoulder Work / Partial Width Spreading

**Setup for shoulder work:**
- Retract the hopper that is NOT needed (use hopper position switch).
- OR keep both hoppers extended but turn off individual gate switches at the outboard end of the inactive side to control spread width in 1-foot increments.
- Turn the spread roll OFF for the inactive hopper (to avoid wear on the spread roll turning against closed gates). Note: with spread roll off, application rate will be slightly less — increase the application rate setpoint to compensate.
- Adjust conveyor speeds independently (items 20/21) to match the reduced delivery needed for partial-width operation. The conveyor should still run approximately 80% of the time.

### Hill and Grade Work

- **Steep upgrades:** The truck may assist the Chipspreader, but the Chipspreader must always be pulling the truck. Never allow the truck to push the Chipspreader.
- **Steep downgrades:** The truck may assist in braking. Always set the truck's own brakes after stopping, regardless of slope. Use radio, hand signals, or horn for coordinated braking communication.
- **Warning:** The larger the truck or steeper the grade, the longer the stopping distance.
- **Speed control on grades:** If the engine cannot maintain speed on a steep hill, bring the joystick rearward toward neutral to let the engine recover to high idle RPM. When the hill decreases in steepness or truck load lightens, push the joystick fully forward again to return to setpoint.

### Traveling Between Job Sites (Roading)

- Keep front hoppers fully closed and latched with safety chains.
- Avoid traveling with material in hoppers — added weight in front hoppers reduces rear-wheel traction and increases stopping distance.
- Keep machine on road or relatively uniform surfaces — rough terrain can damage the extended hoppers or rear conveyor.
- Stopping distances increase significantly when towing a loaded truck. Exercise caution.

### Conveyor Speed Optimization

- For shoulder work or operations requiring less than full hopper width, conveyor speeds can be adjusted independently to match material delivery rate.
- When properly balanced, conveyors should run approximately 80% of the time at maximum hopper width and maximum job speed.

---

## Section 11 — Maintenance Schedule

> **WARNING:** When two people are performing maintenance adjustments, do not start engine without assuring that the other person is clear of moving parts and out from under the machine. Be sure that the mode selector is in park and the control stick is in neutral before attempting to start engine.

### Every Operation (Daily)

Perform before each shift:
1. Grease all Lubrication Chart points (see Weekly section for full point list).
2. Check engine coolant level — refer to engine manual.
3. Check engine oil level — refer to engine manual.
4. Check hydraulic oil level at sight eye on reservoir tank.
5. Check fuel level on computer display; refuel if low.
6. Check DEF level (Tier V engine only).
7. Inspect machine for fluid leaks, loose bolts, improper hose routing.
8. Inspect tire pressures: front 55–60 PSI, rear 60–65 PSI.
9. Check hopper gate clearance: 1/16" between gate and spread roll.
10. Inspect conveyor belt tracking and tension.
11. Confirm all guards, shields, and covers are in place.

### Weekly (Grease All Points Sparingly with #2 Molib-Alloy Grease)

| Point | Location | Qty |
|---|---|---|
| 1 | Bearing — Spreadroll (both ends) | 4 |
| 2 | Bearing — Auger (both ends) | 4 |
| 3 | Bearing — Hopper Gate (both ends) | 4 |
| 4 | Bearing — Individual Gates | As Required |
| 6 | Flange Bearing — Conveyors | 4 |
| 7 | Flange Bearing — Return Idler | 12 |
| 8 | Bearing — Tail Pulley | 4 |
| 9 | Bearing — Hitch Levers | 4 |
| 10 | Shaft — Truck Hitch | 4 |
| 11 | Shaft — Front Axle Pivot | 2 |
| 12 | Spindle — Front Axle | 4 |
| 13 | Tie Rod — Front Axle | 6 |
| 14 | Bearing — Slack Adjuster (2WD only) | 2 |
| 15 | Bearing — Camshaft (2WD only) | 4 |
| 27 | Roller Chain — Power Seat (optional) | 2 (use #10 non-detergent oil) |

### As Needed

| Point | Condition | Action |
|---|---|---|
| 16 | Hydraulic Reservoir | Add ISO VG 46 Hydraulic Oil when low |
| 17 | Hydraulic Oil Cooler | Clean as required |
| 22 | Magnet — Hydraulic Reservoir (in tank) | Clean as required |

### When Indicator Turns Red / Alarm Active

| Point | Action |
|---|---|
| 18 | Engine Air Intake Filter (item 19) — replace filter element |
| 20 | Return Filters — replace filter elements (2) |
| 21 | Suction Filters — replace filter elements (2) |
| 23 | Breather — Hydraulic Reservoir — replace filter element |

> **Filter note:** On new machines, change filter elements after the first two weeks of operation. After that, replace elements on an annual basis UNLESS the hydraulic system has been serviced and contamination introduced — change any time contamination may have entered the system.

### Yearly (Annual)

| Point | Location | Lubricant | Service |
|---|---|---|---|
| 24 | Differential Housing — 1 (2WD) or 2 (4WD) | SAE 90 API GL-5/MIL-L-2105B Gear Lube | Drain and fill |
| 25 | Planetary Wheel End — 2 (2WD) or 4 (4WD) | SAE 90 API GL-5/MIL-L-2105B Gear Lube | Drain and fill |
| 26 | Hub — Rear Axle (2WD only) × 2 | SAE 90 API GL-5/MIL-L-2105B Gear Lube | Drain and fill |

> **New machine note:** On new machines, drain and refill axle lubricants after the first 50 hours of operation. After the initial 50-hour change, change annually.

### Maintenance Adjustments

**Hopper Spread Roll Wear Plate Adjustment:**
1. Turn spread rolls and conveyors OFF.
2. Loosen all wear plate hold-down bolts.
3. Adjust wear plate until nominal 1/16" clearance exists between wear plate and spread roll across the entire hopper width.
4. Re-tighten all hold-down bolts.
5. When one side of a plate is excessively worn, turn the plate over and use the opposite side.

**Hopper Gate Wear Plate Adjustment:**
1. Turn spread roll and conveyors OFF.
2. Loosen wear plate hold-down bolts.
3. Extend the plate 1/32" past the gate edge along the entire gate width.
4. Tighten hold-down bolts.
5. As wear occurs, additional adjustment will be needed. Plate can be flipped when one side is worn.

**Conveyor Belt Adjustment (tracking):**
1. If belt drifts to one side, tighten the tail pulley adjustment on that side until belt centers.
2. If tail pulley adjustment cannot center the belt, adjust the head pulley (see figures 13 and 14 in M-215-16):
   - Belt drifts right: loosen right bearing bolts; loosen jam nuts; start conveyor; tighten adjusting screws until centered; re-tighten jam nuts; stop conveyor; tighten bearing bolts.
   - Belt drifts left: reverse above procedure.
3. Only a small amount of head pulley adjustment should be necessary.
4. Belts should be tight enough to prevent slippage at full load — but excessive tightness shortens belt and bearing life.

---

## Section 12 — Filter Part Numbers

| Filter Type | Etnyre Part / Reference | Location |
|---|---|---|
| Return Filters (2) | Replace annually or when indicator pops up | Between conveyors area, in-tank return line |
| Suction Filters (2) | Replace annually or when indicator active | Suction line to pumps |
| Engine Air Intake Filter | Per engine manufacturer (Cummins) | Air intake assembly |
| Hydraulic Reservoir Breather Filter | Replace annually or when indicator active | Hydraulic reservoir tank top |
| Charge Pressure Filter | Replace when Filter Indicator light (item 42) illuminates | Charge filter assembly |

> **Note:** Specific Etnyre filter part numbers for the VHRS28 are listed in Parts Manual M-211-16 (scan QR code on manual cover) or M-211-18 — check S/N range for your unit. Contact Etnyre Parts at 888-586-1899 for current part numbers.

---

## Section 13 — Winterizing / Storage

> **Note:** The M-215-16 manual does not contain a dedicated winterizing/storage chapter for the VHRS28. The following procedures are derived from system descriptions and general Etnyre equipment practice. Contact Etnyre at 888-586-1899 for a current winterizing bulletin specific to your serial number.

**Recommended Pre-Storage Procedure:**

1. **Complete all outstanding maintenance** per the maintenance schedule (grease all points, change fluids if due).
2. **Empty all hoppers** completely — remove all remaining aggregate from front hoppers and rear hopper.
3. **Run conveyors and augers** to clear all remaining aggregate from belts, auger channels, and gates.
4. **Flush gate area:** Open each gate using the override button to fully flush any remaining fines from the gate/spread roll interface.
5. **Protect hydraulic system:** Verify hydraulic oil is at correct level. On new or recently serviced machines, confirm suction gate valve (in suction tube) is OPEN so the system has oil at the pump inlet.
6. **Drain DEF system (Tier V):** If machine will be stored in freezing temperatures, drain the Diesel Exhaust Fluid (DEF) system per Appendix E of M-215-16 and Cummins engine DEF service bulletin.
7. **Protect engine:** Add fuel stabilizer to the fuel tank per engine manufacturer recommendations. Change engine oil and filter if near the service interval. Drain the water separator.
8. **Protect axles:** If within 50 hours of the annual axle oil change, change all differential, planetary, and hub gear lubes before storage.
9. **Latch and secure hoppers:** Close both front hoppers fully and engage safety chains. This protects the hopper extension mechanisms.
10. **Chock wheels:** Apply wheel chocks.
11. **Cover the control panel:** Install the locking control box cover to protect against vandalism and moisture.
12. **Disconnect batteries** if machine will be stored for extended periods to prevent parasitic drain.
13. **Grease all fittings** generously before storage to protect bearings from corrosion.
14. **Engine coolant:** Verify antifreeze concentration is adequate for expected winter temperatures. The machine carries a Proposition 65 warning for antifreeze — handle per safety data sheet.

**Returning Machine to Service After Storage:**
1. Remove all wheel chocks.
2. Reconnect batteries.
3. Check all fluid levels: engine oil, coolant, hydraulic oil, fuel, DEF.
4. Grease all lubrication points.
5. Verify suction gate valve is fully OPEN before attempting to start.
6. Follow the Hydrostatic System Startup procedure (Section 4) if the hydraulic system was opened or drained.
7. Check tire pressures.
8. Start engine and allow to fully warm up before operating.
9. Test all controls before beginning work.

---

## Section 14 — Safety Reference

> The following safety warnings are reproduced verbatim from M-215-16:

**WARNING — Engine Exhaust (California Proposition 65):**
"Diesel engine exhaust and some of its constituents are known to the State of California to cause cancer, birth defects, and other reproductive harm."

**WARNING — Operations:**
"Do not use this machine for any operation which is not described in this manual. If you have any questions about operation of this machine, contact the Etnyre Service Department at 1-800-995-2116 or 1-815-732-2116. Operations that are not approved could cause serious injury or death."

**WARNING — Fluoroelastomer Handling:**
"Some O-rings and seals used in this vehicle are made from fluoroelastomers. When used under design conditions, fluoroelastomers do not require special handling. However, when fluoroelastomers are heated to temperatures beyond their design temperature (around 600°F), decomposition may occur with the formation of hydrofluoric acid. Hydrofluoric acid can be extremely corrosive to human tissue if not handled properly. A degraded seal may appear as a charred or black sticky mass. Do not touch either the seal or the surrounding equipment without wearing neoprene or PVC gloves if degradation is suspected. Wash parts and equipment with 10% lime water (calcium hydroxide solution) to neutralize any hydrofluoric acid. If contact with the skin occurs, wash the affected areas immediately with water. Then rub a 2.5% calcium gluconate gel into the skin until there is no further irritation, while seeking prompt medical attention. Note to Physicians: For advice or treatment of HF burns, call the DuPont Medical Emergency number, 1-800-441-3637."

**CAUTION — Hydraulic System Cleanliness:**
"Before breaking the seal on all hydraulic fittings, fill caps, etc. be sure to clean around the connection. Failure to do so may cause contaminants to enter the hydraulic system causing damage to pumps, motors, etc."

**WARNING — Ignition Key:**
"Turning ignition switch to 'off' results in a violent stop. SHUT MACHINE OFF AND WAIT FOR ALL MOVEMENT TO STOP BEFORE LEAVING OPERATOR'S SEAT OR SERVICING. FAILURE TO DO SO COULD RESULT IN UNEXPECTED MOVEMENT AND CAUSE SERIOUS INJURY OR DEATH."

**WARNING — Park Selection:**
"Selecting 'park' while the chipspreader is moving results in a violent stop."

**WARNING — Computer Reset:**
"Do not reset computer while chipspreader is in motion. Violent stop will occur which could cause a fall resulting in injury or death."

**WARNING — Gate Hazard:**
"Never put hands in between gate and spread roll or gate and rear of hopper. The gate could move at any time and cause severe injury."

**WARNING — Auger:**
"Auger may start automatically at any time! Do not attempt to clear any jam with the engine running."

**WARNING — Stay Off Hopper:**
"Stay off hopper while machine is moving. Machine movements could cause a fall resulting in injury or death."

**WARNING — No Passengers:**
"NO PASSENGERS. Operators only on machine when operating. Driver only when traveling. Sudden machine movement can cause falls, serious injury or death. Do not sit on handrails."

**WARNING — Moving Under Machine:**
"Do not go under the machine while the engine is running. The machine could move causing severe injury or death."

**WARNING — Towing:**
"Do not tow or push the Chipspreader before reading the towing instructions contained in this manual as this may damage the hydraulic motors."

**WARNING — High-Pressure Setting:**
"When setting the two high pressure cross-port relief valves, DO NOT leave the pump on stroke for more than a few seconds at a time. The flow is being short circuited from the pump inlet and a lot of heat is being generated."

**PARKING BRAKE RATING:**
"PARKING BRAKE MEETS SAE J1472. PARKING BRAKE MAY NOT HOLD ON GRADES STEEPER THAN 15%."

**Hazard Signal Word Definitions:**
- **DANGER:** Immediate hazards which WILL result in severe personal injury or death.
- **WARNING:** Hazards or unsafe practices which COULD result in severe personal injury or death.
- **CAUTION:** Hazards or unsafe practices which COULD result in minor personal injury or product/property damage.

---

## Section 15 — General FAQ

**Q: What is the maximum operating speed of the VHRS28?**
A: The speed setpoint is programmable. Full forward movement gives 100% of the set speed. The maximum reverse speed is up to 1300 FPM.

**Q: What is the normal spreading speed range?**
A: Typical chip spreading is done at 200–500 FPM, depending on aggregate size and application rate requirements. The speed setpoint controls this precisely.

**Q: How many memory presets are available?**
A: Five memory presets (1–5). Each stores a combination of aggregate size, application rate setpoint, and speed setpoint.

**Q: What hydraulic oil does the machine use?**
A: ISO VG 46 Hydraulic Oil.

**Q: What gear lube is used in the axles?**
A: SAE 90 API GL-5/MIL-L-2105 B Gear Lube.

**Q: What grease is used for all bearing fittings?**
A: #2 Molib-Alloy Grease (applied sparingly).

**Q: What is the standby pressure for the auxiliary hydraulic pumps?**
A: 400 PSI (both front and rear auxiliary pumps).

**Q: What is the high pressure setting for the auxiliary pumps?**
A: 3000 PSI. Do not exceed 3100 PSI — hydraulic components are rated for 3100 PSI.

**Q: What is the charge pressure on the drive pump?**
A: Approximately 400 PSI at low idle (acceptable range: 380–420 PSI).

**Q: What is the hydrostatic high pressure setting?**
A: 7000 PSI on both forward and reverse cross-port relief valves. Pressure override (POR) is set to 6500 PSI.

**Q: What is the hopper reducing valve pressure setting?**
A: 1300 PSI (acceptable range: 1200–1400 PSI).

**Q: What is the main relief pressure for the hitch/steering system?**
A: 1200 PSI.

**Q: What is the pilot pressure for the hitch system?**
A: 250 PSI.

**Q: What is the fan valve pressure?**
A: 2000 PSI (acceptable range: 1900–2100 PSI).

**Q: What RPM should the spread rolls run at?**
A: 96 RPM (both left and right spread rolls).

**Q: What is the maximum gate opening?**
A: 4 inches (standard machines). 5 inches (big chippers). Set in computer setup screens — SETUP: GATE OPENING.

**Q: What is the air system pressure?**
A: Main air pressure regulator is set to 80 PSI.

**Q: How do I access the Etnyre online version of this manual?**
A: Scan the QR code on the front cover of M-215-16. The online parts manual M-211-16 (or M-211-18 for certain S/N ranges) is also available via QR code on the cover.

**Q: How do I report a safety defect?**
A: Contact NHTSA in addition to notifying E. D. Etnyre & Co. at 1-800-995-2116. NHTSA investigates safety defects across groups of vehicles and may issue recall campaigns.

**Q: What is the machine's serial number range for M-215-16?**
A: S/N K6975 and Up.

**Q: Who do I call for parts?**
A: Etnyre International — Parts/Service: 888-586-1899 | CustomerService@etnyre.com

---

## Section 16 — RC 36 / RC 28 Computer Connector Pin Reference

### RC 36 Plug 1 (Large Connector) — Key Pins

| Pin | Function |
|---|---|
| 1-01 | Right Auger Solenoid |
| 1-19 | Left Auger In |
| 1-20 | Right Auger In |
| 1-26 | Left Auger Solenoid |
| 1-30 | Left Conveyor Solenoid |
| 1-31 | Right Conveyor Solenoid |
| 1-33 | Reverse Switch |
| 1-34 | Cal − |
| 1-35 | Cal + |
| 1-36 | Rate − |
| 1-38 | Hydraulic Oil Temp |
| 1-39 | Joystick Wiper |
| 1-40 | Right Conveyor In |
| 1-41 | Speed Sensor Direction |
| 1-44 | Memory 1 |
| 1-47 | Enable Left Gate |
| 1-48 | Enable Right Gate |
| 1-49 | Right Spreadroll Solenoid |
| 1-51 | Left Spreadroll Solenoid |
| 1-53 | Right Gate Open Solenoid |
| 1-57 | Speed + |
| 1-58 | Scroll + |
| 1-59 | Right Gate Override |
| 1-64 | Right Gate Wiper |
| 1-65 | Memory 5 |
| 1-66 | Left Gate Wiper |
| 1-67 | Memory 2 |
| 1-69 | Memory 3 |
| 1-70 | Memory 4 |
| 1-77 | Right Gate Close Solenoid |
| 1-79 | Left Gate Open Solenoid |
| 1-80 | Left Gate Close Solenoid |
| 1-83 | Pump Forward Solenoid |
| 1-84 | Pump Reverse Solenoid |
| 1-85 | Rear Motor Solenoid |
| 1-86 | Front Motor Solenoid |
| 1-91 | Fault Indicator |
| 1-92 | Brake Release |
| 1-94 | Backup Alarm |
| 1-95 | UCMD Shutdown |

### RC 36 Plug 2 (Small Connector) — Key Pins

| Pin | Function |
|---|---|
| 2-01, 2-03–2-06, 2-28, 2-40, 2-45, 2-58 | 12 VDC |
| 2-02, 2-07, 2-20, 2-33, 2-46 | Ground |
| 2-09 | Service Brake Signal |
| 2-10 | Rate + |
| 2-11 | Save |
| 2-13 | Speed Sensor Signal |
| 2-14 | Scroll − |
| 2-15 | CAN Diagnosis High |
| 2-16 | CAN Diagnosis Low |
| 2-17 | Enable Left Spreadroll |
| 2-18 | Fuel Level Sender |
| 2-19 | 5 VDC Supply |
| 2-22 | Size − |
| 2-23 | Left Gate Override |
| 2-26 | Enable Right Spreadroll |
| 2-27 | Traction Control |
| 2-30 | Left Conveyor In |
| 2-31 | Joystick Center Tap |
| 2-36 | Park Brake |
| 2-38 | Size + |
| 2-50 | Drive Enable |
| 2-52 | Speed − |
| 2-53 | CAN Work High |
| 2-54 | CAN Work Low |

---

## Section 17 — Voice Agent Call Scripts

### Call Script 1: "My machine won't start — the starter isn't doing anything"

**Agent response flow:**
1. "I can help you with that. First — is the Park/Drive switch on the control panel in the PARK position or the DRIVE position?"
2. If DRIVE: "The engine will not start if the switch is in Drive. Please move the switch to PARK and try starting again."
3. If PARK and still no crank: "Is there a large red mushroom-shaped Emergency Stop button on your control panel? Is it pressed in?"
4. If E-stop is pressed: "Twist that button clockwise to reset it, then try starting."
5. If E-stop is fine: "Let's check your circuit breakers — look at the control panel for a row of breakers and make sure none are tripped. Also check the 30-amp inline fuse for the computer. On your Cummins engine, there are up to four fuses near the power hub at the right rear corner of the engine — please check those as well."
6. If all checks pass and still no crank: "We'll need to escalate this. Please call our Etnyre service team at 888-586-1899 for further diagnosis."

---

### Call Script 2: "My machine just stopped and I see 'ENGINE CAN' on the display"

**Agent response flow:**
1. "That alarm means the computer lost communication with the engine ECM. The machine speed is now limited to 400 FPM. To clear the alarm and continue at reduced speed: press the Scroll button on the display to clear the error, bring your joystick to neutral, then move it out of neutral to resume driving."
2. "To restore full speed capability, we need to find and fix the communication issue. With the machine stopped and engine running, can you scroll through the display screens and tell me what engine RPM is showing?"
3. If RPM shows 0 with engine running: "That confirms the engine ECM communication is broken. Check the engine CAN harness — it's the wiring bundle going to the engine control module. Look for any broken or disconnected connector."
4. "If you cannot find a broken connection on your own, please contact us at 888-586-1899 and we'll walk you through the diagnosis or send a technician."

---

### Call Script 3: "My speed is stuck at 200 FPM and I can't go faster"

**Agent response flow:**
1. "The most common cause is the Traction Control switch being left on — it limits your speed to 200 FPM. Look at your control panel for the Traction Control switch and confirm whether it's in the ON or OFF position."
2. If Traction Control switch is ON: "Turn that switch OFF. Now try increasing your speed — can you go above 200 FPM?"
3. If speed still limited after turning off Traction Control: "The next thing to check is the right spreadroll switch. Turn it OFF. If you can now go above 200 FPM with it off, there's an internal connector problem where the traction control and right spreadroll inputs are shorting together. Try removing and firmly reconnecting the computer connectors, then reinstall the right spreadroll switch and test again."
4. "If the problem persists, call us at 888-586-1899 for connector-level diagnosis."

---

### Call Script 4: "The gates won't open when I push the thumb switch"

**Agent response flow:**
1. "Let's check the most common causes. First — are the Left Gate Power and Right Gate Power switches on your control panel turned to the ON position? These are items 27 and 29 on the panel, behind the joystick area."
2. If no: "Turn both of those switches ON. That connects the gates to the thumb switch. Try the thumb switch again."
3. If yes: "Check your Gate circuit breaker on the control panel — make sure it hasn't tripped. Also check that the Gate Master Switch is turned ON."
4. "Now try pressing the Gate Override button (item 23 for left, item 24 for right) on the panel. Does the gate move with the override?"
5. If gate moves with override: "Good — the hydraulics are working. The problem is in the electrical signal from the thumb switch to the computer. Check the service screens to see if the computer is reading the gate commands. We'll likely need to look at the joystick thumb switch connections. Call us at 888-586-1899 if you need help tracing the wiring."
6. If gate does NOT move with override: "The problem is hydraulic. Check your auxiliary pump hydraulic pressure and the gate solenoid valve. This will require gauge testing per the service manual. Please call us at 888-586-1899."

---

### Call Script 5: "The conveyor won't run in auto mode, but works on manual"

**Agent response flow:**
1. "When the conveyor runs on manual but not in AUTO, the auto diaphragm switch isn't sensing correctly. First — is there material in the conveyor hood above the hopper? The switch turns the conveyor OFF when it senses material."
2. If material is in the hood: "The switch is working correctly — it's sensing material and shutting the conveyor off. Lower or clear the material level in the hood and the conveyor should restart automatically."
3. If no material in hood: "The auto switch sensing distance may need adjustment. Try this: Turn the conveyor selector to AUTO. Then hold the A1 button on the sonic switch until the red light flashes. Place an object at the desired distance from the switch. Then press A1 to save. Test the AUTO operation again."
4. "If the conveyor still doesn't run in AUTO after resetting the switch: the signal from the auto switch may not be returning to the computer. Check the electrical connections at the auto switch on top of the conveyor hood. If connections are good, call us at 888-586-1899."

---

### Call Script 6: "The gates are jumping around and not holding a steady position"

**Agent response flow:**
1. "Unsteady gates are usually caused by the gate current setting being too high. We need to access the computer setup screens. Hold the Cal switch down while turning the ignition key ON — this gets you into the setup screens."
2. "Scroll through the setup screens until you find the RIGHT GATE OPEN, RIGHT GATE CLOSE, LEFT GATE OPEN, and LEFT GATE CLOSE settings. What values are showing for those?"
3. If values are above 1.0 amp: "Those values are too high, which causes the gates to flutter. Use the CAL switch to reduce each value down to between 0.90 and 0.95 amps. Scroll to the Save screen at the end and press Save."
4. "The ideal setting is the highest value that still lets the gate settle steady on the desired opening. Start at 0.90 amps, test the gates, and increase by 0.05 amps if they seem sluggish, until you find the sweet spot."
5. "If adjusting gate current doesn't resolve it, the gate transducer may need recalibration. Call us at 888-586-1899."

---

### Call Script 7: "There's a loud noise / banging sound when I turn the gate master power on or off"

**Agent response flow:**
1. "That loud noise when the gate master power switches on or off usually means the air gates are out of adjustment relative to the hydraulic buss bar — the air gates are slamming against the buss bar with too much gap or too much force."
2. "This requires a mechanical adjustment. First, back off the hydraulic gate arm adjustment screws between all the hydraulic gate buss arms and the air gates. Then adjust the air gate adjustment screws to get a uniform 1/16-inch gap across the spread roll."
3. "Make sure air pressure is being applied to the gates (forcing them closed) while you make this adjustment. Also check all buss arm assembly bolts — replace any bent or broken ones."
4. "After the mechanical adjustment, recalibrate the gate null and scale in the computer setup screens. The null should read 0.00 and the scale should read 4.00 inches."
5. "This procedure takes some time and a trained technician. If you're not comfortable with the mechanical adjustment, please call Etnyre service at 888-586-1899."

---

### Call Script 8: "The hydraulic oil is getting too hot"

**Agent response flow:**
1. "Let's find the cause. First, check your hydraulic oil level at the sight eye on the reservoir tank — is it at the correct level?"
2. If low: "Add ISO VG 46 hydraulic oil to bring it to the full mark. Low oil is a common overheating cause."
3. If level is fine: "Check the front of the hydraulic oil cooler — is it clogged with debris or asphalt? A plugged cooler is very common on chip seal jobs."
4. If cooler is clean: "With the engine at full throttle and the oil hot, unplug the connector on the fan valve. Does the fan speed increase?"
5. If fan speed increases after unplugging: "The fan valve temperature switch may not be triggering the fan soon enough. The hydraulic tank temperature switch should close at 140°F — check that switch and its wiring in the engine harness."
6. If fan speed does NOT increase: "There's a hydraulic issue with the fan circuit — possibly the gear pump or fan motor. This requires hands-on diagnosis. Please call us at 888-586-1899 and we'll help you check the gear pump and fan motor."
7. "Also check the pop-up indicator on the return filter head — if it has popped up, the return filter needs to be replaced."

---

*End of Knowledge Base*

*For further assistance: Etnyre International | Parts/Service: 888-586-1899 | CustomerService@etnyre.com | www.Etnyre.com | 1333 S. Daysville Road, Oregon, IL 61061*
