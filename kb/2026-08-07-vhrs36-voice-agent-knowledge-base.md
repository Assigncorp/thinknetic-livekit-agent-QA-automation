# Etnyre Variable Hopper ChipSpreader VHRS36
## Voice Agent Knowledge Base

**Machine:** Computerized Variable Width Hopper ChipSpreader with RC 36 Controller  
**Model:** VHRS36 (36-inch variable-width hopper)  
**Manuals:** M-215-16 (S/N K6975 and Up, updated August 12, 2025) + M-218-19 (Troubleshooting Supplement, updated November 10, 2020)  
**Manufacturer:** Etnyre International (E. D. Etnyre & Co.)  
**Address:** 1333 S. Daysville Road, Oregon, IL 61061-9778  
**Phone (Sales/General):** 800-995-2116 / 815-732-2116  
**Parts / Service Hotline:** 888-586-1899  
**Customer Service Email:** CustomerService@etnyre.com  
**Website:** www.Etnyre.com  
**Fax:** 800-521-1107  

---

## Section 1 — How to Use This Knowledge Base

This knowledge base is designed to support a voice agent helping operators, technicians, and fleet managers with the Etnyre VHRS36 Computerized Variable Width Hopper ChipSpreader. It covers all major systems based on the operator/service manual M-215-16 and the troubleshooting supplement M-218-19.

**When a caller describes a problem:**
1. Identify the symptom from their description.
2. Navigate to the relevant Troubleshooting section (Sections 10, 11, or 12).
3. Walk the caller through the numbered diagnostic steps in order.
4. For safety-critical steps, read DANGER/WARNING/CAUTION notices verbatim.
5. If the issue cannot be resolved, direct the caller to Etnyre Parts/Service at 888-586-1899.

**Key reminders for the agent:**
- Always confirm the caller has the engine stopped and machine in Park before any maintenance step.
- The VHRS36 has a LEFT and RIGHT hopper — distinguish which side the caller means.
- The RC 36 Controller is the onboard computer. Reset procedures differ from RC 28 (older model).
- Supplement M-218-19 extends troubleshooting beyond what the main manual covers.

---

## Section 2 — Product Overview

### Machine Identity
The Etnyre Variable Hopper ChipSpreader (VHRS36) is a self-propelled, hydrostatic-drive aggregate spreader with a computerized RC 36 controller. It is designed for chip seal (sealcoat) paving operations. The variable-width hopper system allows the machine to spread aggregate across a range of road widths in a single pass, eliminating multiple passes and improving productivity.

**Serial Number Range:** S/N K6975 and Up  
**Controller:** RC 36 (note: M-218-19 also covers RC 28 for older machines)

### Key Specifications
| Parameter | Value |
|---|---|
| Hopper Type | Variable Width (Left + Right independently adjustable) |
| Hopper Width | Variable — extends and retracts independently per side |
| Gate Opening (Standard) | 4 inches maximum |
| Gate Opening (Big Chipper option) | 5 inches maximum |
| Spread Roll Speed | 96 RPM (factory spec) |
| Tire Pressure (Front) | 55–60 PSI |
| Tire Pressure (Rear) | 60–65 PSI |
| Maximum Speed (Forward, full set) | Up to 1300 FPM (reverse) |
| Traction Control Speed Limit | 200 FPM |
| 4WD Max Speed (normal) | 400 FPM setpoint limit without faults |
| 2WD Max Speed (normal) | 600 FPM setpoint limit without faults |
| Hydrostatic Drive Pump High Pressure | 7000 PSI (cross-port relief, forward and reverse) |
| Pressure Override (POR) | 6500 PSI |
| Charge Pressure | 400 PSI (at low idle) |
| Auxiliary Pump High Pressure | 3000 PSI (front and rear auxiliary pumps) |
| Auxiliary Pump Standby | 400 PSI |
| Hopper Reducing Valve | 1300 PSI |
| Main Relief (steering/hitch manifold) | 1200 PSI |
| Pilot Pressure | 250 PSI |
| Fan Valve Relief | 2000 PSI |
| Hydraulic Oil Type | ISO VG 46 |
| Gear Lube | SAE 90 API GL-5/MIL-L-2105 B |
| Grease | #2 Molib-Alloy Grease |

### Major Systems
1. **Hydrostatic Ground Drive** — Rexroth AA4VG125 pump; 2WD or 4WD; 160cc motors
2. **Variable Hopper Assembly** — Left and right hoppers extend/retract independently; individual air-operated gates
3. **Conveyors (Left and Right)** — Carry material from rear hopper to front hopper; independently speed-controlled
4. **Augers (Left and Right)** — Distribute material within front hopper; independently controlled
5. **Spread Rolls (Left and Right)** — Meter aggregate out of hopper; 96 RPM set point
6. **RC 36 Controller** — Controls gate position, speed, application rate, calibration, and alarms
7. **Air System** — Powers individual gate air cylinders; main pressure 80 PSI
8. **Hydraulic Auxiliary Pumps** — Two variable displacement pumps (front and rear) serving hoppers, conveyors, augers, spread rolls
9. **Hitch System** — Power-operated hitch connects to supply truck; hitch height adjustable
10. **Engine** — Cummins diesel (Tier IV or Tier V); electronic engine communication via CAN bus to RC 36

### Component Identification (Major Items)
| No. | Component |
|---|---|
| 1 | Conveyor Drive Motor |
| 2 | Head Pulley Assembly |
| 3 | Gate/Hopper Manifold |
| 4 | Conveyor/Auger/Spreadroll Manifold |
| 5 | Return Filters |
| 6 | Front Drive Axle |
| 7 | Air Reservoir |
| 8 | Hydrostatic Motor |
| 13 | Hydraulic Pumps |
| 22 | Hydraulic Reservoir |
| 23 | Front Control Box Assembly |
| 24/25 | Left/Right Spread Hopper |
| 33 | Rear Hopper Flow Gate |

---

## Section 3 — Warranty

**Warranty Period:** 12 months from date of delivery to original Purchaser.

**Coverage:** E. D. Etnyre Co. warrants its new product to be free from defects in material and workmanship. The company's obligation is limited to repairing or replacing any defective part returned to the company.

**Exclusions — Warranty Does NOT Cover:**
1. Normal start-up services, normal maintenance services, or adjustments usually performed by the selling dealer, factory service representative, or customer personnel.
2. Any product purchased or subjected to rental use.
3. Any product or part showing improper operation, improper maintenance, abuse, neglect, damage, or modification after shipment from factory.
4. Any product or part damaged or lost in shipment (inspect before signing delivery documents).

**Important:** The company will not be responsible for consequential damages. Transportation costs for warranty repairs are not covered. Unauthorized repairs void warranty on affected components.

**Contact for warranty claims:** 800-995-2116 or 815-732-2116

---

## Section 4 — Material Loading and Unloading

### Rear Hopper (Supply Truck Delivery)
- Material is delivered from the supply truck into the rear hopper.
- The rear hopper has flow gates that control how much material falls onto the conveyors.
- Set the rear conveyor gates to deliver as much material as possible onto the conveyor without spillage.

### Conveyor Operation
- Two conveyors (left and right) carry material from the rear hopper to the front variable hopper.
- **Conveyor Selector Switch Positions:**

| Position | Function |
|---|---|
| Bottom (DOWN) | Conveyor ON continuously |
| Middle | AUTO mode — conveyor controlled by sensor; starts when sensor detects no material, stops when material detected |
| Top (UP) | Conveyor OFF |

- Conveyor speed is adjustable 10%–99% using the CAL switch in the operator screen.
- Target: conveyors should run approximately 80% of the time with the hopper at maximum width and Chipspreader at maximum speed for the job.
- Both conveyors are independently controlled and can run in different modes simultaneously.

### Front Hopper (Variable Width)
- Material accumulates in the left and right front hoppers.
- Augers distribute material toward the outer ends of each hopper.
- **Auger Selector Switch Positions:**

| Position | Function |
|---|---|
| Bottom (DOWN) | Auger ON continuously |
| Middle | AUTO mode — controlled by outboard-end sensor |
| Top (UP) | Auger OFF |

- Auger speed is adjustable 10%–99% independently for left and right.

### Valve Position Reference — Key Hydraulic Valves
| Valve / Component | Normal Operating Position | Notes |
|---|---|---|
| Gate Valve (Suction Line) | Fully OPEN (counterclockwise) | NEVER start engine with gate valve closed — will damage pumps |
| Gate Power Switch (L/R) | ON to enable spreading | Connects hopper gate to thumb switch |
| Spread Roll Switch (L/R) | ON to enable spreading | Connects spread roll to thumb switch |
| Gate Master Switch | ON for normal operation | Controls individual gate air cylinders |
| Individual Gate Selector Switches | All ON for full-width spread | Turn off outboard switches for partial-width work |

---

## Section 5 — System Startup

### Pre-Start Checklist
Before starting the engine, always complete the following:

1. Inspect machine condition — tires, fluid leaks, fluid levels, fuel level, loose bolts, hose routing.
2. Check engine coolant level and engine oil level (refer to engine operator's manual).
3. Set tire pressures: Front 55–60 PSI, Rear 60–65 PSI (never exceed sidewall maximum).
4. Grease all fittings and check all reservoir oil levels per lubrication chart.
5. Verify hydraulic suction gate valve is fully open (counterclockwise).
6. Verify front hoppers are retracted and latched with safety chains if traveling between job sites.
7. Install locking control box cover when leaving machine unattended.
8. Chock wheels when leaving machine unattended.
9. Check that gear shift on any connected truck is in neutral.
10. Confirm all shields, covers, and guards are in place.

> **CAUTION:** Before breaking the seal on all hydraulic fittings, fill caps, etc., be sure to clean around the connection. Failure to do so may cause contaminants to enter the hydraulic system causing damage to pumps, motors, etc.

> **CAUTION:** Always place the mode selector switch in the "Park" position when the chipspreader is stopped to avoid accidental movement of the machine.

### Startup Sequence (Normal Operation)
1. Place **Park/Drive switch** in **PARK** position.
2. Place **joystick** in **NEUTRAL** position.
3. Place **Throttle Run/Idle switch** in **IDLE** position.
4. Turn **Power/Ignition Switch** to **ON** — supplies power to all systems.
5. Turn ignition key further right to **START** — release when engine fires.
6. Allow engine to warm up at idle.
7. Move **Throttle Run/Idle switch** to **RUN** (high idle) before performing any work.
8. Set **Speed Set Toggle Switch** to desired chipping speed.
9. Set **Aggregate Size Switch** to the correct aggregate type.
10. Set **Application Rate Switch** to the desired lbs/yd² setpoint.
11. Move **Park/Drive switch** to **DRIVE**.
12. Move **joystick** forward to begin moving.
13. Activate **Gate/Spread Roll switch** (right side) when reaching the spreading start line.

> **WARNING:** Turning the ignition switch to "off" results in a violent stop. SHUT MACHINE OFF AND WAIT FOR ALL MOVEMENT TO STOP BEFORE LEAVING OPERATOR'S SEAT OR SERVICING. FAILURE TO DO SO COULD RESULT IN UNEXPECTED MOVEMENT AND CAUSE SERIOUS INJURY OR DEATH.

> **WARNING:** Do not reset the computer while the chipspreader is in motion. A violent stop will occur which could cause a fall resulting in injury or death.

> **WARNING:** Since all functions except power steering and rear brakes are electrically controlled, turning the key to "off" results in a violent stop.

> **CAUTION:** The front hoppers should be fully closed up and latched using the safety chains at the left side of the machine when the unit is traveling between job sites to avoid possible damage to the outer ends of the hoppers.

### After Hydrostatic System Work (Special Startup Procedure)
If any work was done on the hydrostatic ground drive system involving opening the circuit:
1. Jack machine up and support securely on stands with all four wheels off the ground.
2. Disconnect the 50-pin connector at the engine so engine can only be cranked, not started.
3. Disconnect pump stroker at the pump.
4. Insert 600 PSI gauge in port "G" on the drive pump.
5. Open gate valve in suction tube fully (counterclockwise).
6. Turn ignition ON, throttle to IDLE, crank with starter until 40–60 PSI on charge pressure gauge. DO NOT CRANK MORE THAN 30 SECONDS. Wait 2 minutes before cranking again.
7. Reconnect 50-pin connector.
8. Start engine, let idle 10 minutes. Charge pressure may surge 50–500 PSI while system fills.
9. Shut down engine, remove gauges, replace plugs. Recheck fluid levels after 15 minutes.

---

## Section 6 — Operating Procedures

### Standard Spreading Work Cycle
**Step-by-step spreading sequence:**

a. Place control handle in NEUTRAL.  
b. Set desired chipping speed using **Speed Toggle Switch (3)**.  
c. Turn **Gate/Spread Roll switch (10)** to OFF.  
d. Set desired application rate using **Rate Switch (5)**, or press a memory button.  
e. Confirm **Aggregate Size Switch (4)** is set to the correct aggregate.  
f. Push **speed/direction handle (9)** forward smoothly to full forward position to accelerate to set speed.  
g. Upon reaching the starting line, depress the **right side** of the **Gate/Spread Roll switch (10)** fully to turn gates ON.  
h. At the ending line, depress the **left side** of the **Gate/Spread Roll switch (10)** fully to shut gates OFF.  
i. Return control handle to NEUTRAL.  

**Key behavior notes:**
- Gates close automatically when speed is below 30 FPM, even if switch is left ON.
- Gates will reopen when forward or reverse speed exceeds 30 FPM if switch was left on.
- Speed changes made with Speed Toggle Switch while moving will change the chipspreader speed smoothly; application rate is maintained.
- If gate opening required exceeds what is available for the selected aggregate or hopper position, gates remain at maximum open and application rate cannot be maintained — increase speed to resolve.

### Variable Hopper Width Adjustment

The VHRS36 has left and right hoppers that extend and retract independently.

**Extending the hoppers (widening spread):**
- **Left Hopper Position Switch (25):** Push LEFT to extend left hopper.
- **Right Hopper Position Switch (26):** Push RIGHT to extend right hopper.
- **Front control box — Left Hopper Switch (57):** Push LEFT to extend left hopper.
- **Front control box — Right Hopper Switch (58):** Push RIGHT to extend right hopper.

**Retracting the hoppers (narrowing spread):**
- **Left Hopper Position Switch (25):** Push RIGHT to retract left hopper.
- **Right Hopper Position Switch (26):** Push LEFT to retract right hopper.
- Fully retract and latch with safety chains when traveling between job sites.

**Partial-width spreading:**
- For shoulder work or areas requiring less than full hopper width, turn off the outboard individual gate selector switches to close those sections in 1-foot increments.
- If the spread roll for a section is turned off (for partial-width work), application rate will be less than with the spread roll on — increase the application rate setpoint accordingly.

### Individual Gate Control
- The **Gate Master Switch (51)** connects the individual air gates to the thumb switch on the control stick.
- **Left Hopper Gate Selector Switches (52):** Select which individual gates on the left hopper open with the thumb switch.
- **Right Hopper Gate Selector Switches (53):** Select which individual gates on the right hopper open with the thumb switch.
- Normal operation: Gate Master ON, all individual switches ON — entire left and right hopper width opens.
- For instant shutdown of all gates: Turn Gate Master switch OFF before thumb switch, then turn thumb switch off. Remember to turn Gate Master back ON before opening thumb switch again.

### Gate Hold Feature (VHRS36 Specific)
The RC 36 controller has a GATE OPEN HOLD and GATE SHUT HOLD feature for the RIGHT hopper gate. This staggers the right gate opening/closing relative to the left gate to achieve a straight starting line.

- Default value: 18.0 inches (computer waits until chipspreader travels an additional 18 inches before the right gate opens or closes).
- Left gate is NOT affected by this setting.
- The right spread roll delay adjusts with the gate hold settings.
- If FPM reading is malfunctioning, the right gate hold feature will not work — the right gate will not open. Set GATE HOLD to 0 in setup screens to allow the right gate to operate in manual mode.

### Hitch Operation
- **Hitch Height Switch (22):** Push UP to raise hitch, DOWN to lower. When released, cylinder holds position and floats on a spring for vertical articulation.
- **Hitch Release Pushbutton (17 or 61):** Push to disengage the supply truck. There must be "slack" in the hitch to release; momentarily pull joystick rearward slightly to create slack, then push forward while holding pushbutton.
- To hook up: Press hitch release to open if not already open, then back into truck — hitch automatically closes and locks.
- **Traction Boost Switch (55, optional):** Activates cylinder pushing up on hitch to increase traction on rear tires. Only use while attached to truck. Hitch release will not function while traction boost is active.

> **CAUTION:** Traction Boost may reduce braking efficiency of truck.

### Speed and Braking
- Maximum reverse speed: 1300 FPM (after backing up, reselect memory button to reset chipping speed).
- **Emergency Stop Switch (49):** Brings chipspreader to controlled stop, stops engine while maintaining electrical power. Reset by turning knob clockwise.
- **Brake Pedal (56):** Assists hydrostatic braking. If released during deceleration, speed at that instant becomes new speed setpoint.
- **PARKING BRAKE:** Meets SAE J1472. May not hold on grades steeper than 15%.

---

## Section 7 — Control Panels and Controller

### Main Control Panel (Control Console) — All Controls

![Figure 1 — Control Panel Identification](./2026-08-07-vhrs36-images/M-215-16-page1-img.jpeg)

| Item | Control Name | Function |
|---|---|---|
| 1 | Power/Ignition Switch | OFF → ON (power all systems) → START (spring-return) |
| 2 | Mode Selector — Drive/Park | PARK: disables joystick, applies parking brake. DRIVE: releases brake when joystick moves from neutral. |
| 3 | Speed Set Toggle Switch | Push UP = increase speed setpoint; DOWN = decrease. Display shows setpoint while stopped, actual speed while moving. |
| 4 | Aggregate Size Switch | Selects aggregate: Sand, 1/4" Chips, 3/8" Chips, 3/8" Gravel, 5/8" Chips, 1" Chips |
| 5 | Application Rate Switch | Push UP = increase lbs/yd² setpoint; DOWN = decrease. |
| 6 | Circuit Breakers | Light, Conveyor, Controller, Horn, Gate, Motor — see detail below |
| 7 | Computer Display Screen | Shows application rate, aggregate size, speed. Scrolls through operator and service screens. |
| 8 | Screen Scroll Switch | Scroll through display screens (UP = previous, DOWN = next) |
| 9 | Speed/Direction Control Handle (Joystick) | Forward = advance; neutral = stop + parking brake applied; reverse = back up |
| 10 | Gate/Spread Roll Switch | Right side = open gates/activate spread roll; Left side = close gates |
| 11 | Turn Signal Selector | Push right = right turn signal; left = left turn signal. NOT self-canceling. |
| 12 | Left Turn Signal Indicator | Visual indicator |
| 13 | Right Turn Signal Indicator | Visual indicator |
| 14 | Hazard Flasher Switch | UP = on; DOWN = off |
| 15 | Headlight Switch | Pull OUT = on; push IN = off |
| 16 | Seat Shift Switch (Optional) | Hold right or left to move seat. |
| 17 | Hitch Release Pushbutton | Push to disengage truck from chipspreader |
| 18 | Strobe Switch (Optional) | UP = on; DOWN = off |
| 19 | Application Rate Computer | Inside panel; receives speed pickup and gate transducer signals |
| 20 | Right Conveyor Selector | DOWN = ON; MIDDLE = AUTO; UP = OFF |
| 21 | Left Conveyor Selector | DOWN = ON; MIDDLE = AUTO; UP = OFF |
| 22 | Hitch Height Switch | UP = raise; DOWN = lower |
| 23 | Left Gate Override Switch | Press to momentarily fully open left gate to clear jam; releases back to setpoint |
| 24 | Right Gate Override Switch | Press to momentarily fully open right gate to clear jam; releases back to setpoint |
| 25 | Left Hopper Position Switch | LEFT = extend; RIGHT = retract |
| 26 | Right Hopper Position Switch | RIGHT = extend; LEFT = retract |
| 27 | Left Gate Power Switch | ON = connects left gate to gate/spread roll switch |
| 28 | Left Spread Roll Switch | ON = connects left spread roll to gate/spread roll switch |
| 29 | Right Gate Power Switch | ON = connects right gate to gate/spread roll switch |
| 30 | Right Spread Roll Switch | ON = connects right spread roll to gate/spread roll switch |
| 31 | Left Auger Selector | DOWN = ON; MIDDLE = AUTO; UP = OFF |
| 32 | Right Auger Selector | DOWN = ON; MIDDLE = AUTO; UP = OFF |
| 33 | Memory Selector Buttons (1–5) | Recalls saved combination of speed, rate, aggregate size |
| 34 | Memory Save Button | Saves current setpoints to a memory location |
| 35 | Calibrate Switch | Access calibration screens; adjust left/right hopper output |
| 36 | Traction Control Switch (4WD only) | On = transfers torque to front axle; limits speed to 200 FPM. Joystick must be in neutral to engage. |
| 37 | Throttle Run/Idle Switch | IDLE = low idle (start here); RUN = high idle (for all work) |
| 38 | Throttle Increase/Decrease Switch | Fine-tune engine RPM. Minimum recommended: 900 RPM. Also used to scroll engine fault codes when Engine Diagnostics is ON. |
| 39 | Horn | Signal truck or warn of danger |
| 40 | Batwing Switch | UP = raise batwing hopper; DOWN = lower |
| 41 | Warning Light | Activates when any monitored function reaches alarm point |
| 42 | Charge Filter Indicator | Lit = charge pressure filter is clogged |
| 43 | Auxiliary 12V Power | Cigarette lighter style — on when ignition is ON or in accessory position |
| 44 | Engine Diagnostics On/Off Switch | With ignition ON/engine NOT running: turn on to read fault codes from stop light flashes |
| 45 | Vibrator Auto Select Switch (Optional) | Vibrators cycle ON with gate/spreadroll switch activation for set time, then shut off |
| 46 | Vibrator Manual On/Off Switch (Optional) | Hold UP = vibrators on; releases to OFF |
| 47 | Engine Diagnostics Stop Light | When lit = SHUT DOWN ENGINE immediately; call Cummins dealer |
| 48 | Engine Diagnostics Warning Light | Indicates engine issue — look into soon |
| 49 | Emergency Stop Switch | Controlled stop; stops engine; maintains electrical power. Reset by turning knob clockwise. |
| 50 | Computer Reset Switch (dual) | Both switches must be pressed simultaneously to reset. Machine must be stopped, Park/Drive in PARK, joystick in neutral. |
| 51 | Individual Gates Master Switch | Connects selected individual gates to thumb switch |
| 52 | Left Hopper Gate Selector Switches | Select which left hopper gates open with thumb switch |
| 53 | Right Hopper Gate Selector Switches | Select which right hopper gates open with thumb switch |
| 54 | Hopper Raise/Lower Switch | UP = raise hopper; DOWN = lower hopper |
| 55 | Traction Boost Switch (Optional) | Pushes up on hitch for increased rear traction when attached to truck |
| 56 | Brake Pedal | Service brake; assists hydrostatic braking |

### Circuit Breaker Detail

| Breaker | Powers | Power Source |
|---|---|---|
| Light | All lights except brake lights | Accessory post (ignition switch) — loses voltage when starter engaged |
| Conveyor | Conveyor and auger switches | Accessory post |
| Controller | Joystick, display, hitch, hopper functions, seat, batwings, gate override | Accessory post |
| Horn | Horn, input switches, front control box | Ignition post — maintains voltage during start |
| Gate | Gate power switches, spreadroll power switches, individual gates | Ignition post |
| Motor | Brake lights, speed sensor, traction control switch | Ignition post |
| Computer | All computer functions | In-line 30-amp fuse, accessory post |

### Front Operator's Control Box (Items 57–65)

![Figure 7 — Front Operator's Control Panel](./2026-08-07-vhrs36-images/fig7-_front-operators-control-panel.jpeg)

| Item | Control | Function |
|---|---|---|
| 57 | Left Hopper Switch | Push LEFT = extend; RIGHT = retract |
| 58 | Right Hopper Switch | Push RIGHT = extend; LEFT = retract |
| 59 | Left Conveyor Pushbutton | Press = turn left conveyor on (overrides selector); release = returns to selector control |
| 60 | Right Conveyor Pushbutton | Press = turn right conveyor on (overrides selector); release = returns to selector control |
| 61 | Hitch Release Pushbutton | Same function as item 17 at main console |
| 62 | Left Auger Pushbutton | Press = left auger on; release = off per selector position |
| 63 | Right Auger Pushbutton | Press = right auger on; release = off per selector position |
| 64 | Left Gate Override Switch | Press = momentarily fully open left gate; release = returns to setpoint |
| 65 | Right Gate Override Switch | Press = momentarily fully open right gate; release = returns to setpoint |

> **WARNING:** Auger may start automatically at any time! Do not attempt to clear any jam with the engine running.

### Variable Hopper Controls — Detail

The VHRS36 variable hopper controls are critical to achieving proper spread width:

- **Hopper Extension (Items 25/26 or 57/58):** Use the position switches to extend or retract each hopper independently. Extending widens the spread; retracting narrows it.
- **Gate Power Switches (27, 29):** Must be ON to enable gate operation for that side.
- **Spread Roll Switches (28, 30):** Must be ON to enable spread roll for that side.
- **Gate Hold Feature:** The SETUP: GATE OPEN HOLD and GATE SHUT HOLD screens in computer setup control the right gate delay (default 18 inches) to achieve a straight starting line. The left gate is not affected.
- **Individual Gate Selectors (52, 53):** Each switch controls 1-foot increment of gate opening at the outboard ends of each hopper. Turn off outboard switches when hoppers are not fully extended for shoulder or partial-width work.
- **Batwing Switch (40):** Controls the optional batwing hopper extension.

### Computer Display Screens (Operator Screens)

**Screen 1 (Main):**
```
20.0        3/8       400
lb/yd²     Chip      fpm
```
Shows: Application rate setpoint | Aggregate size | Speed setpoint (stopped) or actual speed (moving)

**Screen 2:**
```
100°F       60 PSI    15%
WATER       OIL       FUEL
```
Shows: Engine coolant temp | Engine oil pressure | Fuel level

**Screen 3:**
```
100°F       2200 RPM  13.8V
HYD OIL     ENGINE    BATTERY
```
Shows: Hydraulic oil temp | Engine RPM | System voltage (battery when not running; alternator when running)

**Screen 4:**
```
120.8             7550 FT
ENGINE            CHIPPED
```
Shows: Engine hours | Feet chipped (accumulates only when gate thumb switch is active)

### Alarm Setpoints
| Alarm | Threshold |
|---|---|
| High Water Temperature | 240°F |
| Low Fuel | 10% (approximately 7 gallons) |
| High Hydraulic Oil Temp | 180°F |
| Low Voltage | 12 volts |
| High Voltage | 15 volts |

---

## Section 8 — Calibration

### Why Calibrate
Calibration ensures the application rate displayed on the screen equals the actual amount of aggregate applied to the ground. Certain material conditions (aggregate density, gate wear, hopper configuration) will cause the actual output to drift from the setpoint. On the VHRS36, calibration must be done separately for LEFT and RIGHT hoppers.

### When to Calibrate
- Initial machine setup.
- When aggregate type is changed.
- When output appears heavier or lighter than expected on one or both sides.
- After gate transducer replacement.
- After spread roll wear plate adjustment.

### Pre-Calibration Requirement
- Verify both spread rolls are turning at **96 RPM** before calibrating material.

### Material Calibration Procedure — Step by Step
1. Select the aggregate to be calibrated on the display (e.g., 3/8 Chips).
2. Set application rate setpoint to desired value (e.g., 20 lb/yd²).
3. Set speed setpoint to approximately 300 FPM.
4. Place the calibration canvas on a flat surface with room for the chipspreader to reach full speed before reaching the canvas.
5. With the control handle in full forward position (to assure constant speed), maneuver the chipspreader toward the canvas.
6. Actuate the gate thumb switch about 10 feet before material will hit the canvas.
7. Deactivate the gate thumb switch once the canvas is covered.
8. Weigh the material AND canvas with the scale provided. Weigh the empty canvas. Subtract to determine lbs/yd².
9. Perform steps 4–8 a minimum of **3 times** and **average the values** before making any changes.
10. Compare measured values against the setpoint on the display.

### Entering Calibration Values

**Accessing calibration screens:**
- Press the CAL switch UP or DOWN from the main operator screen.

**Right hopper calibration:**
- Screen displays: Right hopper measured weight offset and RIGHT CAL value (density factor).
- Example: Setpoint = 20.0 lbs; Right hopper weighed 18.0 lbs (2 lbs light).
- Hold CAL switch UP (+) until lb/yd² reads +2.0.
- Press **SAVE pushbutton** to store the calibration.
- The RIGHT CAL % value will decrease as rate is increased, increase as rate is decreased.

**Left hopper calibration:**
- Press scroll switch DOWN (-) to access LEFT CAL screen.
- Example: Setpoint = 20.0 lbs; Left hopper weighed 23.5 lbs (3.5 lbs heavy).
- Hold CAL switch DOWN (-) until lb/yd² reads -3.5.
- Press **SAVE pushbutton** to store.

**To exit calibration screens:**
- Press scroll switch UP (+) twice to return to main operator screen.
- Calibration only changes when SAVE is pressed.

**Notes:**
- Calibration is permanent (stored in non-volatile memory; survives power-down).
- Calibration is per aggregate type, not per memory location. If 3/8 chips is in memory 1 and memory 2, calibrating 3/8 chips updates both.
- For fine-tuning while chipping: if one side appears lighter or heavier, access that side's cal screen and add or subtract 1–2 lbs, press SAVE.

### Computer Setup Screens (via CAL switch during startup)
Access by holding CAL switch UP or DOWN while turning ignition key on.

| Screen | Purpose | Setting |
|---|---|---|
| SETUP: FIRMWARE | Shows firmware version | Read only |
| SETUP: WORK MODE | Ship mode (300 FPM fixed) or Work mode | Set to WORK for normal operation |
| SETUP: ENGINE | Electronic or mechanical engine | Set to ELECTRONIC for Cummins with ECU |
| SETUP: DRIVE | 2WD or 4WD | Match machine configuration |
| SETUP: MOTOR SIZE | Motor displacement | 160 CC (standard) |
| SETUP: HOPPER | Fixed or Variable | Set to VARIABLE for VHRS36 |
| SETUP: UNITS | English or Metric | Set to ENGLISH for standard US units |
| SETUP: JOYSTICK | Calibrate neutral, forward, reverse positions | Follow 3-step cal sequence |
| SETUP: GATE OPENING | Maximum gate opening | 4.00 inches (standard); 5.00 inches (big chipper) |
| SETUP: RIGHT NULL | Set closed position of right gate to 0.00 inches | Gate must be actually closed |
| SETUP: RIGHT SCALE | Set full-open position of right gate to 4.00 inches | Hold right gate override; verify gate is fully open |
| SETUP: LEFT NULL | Set closed position of left gate to 0.00 inches | Gate must be actually closed |
| SETUP: LEFT SCALE | Set full-open position of left gate to 4.00 inches | Hold left gate override; verify gate is fully open |
| SETUP: RIGHT OPEN | Current (amps) for right gate open solenoid | Ideal: 0.900 amps |
| SETUP: RIGHT CLOSE | Current for right gate close solenoid | Ideal: 0.950 amps |
| SETUP: LEFT OPEN | Current for left gate open solenoid | Ideal: 0.900 amps |
| SETUP: LEFT CLOSE | Current for left gate close solenoid | Ideal: 0.950 amps |
| SETUP: GATE OPEN HOLD | Right gate delay distance for straight start line | Default 18.0 inches |
| SETUP: GATE SHUT HOLD | Right gate delay distance for straight stop line | Default 18.0 inches |
| SETUP: SAVE AND EXIT | Save or exit setup | Press SAVE button to save |

### Joystick Calibration Procedure
1. Place joystick in neutral — display should read 0.0%.
2. Press CAL switch — follow on-screen prompts.
3. Calibrate neutral: Press CAL (display shows "Neutral: ~2.4 volts").
4. Push stick full forward: Display shows "Forward: ~4.4 volts" — press CAL.
5. Pull stick full reverse: Display shows "Reverse: ~0.7 volts" — press CAL.
6. Press scroll switch to exit.

### Gate Transducer Adjustment Procedure
1. Place Drive/Park selector in PARK.
2. Hold CAL switch DOWN and start engine — release when computer beeps 3 times (enters setup).
3. Scroll to RIGHT GATE NULL. Verify right gate is closed (1/16" gap to spread roll). Set to 0.0 by pressing CAL DOWN.
4. Scroll to RIGHT GATE SCALE. Hold right gate override. Display should read 4.00". If not, verify gate is fully open, then press CAL DOWN while holding override. Release override — display should return to 0.00".
5. Scroll to LEFT GATE NULL. Repeat steps for left gate.
6. Scroll to last screen — press SAVE pushbutton.

**Physical transducer adjustment (if computer setup alone cannot correct):**
- Blue wire (signal) at closed gate: should read 0.5–1.5 VDC (ideal: 1.0 VDC).
- Red wire (supply): should read 5.0 VDC.
- Loosen mounting bolts on transducer; rotate to achieve 0.5–1.5 VDC closed reading.
- With gate fully open: blue wire should read 3.5–4.5 VDC.
- After adjustment, re-enter setup screens to reset NULL and SCALE.

---

## Section 9 — Troubleshooting — Machine Systems

### Q: The starter won't crank / the machine won't start cranking

**Step 1 — Check Park/Drive Switch:** Park/Drive switch must be in PARK to start the machine. If it is in DRIVE, move it to PARK and try again.

**Step 2 — Check Emergency Stop Button:** If the Emergency Stop button is pressed/activated, the machine will not crank. Twist the Emergency Stop button clockwise to reset it, then attempt to start.

**Step 3 — Check for failed relay or disconnected wire:** Inspect electrical connections at the starter relay. Look for loose connections, corroded terminals, or disconnected wires.

**Step 4 — Replace or repair failed component:** If steps 1–3 do not resolve the issue, a relay or starter component may have failed. Contact Etnyre service at 888-586-1899 for further assistance.

---

### Q: The starter cranks but the engine will not start

**Step 1 — Check display for "ENGINE CAN" message:** If the information display shows ENGINE CAN, there is no CAN bus communication between the engine and computer. Proceed to Step 2.

**Step 2 — Check Tier 4 monitor (if equipped):** Determine if the Tier 4 monitor is receiving engine data from the Cummins ECM controller. If NO — go to Step 3. If YES — go to Step 4.

**Step 3 — Check Cummins ECM fuses:** Locate fuses near the power and ground distribution hub at the right rear corner of the Cummins engine. There may be up to 4 fuses depending on engine size. Verify fuse size and connections against the schematic. Note: If equipped with inline yellow rubber-insulated fuse holders with glass fuses — pull holder apart, ensure ring is fully over the end of the fuse (not just touching), ensure ring is tight with good solder joint. Replace any blown fuse with correct size only.

**Step 4 — Check E-stop switch and fuel solenoid:** Inspect the Emergency Stop switch and its wiring, particularly the fuel solenoid portion of the switch.

**Step 5 — Check fuel solenoid/pump on Cummins engine:** Verify the fuel solenoid and fuel pump are operating correctly on the engine.

---

### Q: The machine will not move

**Step 1 — Check Start Latch (Computer Lock):** The computer locks the machine from moving after startup. Place Park/Drive switch in PARK and bring joystick to neutral. Move Park/Drive switch to DRIVE, then move joystick — machine should move.

**Step 2 — Check speed setpoint:** Raise the speed setpoint by moving the SPEED switch UP or pressing a memory button. The new setpoint is displayed while changing.

**Step 3 — Check brake pressure switch:** Turn off machine, unplug electrical connector on brake pressure switch, start machine, and attempt to move. NOTE: With brake pressure switch unplugged, the service brake alone will not stop the machine. If machine moves after unplugging, replace the brake pressure switch.

**Step 4 — Check for Joystick Failure:** Inspect joystick calibration and connections. See Joystick Fault section.

**Step 5 — Check pump solenoid connections:** If machine moves forward but "Pump Reverse Sol error" appears when trying reverse — there is an electrical disconnect between computer and pump (reverse side). If machine moves reverse but "Pump Forward Sol error" appears — electrical disconnect on forward side. Locate and repair.

**Step 6 — Check charge pump:** Install a 1000 PSI gauge in port "G" on the drive pump. With engine at low idle, pressure should be around 400 PSI. If pressure reads near 0 PSI, the charge pump has a problem.

---

### Q: Machine speed setpoint is limited to 200 FPM and I cannot increase it

**Step 1 — Check Traction Control switch:** The traction control switch is a maintained switch. It may have been left on, which sets speed limit to 200 FPM the next time machine is stopped. Turn traction control switch OFF.

**Step 2 — Turn off right spreadroll switch:** If speed can now be changed higher than 200 FPM, there is a problem inside the computer connector. The traction control and right spread roll switch inputs are adjacent in the computer connector.

**Step 3 — Remove and reconnect computer connectors:** Disconnect the computer connectors, reconnect, and check if speed can be changed above 200 FPM.

**Step 4 — Inspect connector pins:** Remove the input pins for the traction control switch and right spreadroll switch from the computer connector. Inspect wire crimps and remove any loose strands of wire. Reinstall pins.

---

### Q: Machine speed is limited to 400 FPM (4WD) or 600 FPM (2WD) and I cannot go faster

**Step 1 — Check for WARNING: ENGINE CAN on display:** If this message appears, the computer has lost communication with the engine. Check engine CAN communication harness for broken connection or wire.

**Step 2 — Check for ALARM: FRONT MOTOR SOL FAILURE:** Enter service screens (machine in PARK). Scroll to SERVICE: Front Motor. Status should be approximately 0.40 amps. If it reads 0.00 amps, there is a disconnection between the computer and the front motor solenoid. For 4WD, also check SERVICE: Rear Motor.

**Step 3 — Check for ALARM: Speed Sensor Failure:** Check circuit breakers. Check the speed sensor connector at the front drive motor. Check all connections between speed pickup and computer. Verify voltages at speed sensor connector (Wire #1: 12 VDC; Wire #2: Ground; Wire #3: 4–7 VAC while machine moving; Green/Yellow wire: 0 VDC forward, 12 VDC reverse).

---

### Q: Speed sensor fault / uncommanded motion detection (UCMD) shutdown

**Step 1 — Identify the type:** Was the engine shut down suddenly? If machine moved in wrong direction and engine shut down, this is UCMD Direction. If machine continued moving when it should have stopped and engine shut down, this is UCMD Speed.

**Step 2 — UCMD Direction:** Speed pickup is wired incorrectly or has broken connection. Correct or repair electrical connections at the speed pickup.

**Step 3 — UCMD Speed (joystick out of calibration):** Enter setup screens in PARK. Recalibrate the joystick following the 3-step procedure.

**Step 4 — UCMD Speed (joystick microswitch adjustment):** If machine slows to a stop and engine shuts down (UCMD Speed or Warning Engine CAN), the joystick neutral microswitch needs adjustment. Remove the joystick from the housing. Adjust the microswitch away from the notched plate.

**Step 5 — Reset computer:** After correcting the fault, reset the computer (both Computer Reset switches simultaneously) to restore normal operation.

---

### Q: Joystick fault alarm

**Step 1 — Check power:** Confirm 12V supply is present at joystick connector.

**Step 2 — Check ground:** Verify ground connection at joystick is intact.

**Step 3 — Check center tap voltage:** Center tap should be 2.5V ± 1.0V. If out of range, recalibrate the joystick in setup screens.

**Step 4 — Check reverse switch signal:** Computer must see reverse switch signal within 2 seconds of moving to reverse. Check reverse switch wires.

**Step 5 — Reset circuit breakers and recalibrate:** Reset all circuit breakers. Enter setup screens and recalibrate joystick. If alarm persists, the machine will not move until the fault is resolved and computer is reset.

---

### Q: No conveyor movement

**Step 1 — Conveyor belt stalled:** Turn conveyor speed to 100%. Cycle the conveyor switch ON and OFF several times to break the belt free. Check that conveyor belt is centered on head pulley and tail pulley. Lower the cutoff plate in rear hopper.

**Step 2 — Speed set too low:** Adjust conveyor speed to a higher percentage. Normal use is around 75%.

**Step 3 — Conveyor solenoid failure:** Look for electrical disconnect between computer and conveyor solenoid. Find and repair loose or broken connection.

**Step 4 — Start latch:** Move joystick to neutral, place Park/Drive switch in PARK. The conveyor switch should now function properly.

**Step 5 — Auto mode problem (if conveyor works on ON but not AUTO):** Check that the auto switch is sensing material correctly — ensure material is not already present in the hood. Set the switching distance to desired location. Check the signal from the auto switch returning to computer. Reset the switch using the operations manual procedure.

---

### Q: No auger movement

**Step 1 — Auger stalled:** Turn auger speed to 100%. Cycle auger switch ON and OFF several times to break free. (Note: audible noise from hydraulic pump should be heard if auger is stalled against material.)

**Step 2 — Speed set too low:** Adjust auger speed to a higher percentage. Normal use is around 75%.

**Step 3 — Start latch:** Move joystick to neutral, place Park/Drive switch in PARK. The auger should now function properly.

**Step 4 — Auto mode (if auger works on ON but not AUTO):** Check for holes in the diaphragm switch. Ensure material is not already touching the switch. Check signal from auto switch returning to computer (electrical connections).

> **WARNING:** Auger may start automatically at any time! Do not attempt to clear any jam with the engine running.

---

### Q: Hydraulic oil is getting hot / overheating

**Step 1 — Check oil level:** Verify hydraulic reservoir oil level is at the sight eye.

**Step 2 — Verify temperature:** Confirm hydraulic oil temperature is actually above 180°F using a laser probe or mechanical temperature gauge (do not rely solely on display).

**Step 3 — Check fan speed/airflow:** Clean front of cooler to allow more airflow. With engine at full throttle, unplug the fan valve connector. If fan speed increases — electrical problem (check temperature switch in hydraulic tank; switch should close when tank temperature is above 140°F; check temperature switch wires). If fan speed does NOT increase — hydraulic problem: check for valve not shifting completely, damaged gear pump, or damaged fan motor.

**Step 4 — Check filter restriction:** Check for red pop-up indicator on top of filter head (indicates clogged filter).

**Step 5 — Check pump orifice:** If orifice screen in load sense line is plugged, pump will remain at high pressure. On variable hopper machines: hold the hopper IN switch until pump is heard at high pressure. This noise should decrease quickly when switch is released. If it does not — see "Auxiliary Hydraulic Pressure Will Not Relieve" section.

**Step 6 — Check standby pressure, high pressure, and function pressures:** Check and verify all hydraulic pressures are within normal limits. Identify location of heat generation — may be relief valve or hydraulic quick coupling.

---

### Q: Water temperature / engine coolant overheating alarm

**Step 1 — Verify temperature:** Confirm engine coolant is exceeding 240°F using laser probe or mechanical temperature gauge.

**Step 2 — Clean radiator:** Clean front of radiator to allow more airflow.

**Step 3 — Check coolant level:** Inspect engine coolant level and top off if low.

**Step 4 — Check for coolant leaks:** Inspect hoses, fittings, and radiator for leaks.

**Step 5 — Check cooling fan:** With water temperature hot and engine at full throttle, unplug the fan valve electrical connector. If fan does NOT spin at full speed — hydraulic problem (valve not shifting, damaged gear pump, or damaged fan motor). Investigate further.

---

### Q: Fuel sender alarm / low fuel warning

**Step 1 — Check actual fuel level:** If fuel level is low, refuel and clear alarm with scroll switch.

**Step 2 — Check for debris on sending unit:** Look for metallic debris on top of the fuel sending unit.

**Step 3 — Check wiring connections:** Look for loose or bad connections or frayed wire touching ground.

**Step 4 — Disconnect sender wire:** If alarm stops when sender wire is disconnected, the sending unit is faulty. Verify resistance per calibration table: Empty = 240 ohms (range 240–260); Full = 33.5 ohms (range 27.5–39.5). If alarm persists after disconnecting, check wiring between sender and computer, connection at computer connector (P2-PIN19 on RC 28; check RC 36 schematic for equivalent pin).

---

### Q: No gradability — machine won't climb hills

**Step 1 — Verify grade is within machine capability:** All calculations based on combined weight of ChipSpreader/dump truck/aggregate = 80,000 lbs max, engine at 2200 RPM, speed setpoint at 200 FPM. Acceptable grades: 2WD = 6–8%; 4WD with 160cc motors = 12–18%. Check motor size (cc) stamped on tag attached to top of drive motor.

**Step 2 — 2WD machines — test motor servo:** Disconnect the electrical connector attached to the front drive hydraulic motor servo (secure wire). Test unit on grade with 80,000 lbs. If disconnecting servo allows machine to pull the grade, the servo is the problem (receiving power that is changing position of internal swash plate).

**Step 3 — 4WD machines — test motor servos:** Disconnect electrical connectors on BOTH front and rear drive motor servos. Test on grade. Reconnect servos one at a time to identify which motor servo is causing the problem.

**Step 4 — Check POR pressure:** Check and verify the hydrostatic Priority Override (POR) hydraulic pressure.

**Step 5 — Check main hydraulic pressures:** Check and verify hydrostatic main hydraulic pressure (Forward) and main hydraulic pressure (Reverse).

---

### Q: Auxiliary hydraulic pressure will not relieve

**Step 1 — Identify the problem:** Found during auxiliary pump pressure checks. Main pressure MUST relieve after checking, or auxiliary pump will not de-stroke. This creates heat, torque loss, and hard start if shut off.

**Step 2 — Shut off machine and close suction valve:** Shut off the machine. Close and shut off the main hydraulic suction valve.

**Step 3 — Locate and cap case drain:** Cap off the case drain at the pump.

**Step 4 — Remove compensator and orifice:** Remove compensator from hydraulic pump(s). Remove load sense compensator cartridge. Locate the 2mm allen head orifice inside housing. Remove the orifice.

**Step 5 — Clean orifice:** Clean orifice with strand of primary wire or torch cleaning kit. Re-install orifice.

**Step 6 — Reassemble:** Re-install cartridge, re-install compensator, uncap and reinstall case drain hose, open suction valve. Install air regulator to hydraulic tank through vent filter connection. Apply 3–5 lbs pressure to hydraulic system to push out trapped air. Start machine and operate all functions to ensure hydraulic oil circulation. Check and adjust pressures.

---

### Q: Display says "ETNYRE NO COMMUNICATION" or is not working

**Step 1 — Display reads "ETNYRE NO COMMUNICATION":** Signal from computer is not being received by the display. Check green and yellow wire connections between display and computer. Check fuse to computer. Check power and ground to computer.

**Step 2 — No message on display at all:** Check power and ground to the display directly.

---

### Q: Computer fault screen messages — what do they mean?

| Fault Code | Meaning | Action |
|---|---|---|
| WARNING: ENGINE CAN | Computer lost connection with engine; speed limited to 400 FPM | Scroll to clear, correct fault, reset computer |
| ALARM: PUMP FWD SOL FAILURE | Computer lost connection with pump forward coil | Machine will not move forward until corrected; machine CAN move reverse |
| ALARM: PUMP REV SOL FAILURE | Computer lost connection with pump reverse coil | Machine will not move forward; can move reverse |
| ALARM: SPEED SENSOR FAILURE | Computer not seeing expected feedback from speed pickup; speed limited to 400 FPM | Scroll to clear, correct fault, reset computer |
| ALARM: FRONT MOTOR SOL FAILURE | Computer disconnected from front motor solenoid; speed limited to 400 FPM | Scroll to clear, correct fault, reset computer |
| ALARM: REAR MOTOR SOL FAILURE | Computer disconnected from rear motor solenoid; speed limited to 400 FPM | Scroll to clear, correct fault, reset computer |
| ALARM: JOY STICK FAILURE | Joystick center tap out of range, or reverse switch mismatch | Machine will not move until resolved and computer reset |
| WARNING: FUEL LEVEL LOW | Fuel below 10% | Scroll to clear; will return in 5 minutes if still present |
| ALARM: HYDRAULIC OIL HOT | Hydraulic oil above 180°F | See Hydraulic Oil Gets Hot section |
| ALARM: ENGINE COOLANT HOT | Engine coolant above 240°F | See Water Temperature Alarm section |
| ALARM: BATTERY VOLTAGE LOW | Computer supply below 11V | Check charging system and battery |
| ALARM: BATTERY VOLTAGE HIGH | Computer supply above 15V | Check charging system |
| EMERGENCY: SHUTDOWN UCM SPEED | Machine moving when no command sent; engine shuts down | Fast audible alarm; reset computer to stop alarm; correct wiring |
| EMERGENCY: SHUTDOWN UCM DIRECTION | Wrong direction detected from speed pickup | Engine shuts down; correct speed pickup wiring |

---

## Section 10 — Troubleshooting — Output Quality Problems

### Q: The application rate on the display doesn't match what's actually going on the road

**Step 1 — Verify aggregate size is correctly selected:** If setpoint is dramatically different from ground application, check that the correct aggregate size is selected on the Aggregate Size Switch (4).

**Step 2 — Perform material calibration:** Perform the canvas weight test (minimum 3 passes, average the results). Use the CAL switch to enter the difference and press SAVE.

**Step 3 — Check spread roll speed:** Verify both spread rolls are running at 96 RPM before calibrating. If spread rolls are not at 96 RPM, see Spread Roll Speed Fluctuating troubleshooting.

**Step 4 — Check gate transducer:** If calibration corrections are large and repeated, the gate transducer may need mechanical adjustment. See Gate Transducer Adjustment section.

---

### Q: Gates are unsteady / gate flutter

**Step 1 — Check gate current settings:** The following parameters must be set between 0.9 and 1.0 amp: Right Gate Open, Right Gate Close, Left Gate Open, Left Gate Close. Use the CAL switch to adjust these values in computer setup.

- Too HIGH: Gates flutter and cannot find the desired gate opening.
- Too LOW: Gates stop before reaching the desired opening; unrepeatable material delivery.
- Ideal: The highest value that still allows gates to settle on the desired opening.

**Step 2 — Verify hydraulic standby pressure:** Low standby pressure can cause erratic gate behavior. Check and adjust auxiliary pump standby pressure to 400 PSI.

---

### Q: Gates will not operate

**Step 1 — Check Gate Arming Switches:** Make sure Gate Arming switches (Gate Power Switches) are turned ON. These are located on the operator's panel behind the joystick.

**Step 2 — Check circuit breakers:** Check all circuit breakers, including making sure there is power to both sides of the circuit breaker assembly.

**Step 3 — Test with gate override button:** Press the gate override button and test gate operation. If gate operates with override = possible ELECTRICAL issue (proceed to steps 6 and 7). If gate does NOT operate with override = possible HYDRAULIC issue (proceed to step 5).

**Step 4 — Check service screen gate commands:** Look at output gate commands in the Service Screens (Computer Service Screens appendix).

**Step 5 — Check hydraulic gate valve:** Manually override the spool assembly to test operation. If gate operates with mechanical override — electrical issue (proceed to steps 6 and 7). If gate does NOT operate with mechanical override — refer to hydraulic pressure testing in Appendix D.

**Step 6 — Check gate transducer adjustments:** Refer to Checking Solid State Gate Transducer procedure.

**Step 7 — Check gate null/scale calibration:** Refer to the computer setup procedure for correct null/scale procedure. Re-calibrate gate transducer in computer setup if needed.

**Step 8 — Check joystick center roller micro switch:** Verify switch is activating properly (yes/no).

**Step 9 — Check power across gate switch in joystick handle:** Verify activating properly.

**Note on Gate Hold Feature:** The RH gate uses a gate hold feature. If FPM is malfunctioning or not working, the right gate will not open. Disable gate hold (set to 0 in setup screens) to allow right gate to operate in manual mode.

---

### Q: Spread roll speed is fluctuating or inconsistent

**Step 1 — Check auxiliary standby pressure:** If standby pressure is too low, the pump will not come on stroke quickly enough, causing insufficient pressure and flow to the spread roll. Check and set standby pressure to 400 PSI per procedures in Appendix D.

**Step 2 — Check and adjust spread roll flow control cartridge:** On variable width hopper units (VHRS36), the flow control cartridge is located in the auger/spread roll manifolds. Left and right spread rolls have separate cartridges. Adjust to achieve 96 RPM.

**Step 3 — Remove and inspect flow control cartridge:** If steps 1 and 2 do not correct the problem, remove and inspect the spread roll flow control cartridge for contamination or debris.

**Step 4 — Monitor standby pressure while spread roll speed fluctuates:** Watch if spread roll speed follows pressure changes (as pressure decreases, spread roll speed decreases). If yes, proceed to step 5.

**Step 5 — Inspect load sense check valves:** Remove load sense check valves (2) located on top of the auger, conveyor, spreadroll manifold. Inspect for contamination, debris, worn spring, or pitted seat assembly.

---

### Q: Overlap or streak in the center when hoppers are fully extended

**Step 1 — Heavy material in center (overlap):** The gate cut-off plate needs to be adjusted by sliding it further INTO the hopper. Adjust both sides evenly.

**Step 2 — Void or streak down the center:** First, adjust the cut-off plate by sliding it OUT of the hopper further. If the cut-off plate cannot be adjusted any further, adjust the hopper in/out cylinder at the rod end of the cylinder (adjust both sides evenly).

---

### Q: Air gates are out of adjustment (very loud noise when master power is turned on/off)

**Step 1 — Identify the problem:** Determine if air gate(s) are out of adjustment OR if hydraulic gate buss arm(s) are not operating properly.

**Step 2 — Adjust air gates (if air gate problem):**
a. Back off hydraulic gate arm adjustment screws between all hydraulic gate buss arms and air gates.
b. Adjust air gate adjustment screws to achieve a uniform gap of 1/16" across the spread roll. Ensure air pressure is applied to the gate forcing it closed during this adjustment.
c. Check all buss arm assembly bolts for tightness; replace any bent or broken bolts.
d. Calibrate gate (null/scale) in computer setup.
e. With machine running, hydraulic pressure applied — turn air gate master power ON; turn all individual air gate switches ON; allow air gates to open to the hydraulic gate buss arm.
f. Adjust hydraulic gate buss arm adjustment screws to force air gates to close until the air gate adjustment screws touch and stop movement. Do NOT force screws past the stop — this can change the gate transducer setting.
g. Repeat step 2d to verify null is still at 0.00 and scale is at 4.00.

**Step 3 — Adjust hydraulic gate buss arm (if hydraulic buss arm problem):**
a. Calibrate gate (null/scale) in computer setup.
b. Refer to "Checking Solid State Gate Transducer" procedure for gate transducer adjustment if needed.

---

### Q: Hydraulic standby (load sense) pressure is fluctuating (gauge needle not steady)

**Step 1 — Root cause:** This happens when the volume of oil in the load sense system is too great, due to a missing or contaminated orifice or load sense check valve.

**Step 2 — Check orifice in load sense line fitting:** Inspect the orifice (0.040 hole) in the fitting attached to the auxiliary hydraulic pump load sense compensator valve. Verify the orifice is installed. Check for contamination. Verify orifice size (.040).

**Step 3 — Check compensator operation:** Verify pressure is responding to hydraulic system demand.

**Step 4 — Check load sense check valves:** With engine off, remove load sense lines from compensators and cap them. Check and set standby pressure. If proper standby pressure is obtained and remains steady with no fluctuating, proceed to isolate. Attach load sense lines one at a time to identify which hydraulic manifold block has a contaminated or bad load sense check valve. Replace if found.

---

## Section 11 — Troubleshooting — Application-Specific Problems

### Q: Machine is spreading heavier on one side than the other

**Step 1 — Check hopper extension:** Verify both hoppers are extended equally.

**Step 2 — Recalibrate independently:** Perform canvas weight test separately for left and right hoppers. Calibrate the heavier side DOWN or lighter side UP using the CAL switch.

**Step 3 — Check individual gate settings:** Verify all individual gate selector switches on both sides are in the same configuration.

**Step 4 — Check spread roll speed:** Verify left and right spread rolls are both running at 96 RPM.

---

### Q: Material is piling up in one area of the hopper / uneven distribution

**Step 1 — Adjust conveyor speed:** Use the CAL switch to independently adjust left and right conveyor speeds. Increase speed on the side that is running low, decrease on the side running full.

**Step 2 — Adjust auger speed:** Similarly, independently adjust left and right auger speeds to distribute material more evenly within the hopper.

**Step 3 — Check auto switch position:** If using auto mode, verify the ultrasonic auto switch sensing distance is properly set.

---

### Q: I need to do shoulder work or spread a narrow strip

**Step 1 — Retract the appropriate hopper:** Use the Hopper Position Switch to retract the hopper on the side that should NOT spread.

**Step 2 — Turn off outboard individual gates:** For partial-width work without fully retracting the hopper, turn off individual gate selector switches on the outboard end (each switch controls 1-foot increments).

**Step 3 — Consider spread roll:** If the spread roll for a section is turned off for partial-width work, application rate will be lower than with the spread roll on. Increase the application rate setpoint to compensate.

**Step 4 — Adjust conveyor speed:** For shoulder work or operations requiring less than full hopper width, adjust conveyor speed to match the reduced rate being spread.

---

### Q: The starting or stopping line is not straight — one side starts/stops ahead of the other

**Step 1 — Adjust Gate Open Hold and Gate Shut Hold:** Access setup screens. Adjust SETUP: GATE OPEN HOLD and SETUP: GATE SHUT HOLD distances (default 18.0 inches) for the right gate. Increasing the value delays the right gate more; decreasing it reduces the delay.

**Step 2 — Verify Gate Hold is not disabled:** If the GATE HOLD value is set to 0, the gate hold feature is disabled and the right gate operates in manual mode.

**Step 3 — Check FPM reading:** If the FPM reading is malfunctioning, the gate hold feature will not work. Resolve any speed sensor faults first.

---

## Section 12 — Maintenance Schedule

### Weekly (or per every use) — Grease Points
| Point | Location | Fittings | Lubricant |
|---|---|---|---|
| 1 | Bearing — Spread Roll (both ends) | 4 | #2 Molib-Alloy Grease |
| 2 | Bearing — Auger (both ends) | 4 | Grease |
| 3 | Bearing — Hopper Gate (both ends) | 4 | Grease |
| 4 | Bearing — Individual Gates | As required | Grease |
| 6 | Flange Bearing — Conveyors | 4 | Grease |
| 7 | Flange Bearing — Return Idler | 12 | Grease |
| 8 | Bearing — Tail Pulley | 4 | Grease |
| 9 | Bearing — Hitch Levers | 4 | Grease |
| 10 | Shaft — Truck Hitch | 4 | Grease |
| 11 | Shaft — Front Axle Pivot | 2 | Grease |
| 12 | Spindle — Front Axle | 4 | Grease |
| 13 | Tie Rod — Front Axle | 6 | Grease |
| 14 | Bearing — Slack Adjuster (2WD only) | 2 | Grease |
| 15 | Bearing — Camshaft (2WD only) | 4 | Grease |
| 27 | Roller Chain — Power Seat (Optional) | 2 | #10 Non-Detergent Oil |

### As Required
| Point | Task | Lubricant/Action |
|---|---|---|
| 16 | Hydraulic Reservoir | Add ISO VG 46 hydraulic oil when low |
| 17 | Hydraulic Oil Cooler | Clean as required |
| 18 | Engine Oil Fill | Per engine manual |
| 22 | Magnet — Hydraulic Reservoir (in tank) | Clean as required |

### When Indicator Turns Red
| Point | Item | Action |
|---|---|---|
| 19 | Filter — Engine Air Intake | Replace filter element |
| 20 | Filter — Return (2 filters) | Replace filter element |
| 21 | Filter — Suction (2 filters) | Replace filter element |
| 23 | Breather — Hydraulic Reservoir | Replace filter element |

### Yearly
| Point | Item | Lubricant | Notes |
|---|---|---|---|
| 24 | Differential Housing | SAE 90 API GL-5 Gear Lube | 1 housing (2WD), 2 housings (4WD) |
| 25 | Planetary Wheel End | Gear Lube | 2 locations (2WD), 4 locations (4WD) |
| 26 | Hub — Rear Axle (2WD only) | Gear Lube | 2 locations |

### New Machine Break-In
- **First 2 weeks of operation:** Change return and suction filter elements after first two weeks. After initial change, replace annually unless contamination introduced.
- **First 50 hours:** Drain axle differential lubricant. Fill with SAE 90 API GL-5 gear lube. After initial 50-hour change, change annually.

### Maintenance Adjustments

**Hopper Spread Roll Wear Plate Adjustment:**
1. Turn spread rolls and conveyors OFF.
2. Loosen all spread roll wear plate hold-down bolts. Adjust wear plate until a nominal 1/16" clearance exists between wear plate and spread roll across the entire hopper width.
3. Retighten all hold-down bolts.
4. When one side of a plate is worn excessively, turn the plate over and use the opposite side.

**Hopper Gate Wear Plate Adjustment:**
1. Turn spread roll and conveyors OFF.
2. Loosen wear plate hold-down bolts. Extend the plate 1/32" past the gate edge along the entire gate width.
3. Tighten hold-down bolts.
4. As plate wear occurs, additional adjustment will be necessary.
5. Worn side can be reversed.

---

## Section 13 — Filter Part Numbers

| Item | Description | Qty | Part Number / Notes |
|---|---|---|---|
| Return Filters | Hydraulic return filters | 2 | Replace when indicator pops up or annually |
| Suction Filters | Hydraulic suction filters | 2 | Replace when indicator pops up or annually |
| Engine Air Intake Filter | Engine air filter element | 1 | Replace when indicator turns red |
| Hydraulic Reservoir Breather | Tank breather filter element | 1 | Replace annually |
| Computer In-line Fuse | Computer power fuse | 1 | 30-amp in-line fuse |

> Note: Contact Etnyre Parts/Service at 888-586-1899 for current part numbers matching your serial number range. Parts manuals M-211-16 (S/N range check) and M-211-18 (S/N range check) are available via QR codes on the manual cover.

### Decal Sets Reference

| Item | Part No. | Qty | Description |
|---|---|---|---|
| 1 | 3102067 | 1 | Decal Set, Chips Hopper Variable |
| 2 | 3102065 | 1 | Decal Set, Chipspreader Body |
| 3 | 3101999 | 2 | Decal — Chipspreader, Forward |
| 4 | 3102000 | 2 | Decal — Chipspreader, Quad |
| 5 | 6000758 | 1 | Emblem — Vehicle, Slow Moving |
| 6 | 3102176 | 4 | Decal — Warning, Pinch Point |
| 7 | 3101717 | 1 | Warning — Hoppers, Stay Off |
| 8 | 3102205 | 2 | Warning — No Passengers, No Handrails |
| 9 | 3102346 | 1 | Important — Hydraulic Bleed Valve |
| 10 | 3103230 | 1 | Notice — Emission Control Information |
| 11 | 3102268 | 1 | Warning — Ignition Switch |
| 12 | 3190516 | 1 | Caution — Traction Boost |

---

## Section 14 — Winterizing / Storage

### Before Extended Storage
1. Perform all lubrication and maintenance per the maintenance schedule.
2. Fill fuel tank to prevent condensation.
3. Run engine to circulate fresh engine oil and hydraulic oil through all systems.
4. Check antifreeze level in engine coolant. The antifreeze decal on the machine indicates the correct coolant mixture.
5. Retract both front hoppers fully and latch with safety chains.
6. Install locking control box cover.
7. Chock all wheels.
8. Disconnect battery if storing for extended periods.
9. Drain water separator in air system.

> **WARNING:** Do not store with material in hoppers — weight in front hoppers reduces rear traction, and material can harden/cake and jam gates.

### Returning to Service After Storage
1. Check all fluid levels (hydraulic oil, engine oil, coolant, fuel).
2. Check tire pressures (Front: 55–60 PSI; Rear: 60–65 PSI).
3. Grease all fittings per lubrication chart.
4. Check all hose connections for leaks or deterioration.
5. Perform hydrostatic system startup procedure if any hydraulic work was done during storage.
6. Perform gate transducer check and calibration if machine has been stored for an extended period.
7. Check spread roll speed (should be 96 RPM) and recalibrate material output.

---

## Section 15 — Safety Reference

> **DANGER — Immediate hazards which WILL result in severe personal injury or death.**

> **WARNING — Hazards or unsafe practices which COULD result in severe personal injury or death.**

> **CAUTION — Hazards or unsafe practices which could result in minor personal injury or product or property damage.**

### Key Safety Rules (Verbatim from M-215-16)

> "Do not use this machine for any operation which is not described in this manual. If you have any questions about operation of this machine, contact the Etnyre Service Department at 1-800-995-2116 or 1-815-732-2116. Operations that are not approved could cause serious injury or death."

> "Unsafe operation of equipment may cause injury. Read, understand and follow the manuals when operating or performing maintenance."

> "Never place hands between the spread roll or gate and rear of hopper. The gate could move at any time and cause severe injury."

> "Do not travel with the seat unlatched. Seat movement could occur causing disorientation and possible loss of control."

> "Remain clear of all moving parts."

> "Always use steps, platforms and handrails provided."

> "Always have shields, covers and guards in place when operating."

> "Make certain everyone is clear of machine before starting or operating the machine."

> "Keep loose clothing away from conveyor area when operating the conveyors."

> "Stay off hopper while machine is moving. Machine movements could cause a fall resulting in injury or death."

> "WARNING NO PASSENGERS. Operators only on machine when operating. Driver only when traveling. Sudden machine movement can cause falls, serious injury or death. Do not sit on handrails."

> "Auger may start automatically at any time! Do not attempt to clear any jam with the engine running."

> "Never put hands in between gate and spread roll or gate and rear of hopper to clear an obstruction. The gate could move at any time and cause severe injury."

> "PARKING BRAKE MEETS SAE J1472. PARKING BRAKE MAY NOT HOLD ON GRADES STEEPER THAN 15%."

> "The fuel tank is part of the crosswalk. Do not drill or weld in this area."

> "To avoid potential damage to electrical components, disconnect batteries before welding."

### California Proposition 65 Warning (Verbatim)
> "Diesel engine exhaust and some of its constituents are known to the State of California to cause cancer, birth defects, and other reproductive harm. Always start and operate the engine in a well ventilated area. If in an enclosed area, vent the exhaust to the outside. Do not modify or tamper with the exhaust system."

### Fluoroelastomer Handling Warning (Verbatim)
> "Some O-rings and seals used in this vehicle are made from fluoroelastomers. When used under design conditions, fluoroelastomers do not require special handling. However, when fluoroelastomers are heated to temperatures beyond their design temperature (around 600° Fahrenheit), decomposition may occur with the formation of hydrofluoric acid. Hydrofluoric acid can be extremely corrosive to human tissue if not handled properly. A degraded seal may appear as a charred or black sticky mass. Do not touch either the seal or the surrounding equipment without wearing neoprene or PVC gloves if degradation is suspected. Wash parts and equipment with 10% lime water (calcium hydroxide solution) to neutralize any hydrofluoric acid. If contact with the skin occurs, wash the affected areas immediately with water. Then rub a 2.5 calcium gluconate gel into the skin until there is no further irritation, while seeking prompt medical attention. Note to Physicians: For advice or treatment of HF burns, call the DuPont Medical Emergency number, 1-800-441-3637."

### Emergency Driveline Disengage Procedure (from M-218-19)
For towing when machine cannot drive under its own power:
1. Install a chain or strap around the front hydrostatic motor and parking brake assembly. Secure assembly to front engine crossmember.
2. Remove the four 16mm bolts securing the parking brake to the front axle.
3. Pull the parking brake and motor assembly away from the front axle to disengage the spline.
4. On 4WD machines, secure the rear motor to the frame crossmember and remove the rear motor in the same manner.
5. Tow chipspreader to an area where it can be loaded onto a trailer. Do NOT tow for long distances.
6. When returning to service, verify that the axle differential housings are filled with gear lube to the full level.

---

## Section 16 — General FAQ

### Q: What is the difference between the RC 36 and RC 28 controllers?
The RC 36 is the newer controller used in VHRS36 and similar units (S/N K6975 and up). The RC 28 is the older controller used in earlier ChipSpreader models. The troubleshooting guide M-218-19 covers both. The pin assignments are different: RC 36 Plug 1 and Plug 2 assignments are documented on pages 24–25 of M-218-19. If performing electrical diagnostics, use the correct connector diagram for the specific controller installed in the machine.

### Q: Can I adjust the speed setpoint while the machine is in motion?
Yes. Use the Speed Set Toggle Switch (3) to increase or decrease the setpoint while moving. The machine will transition smoothly to the new setpoint. The display will show the new setpoint while the switch is held, then return to showing actual speed.

### Q: How do I save operating settings for quick recall?
1. Set Application Rate, Aggregate Size, and Speed to desired values.
2. Press the Memory SAVE button (34).
3. Display reads "Select location 1, 2, 3, 4, or 5."
4. Press the corresponding Memory Selector button (33).
5. Display returns to main operator screen.
6. To verify: press that memory button — display should show "Restoring memory X" and display saved values.
Up to 5 memory presets can be stored. Calibration is tied to the aggregate type, not the memory location.

### Q: How do I read engine fault codes?
1. Turn ignition key to ON (engine NOT running).
2. Position Engine Diagnostics On/Off Switch (44) to ON.
3. Watch the Engine Diagnostics Stop Light (47) — it will flash a series of times corresponding to a fault code.
4. The Warning Light (48) will light when the code is finished.
5. If more than one fault code exists, use the Throttle Increase/Decrease Switch (38) to scroll through active fault codes.
6. Turn off Engine Diagnostics switch when done; Throttle switch returns to normal throttle function.

### Q: Why won't the right gate open even when everything looks correct?
The most common cause on the VHRS36 is the GATE HOLD feature. If the FPM reading is zero or incorrect, the computer will not release the right gate hold. Also verify the Gate Master Switch (51) is ON and the Right Gate Power Switch (29) is ON. Check in service screens: SERVICE: R.GATE SEL should show "Activated" when the right gate power is on and thumb switch is depressed.

### Q: What should I do if the machine starts moving unexpectedly?
Immediately return the joystick to NEUTRAL. The parking brake will automatically apply when the computer reads zero speed. If the machine does not stop, press the Emergency Stop Switch (49). Do not turn the ignition key to OFF while moving — this causes a violent stop.

### Q: How do I set up the ultrasonic conveyor auto switches?
To change switching distance (must be completed within 5 minutes of turning switch on):
1. Turn key to ON; turn conveyor selector switch to AUTO.
2. Hold A1 button until red light flashes.
3. Place object at the desired distance from the switch.
4. Press A1 to save.
5. Repeat steps 2–4 for A2 button.

To set mode:
1. Hold A1 button while conveyor switch is turned to AUTO.
2. Green light flashes 1, 2, 3, or 4 times between pauses.
3. Press A2 until green light flashes 2 times between pauses.
4. Hold A1 for more than 2 seconds to save.

Alternative (per M-218-19):
1. Hold A2 button on sonic switch until green lights flash.
2. Place object at desired distance from switch.
3. Press A2.

> **CAUTION:** Setting switching point too close or changing mode from desired setting may cause automatic switches to function improperly.

### Q: What are normal operating pressures I should know?
| System | Pressure |
|---|---|
| Drive pump charge pressure (low idle) | 400 PSI |
| Drive pump forward/reverse high pressure relief | 7000 PSI |
| Drive pump POR setting | 6500 PSI |
| Auxiliary pump standby | 400 PSI |
| Auxiliary pump high pressure relief | 3000 PSI |
| Hopper reducing valves | 1300 PSI |
| Air system main regulator | 80 PSI |
| Main relief (steering manifold, MPT) | 1200 PSI |
| Pilot pressure (PP) | 250 PSI |
| Fan valve relief | 2000 PSI |

### Q: What does the fuel level resistance calibration table look like?
The fuel sender calibration (from M-218-19):

| Position | Ohms | Ohms Range |
|---|---|---|
| Empty | 240 | 240–260 |
| Full | 33.5 | 27.5–39.5 |

### Q: What does the hydraulic oil temperature resistance table look like?
The hydraulic oil temperature sender resistance values (from M-218-19 Figure 2):

| Ohm Min | Ohm Max | Display (°F) |
|---|---|---|
| 0 | 325 | 100 |
| 266 | 295 | 110 |
| 211 | 235 | 120 |
| 168 | 184 | 130 |
| 138 | 151 | 140 |
| 111 | 124 | 150 |
| 94 | 100 | 160 |
| 81 | 85 | 170 |
| 74 | 80 | 175 |
| 68 | 73 | 180 |
| 58 | 63 | 190 |
| 52 | 54 | 200 |
| 44 | 46 | 210 |
| 37 | 40 | 220 |
| 29 | 28 | 230 |
| 26 | 27 | 240 |

### Q: What are the RC 36 controller computer connector pin assignments?
The RC 36 controller (used in VHRS36) pin assignments (from M-218-19, page 25):

**Plug 1 (Large) — Key pins:**
- 1-01: Right Auger Solenoid
- 1-19: Left Auger In
- 1-20: Right Auger In
- 1-26: Left Auger Solenoid
- 1-30: Left Conveyor Solenoid
- 1-31: Right Conveyor Solenoid
- 1-33: Reverse Switch
- 1-39: Joystick Wiper
- 1-41: Speed Sensor Direction
- 1-47: Enable Left Gate
- 1-48: Enable Right Gate
- 1-49: Right Spreadroll Solenoid
- 1-51: Left Spreadroll Solenoid
- 1-53: Right Gate Open Solenoid
- 1-77: Right Gate Close Solenoid
- 1-79: Left Gate Open Solenoid
- 1-80: Left Gate Close Solenoid
- 1-83: Pump Forward Solenoid
- 1-84: Pump Reverse Solenoid
- 1-85: Rear Motor Solenoid
- 1-86: Front Motor Solenoid
- 1-92: Brake Release
- 1-94: Backup Alarm
- 1-95: UCMD Shutdown

**Plug 2 (Small) — Key pins:**
- 2-09: Service Brake Signal
- 2-13: Speed Sensor Signal
- 2-17: Enable Left Spreadroll
- 2-18: Fuel Level Sender
- 2-19: 5 VDC Supply
- 2-22: Size Decrease
- 2-23: Left Gate Override
- 2-26: Enable Right Spreadroll
- 2-27: Traction Control
- 2-31: Joystick Center Tap
- 2-36: Park Brake
- 2-38: Size Increase
- 2-50: Drive Enable
- 2-53: CAN Work High
- 2-54: CAN Work Low

---

## Section 17 — Voice Agent Call Scripts

### Script 1 — Machine Will Not Move
**Agent:** "Good morning, this is the Etnyre ChipSpreader support line. How can I help you today?"

**Caller:** "My chipspreader won't move at all. I push the joystick forward and nothing happens."

**Agent:** "I can help you troubleshoot that. Let's go through a few quick checks. First — is the Park/Drive switch in Drive position?"

**Caller:** "Yes."

**Agent:** "Good. Is the joystick currently in the neutral or center position?"

**Caller:** "Yes."

**Agent:** "After the computer starts up, the machine locks from moving until you cycle the joystick. Try this: Put the Park/Drive switch to Park, bring the joystick to neutral, then switch back to Drive and push the joystick forward. Does that help?"

**Caller:** "No, still nothing."

**Agent:** "What speed setpoint is showing on the display?"

**Caller:** "It says 0 or maybe 50."

**Agent:** "Try pushing the Speed Toggle Switch up to increase the setpoint to at least 200 FPM. Then try the joystick again."

**Caller:** "Still no movement."

**Agent:** "I'd like you to check the brake pressure switch. Turn the machine off, disconnect the electrical connector on the brake pressure switch, restart the machine, and try to move. If it moves now, that switch needs to be replaced. If there's still no movement, we'll need to check the charge pump pressure. Can you install a gauge in port G on the drive pump?"

---

### Script 2 — Gates Will Not Open
**Agent:** "Thanks for calling Etnyre support. What's happening with your machine today?"

**Caller:** "I activated the gate switch but no aggregate is coming out. The gates won't open."

**Agent:** "Let's check a few things. Are the Gate Power switches — both Left Gate Power and Right Gate Power — turned to the ON position on your control panel?"

**Caller:** "Let me check... yes they are."

**Agent:** "Good. Are the Spread Roll switches also on?"

**Caller:** "Yes."

**Agent:** "Try pressing the Gate Override button — either the left or right override — and see if the gate opens with that button."

**Caller:** "The override does open the gate."

**Agent:** "That tells me the hydraulic side is working, and this is an electrical or computer issue. Can you look at your display? Make sure the machine is in Drive, the joystick has been moved out of neutral at least briefly, and the Gate Master switch is on. Also check that the right hopper Gate Hold distance isn't set too high in the computer setup screens. You may also want to reset the computer — bring the machine to a stop, put it in Park, and press both Computer Reset switches simultaneously."

---

### Script 3 — Machine Speed Stuck at 200 FPM
**Agent:** "Etnyre support, how can I help?"

**Caller:** "My chipspreader is stuck at 200 feet per minute. I can't get it to go any faster."

**Agent:** "That's typically caused by the Traction Control switch being left on. Is the Traction Control switch turned on? It's switch number 36 on your control panel."

**Caller:** "Oh — yes it is, I must have bumped it."

**Agent:** "Turn it off. But you'll need to bring the joystick to neutral first before engaging or disengaging the traction control switch. Then you should be able to set your speed higher."

**Caller:** "I turned it off but still limited to 200."

**Agent:** "In that case, try turning off the Right Spreadroll switch. If the speed can now be changed higher than 200, there's a problem inside the computer connector — the traction control and right spreadroll inputs are adjacent pins. Try disconnecting and reconnecting the computer connectors. If that doesn't help, the pins in the connector may need to be removed and reinstalled to clear any short."

---

### Script 4 — Calibration Question
**Agent:** "Hello, Etnyre support line. What can I help you with?"

**Caller:** "My application rate is showing 20 pounds per square yard but when I weigh the material coming off, it's more like 23. How do I fix that?"

**Agent:** "You need to calibrate the hopper. Before we start, confirm both spread rolls are running at 96 RPM — that's required before calibrating. Also, since you have a variable hopper machine, you'll need to calibrate the left and right hoppers separately."

**Caller:** "Okay, how do I do that?"

**Agent:** "Use your calibration canvas on a flat surface. Set your speed to 300 feet per minute. Make at least 3 passes over the canvas, weigh the material each time, and average the results. Then press the CAL switch up or down on your control panel to enter the calibration screen. For the right hopper, you'll see the RIGHT CAL screen. If your right hopper measured 23 at a setpoint of 20, hold the CAL switch DOWN until the display shows negative 3.0 — then press the SAVE button. Repeat for the left hopper on the LEFT CAL screen. The change takes effect immediately."

---

### Script 5 — Hydraulic Oil Overheating
**Agent:** "Etnyre ChipSpreader support, how can I help?"

**Caller:** "The hydraulic oil hot alarm just came on. What should I do?"

**Agent:** "Stop spreading and let's figure out why it's overheating. First — check the oil level in the hydraulic reservoir. Is it at or near the sight glass?"

**Caller:** "It looks okay."

**Agent:** "Next, check the front of the hydraulic oil cooler. Is it clean and free of debris? Grass, dirt, or aggregate can block airflow and cause overheating."

**Caller:** "It does look pretty dirty."

**Agent:** "Clean the front of the cooler with compressed air or a water hose. Allow the system to cool down below 180 degrees Fahrenheit — that's the alarm threshold. If it continues overheating after cleaning, the next step is to check the cooling fan. With the engine at full throttle and the oil still hot, unplug the fan valve connector. If the fan speeds up when you unplug it, there's an electrical problem with the fan thermostat switch. If the fan doesn't speed up, there's a hydraulic issue — a possible bad gear pump or fan motor. Call us at 888-586-1899 if you need further assistance."

---

### Script 6 — Starting Procedure Walk-Through
**Agent:** "Etnyre support, what can I help you with today?"

**Caller:** "This is my first time operating this machine. Can you walk me through startup?"

**Agent:** "Absolutely. Before we start, make sure the machine has been inspected — check all fluid levels, tire pressures between 55 and 65 PSI depending on front or rear, and make sure all guards are in place. Is the machine on level ground?"

**Caller:** "Yes."

**Agent:** "Good. First, put the Park/Drive switch in the PARK position. Put the joystick in NEUTRAL. Put the Throttle Run/Idle switch in the IDLE position. Then turn the ignition switch to ON — you'll see the computer screen light up. Turn the key further right to START and release it when the engine starts. Let it idle for a minute or two. Then move the Throttle Run/Idle switch to RUN for high idle. Now set your aggregate size, application rate, and speed setpoint. When you're ready to move, switch to DRIVE and push the joystick forward. When you reach the spreading start line, push the right side of the Gate/Spread Roll switch to open the gates. Is there anything specific about the controls you'd like me to explain further?"

---

### Script 7 — Computer Reset Instructions
**Agent:** "Etnyre support. What's the issue today?"

**Caller:** "My display is showing a fault alarm and the machine slowed down. How do I reset the computer?"

**Agent:** "First, bring the machine to a complete stop. Do not try to reset the computer while the machine is moving — that causes a violent sudden stop. Once you're stopped, put the Park/Drive switch in PARK and make sure the joystick is in the center neutral position. Then press both Computer Reset switches at the same time — you have to press both simultaneously for it to work. One switch alone won't do anything. After the reset, put the Park/Drive switch back to Drive, then move the joystick to resume operation."

**Caller:** "What if the alarm comes back?"

**Agent:** "If the alarm returns, the underlying fault hasn't been corrected. The most common alarms are engine CAN communication loss, speed sensor failure, and motor solenoid failures. Can you read me exactly what the display says? I can walk you through the specific diagnostic steps for that fault."

---

### Script 8 — Spread Roll Not Running / Auger Jammed
**Agent:** "Etnyre support, go ahead."

**Caller:** "One of my augers is jammed and the other spread roll isn't turning. What do I do?"

**Agent:** "Let me address these one at a time. For the jammed auger — IMPORTANT: Do not put your hands near the auger with the engine running. The auger can start automatically. With the engine running, set the auger speed selector to 100% and cycle the auger switch ON and OFF several times — this pulsing motion can break the material free. If the auger won't break free, shut the engine off completely before any manual clearing attempt."

**Caller:** "Okay, got it."

**Agent:** "For the spread roll not turning — first, confirm the Spread Roll Power switch for that side is turned ON. Then confirm the Gate/Spread Roll thumb switch is activated. Check if the spread roll switch is connected by verifying in the service screens. Also check if the auxiliary standby pressure is at 400 PSI — if it's too low, spread rolls won't turn properly. If the other side's spread roll IS turning, compare the flow control valve positions between left and right in the auger/spread roll manifold."

---

*End of Voice Agent Knowledge Base*

*Sources: Etnyre International Manual M-215-16 (S/N K6975 and Up, updated August 12, 2025) and Troubleshooting Supplement M-218-19 (updated November 10, 2020).*

*For technical assistance: 888-586-1899 | CustomerService@etnyre.com | www.Etnyre.com*
