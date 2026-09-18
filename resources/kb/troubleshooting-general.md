# Etnyre Chipspreader Troubleshooting Knowledge Base
### Voice Agent Reference Guide — M-218-08R

> **For further assistance, call Etnyre Service Department at 1-800-995-2116.**

---
# **CHIPSPREADER OVERVIEW**

## **What Is a Chipspreader?**

A chipspreader is a specialized road maintenance machine used to apply aggregate, also called “chips” or stone, evenly across a road surface during chip seal operations.

Chipspreaders are commonly used by:

* State DOTs  
* County road departments  
* Municipal public works  
* Asphalt contractors  
* Pavement preservation companies

The machine spreads stone at a controlled rate immediately after asphalt emulsion is applied to the roadway.

---

# **COMMON USES OF CHIPSPREADERS**

## **Chip Seal Operations**

Typical process:

1. Asphalt emulsion is sprayed onto the roadway  
2. Chipspreader applies aggregate evenly  
3. Rollers compact the chips into the emulsion

Benefits:

* Extends pavement life  
* Improves skid resistance  
* Seals small cracks  
* Lower cost than resurfacing

---

## **Other Uses**

* Parking lots  
* Highway shoulders  
* Rural roads  
* Airport maintenance  
* Temporary haul roads

---

# **BASIC CHIPSPREADER COMPONENTS**

## **Hopper**

Stores aggregate before spreading.

Common Issues:

* Bridging  
* Uneven feeding  
* Overloading

---

## **Conveyor System**

Moves aggregate from hopper to spread gates.

May include:

* Conveyor chains  
* Belts  
* Hydraulic motors

---

## **Spread Gates**

Control aggregate distribution and spread width.

Operators may adjust:

* Gate height  
* Spread width  
* Application rate

---

## **Hydraulic System**

Powers:

* Conveyor movement  
* Gate operation  
* Steering  
* Drive systems

Common maintenance areas:

* Hydraulic fluid  
* Filters  
* Hoses  
* Cooling system

---

## **Operator Controls**

Typically include:

* Joysticks  
* Spread controls  
* Speed controls  
* Gate controls  
* Display panels

---

## **Sensors & Electronics**

Modern chipspreaders may include:

* Speed sensors  
* Gate sensors  
* Rate controllers  
* Electronic calibration systems

---

# **COMMON TERMINOLOGY**

## **Aggregate**

Stone material spread onto the road surface.

---

## **Application Rate**

Amount of aggregate spread over an area.

Usually measured in:

* Pounds per square yard  
* Kilograms per square meter

---

## **Calibration**

Adjusting settings for accurate application rates.

---

## **Chip Seal**

Road preservation process using asphalt emulsion and aggregate.

---

## **Emulsion**

Liquid asphalt binder sprayed before aggregate placement.

---

## **Spread Width**

Width of aggregate distribution across roadway.

---

## **Streaking**

Uneven aggregate distribution leaving visible gaps or lines.

---

## **Bridging**

When aggregate gets stuck in the hopper and stops flowing evenly.

---

# **DAILY PRE-OPERATION CHECKS**

## **Visual Inspection**

Check for:

* Hydraulic leaks  
* Loose hoses  
* Damaged wiring  
* Conveyor damage  
* Gate obstructions

---

## **Hydraulic System**

Verify:

* Fluid levels  
* Hose condition  
* Cooler cleanliness

---

## **Tires & Brakes**

Inspect:

* Tire pressure  
* Tire wear  
* Brake operation

---

## **Safety Equipment**

Verify:

* Lights  
* Backup alarms  
* Mirrors  
* Warning decals

---

## **Controls**

Ensure:

* Joysticks respond correctly  
* Displays power on  
* Sensors communicate properly

## How to Use This Guide

When a caller describes a problem, match it to one of the problem categories below. Walk them through each numbered step in order. At decision points, ask the caller what they observe and branch accordingly. Always confirm safety before any electrical or hydraulic checks.

---

## Problem 1 — Speed Sensor Error or Failure

**Symptoms:** Speed sensor error alarm is sounding; machine is not moving as expected.

**First check:** Ask the caller — is the joystick in the neutral position? The alarm will sound if the joystick is out of neutral and the machine is not moving. Have them return it to neutral first.

**Step 1.** Check fuses or circuit breakers.

**Step 2.** Physically inspect the speed sensor:
- Is the sensor loose or detached?
- Is it misaligned with the pickup gear?
- Is the clearance correct? The recommended gap is one-sixteenth of an inch.
- Are there any loose, pinched, or rubbed wires?

**Step 3.** With the wiring harness disconnected, check voltage at the wiring from the computer to the speed sensor:
- Red wire should read 12 volts DC.
- Black wire is ground.
- Clear or white wire should read 9 to 10 volts DC.
- Shield wire is ground.

- **If voltages and grounds are correct** → Go to Step 4.
- **If voltages or grounds are not correct** → Go to Step 5.

**Step 4.** With the harness connected, check power at the speed sensor while the machine is moving:
- Red wire: 12 volts DC.
- Black wire: ground.
- Clear or white wire: should read 4 to 7 volts AC while the machine is moving. If there is no signal, replace the speed sensor.
- Shield: ground.

**Step 5.** With the speed sensor disconnected, check connections at the computer:
- Computer pin P1-PIN 21 should supply 12 volts DC (speed sensor power). If voltage is present here but was absent in Step 3, check wiring between the computer and sensor for continuity. No continuity means the wiring harness assembly needs to be replaced. No voltage indicates a bad connection or bad computer output.
- Ground is attached to the computer base.
- Computer pin P3-PIN 10 should read 9 to 10 volts DC. If voltage is present here but was absent in Step 3, check wiring continuity. If no continuity, replace the wiring harness. If no voltage is present at all, check the other end of the pull-up resistor on P3-PIN 10. It should read 12 volts DC. If it does, replace the resistor — it should be 1k ohm.

> **Note for Kessler axles:** The speed sensor part number is 6703670.

---

## Problem 2 — Fuel Sender Alarm

**Symptoms:** Fuel sender alarm is active.

**Step 1.** Ask the caller: Is the machine actually low on fuel? If yes, refuel. If the tank is not low, continue.

**Step 2.** Check if any metallic debris is resting on top of the sending unit.

**Step 3.** Check the wiring connection at the sending unit for loose connections or frayed wire touching ground.

**Step 4.** Disconnect the wire from the sending unit.
- **If the alarm stops** → The sending unit or its resistance values are the issue. Verify resistance using the fuel sender calibration chart below.
- **If the alarm continues** → Go to Step 5.

**Step 5.** Check wiring between the sender and the computer for any damage.

**Step 6.** Check the connection at the computer for a loose connector.

**Step 7.** Check computer terminal P2-PIN 19.

**Fuel Sender Resistance Reference (key values):**
- Tank full (100% display): approximately 250 ohms — 68 gallons total, 65 usable.
- Tank at 50% display: approximately 140 ohms — 32 gallons total, 29 usable.
- Tank at 25% display: approximately 94 ohms — 18 gallons total, 15 usable.
- Tank at 10% display: approximately 63 ohms — 10 gallons total, 7 usable.
- Tank empty (0% display): approximately 34 to 39 ohms — 4 to 5 gallons total.

---

## Problem 3 — Low Oil Pressure Alarm

**Symptoms:** Low oil pressure alarm is active.

**Important — Alarm activation thresholds:**
- Alarm triggers at 5 PSI when engine is at 1,400 RPM or below.
- Alarm triggers at 10 PSI when engine is above 1,400 RPM.
- The low pressure condition must exist for 2 seconds before the alarm activates.

**Step 1.** Install a mechanical gauge and verify actual engine oil pressure:
- At idle: approximately 30 PSI.
- At full RPM: approximately 65 PSI.
- Engine coolant must be at operating temperature (160 to 190 degrees Fahrenheit) for accurate readings.

**Step 2.** Check wiring at the sensor for loose or bad connections.

**Step 3.** Ground the sensor wire to the engine block and check if the alarm stops.
- **If the alarm stops** → The sensor or its wiring is the issue. Verify sensor resistance values using the calibration chart below.
- **If the alarm continues** → Go to Step 4.

**Step 4.** Check computer connectors P2 and P3.

**Step 5.** At the computer, check:
- Oil pressure sender: P2-PIN 18.
- Oil pressure ground: P2-PIN 2.

**Step 6.** Look for any wires that are pulled out, touching each other, or disconnected.

**Step 7.** Check continuity of wiring between the computer and the oil pressure sender.

**Step 8.** If needed, install a new OEM oil pressure sender unit. Resistance values must be correct for the system to work properly.

**Oil Pressure Sender Resistance Reference (key values):**
- 0 PSI: 240 ohms nominal (range 225 to 257).
- 30 PSI: 156 ohms nominal (range 150 to 168).
- 65 PSI: 100 ohms nominal (range 100 to 100).
- 100 PSI: 60 ohms nominal.
- 125 PSI: 33 ohms nominal.

---

## Problem 4 — Water Temperature Alarm

**Symptoms:** Water temperature alarm is active.

**Step 1.** Verify actual coolant temperature using a laser probe or mechanical gauge.
- **If coolant is NOT exceeding 240 degrees Fahrenheit** → Go to Step 2 (electrical issue).
- **If coolant IS exceeding 240 degrees Fahrenheit** → Skip to Step 7 (actual overheating).

**Step 2.** Check the wiring terminal at the sensor for loose or bad connections.

**Step 3.** Inspect wiring for frayed or bare sections.

**Step 4.** Disconnect the sensor and check if the alarm stops.
- **If the alarm stops** → Verify sensor resistance values using the calibration chart below.
- **If the alarm continues** → Go to Step 5.

**Step 5.** Check for loose or bad connection at computer plug P2.

**Step 6.** Check wiring from sensor to computer pin P2-PIN 20.

**Steps 7 through 11 — Actual Overheating:**

**Step 7.** Check engine coolant level. Use caution when removing the radiator cap.

**Step 8.** Clear any debris from in front of the radiator.

**Step 9.** Check whether the radiator or hydraulic cooler is clogged with aggregate dust or particles. Clean if needed.

**Step 10.** Check for any leaks in the cooling system. Leaks allow particles to collect and cause blockages.

**Step 11.** If overheating continues after these checks, investigate further into the radiator or engine for a deeper problem.

**Water Temperature Sensor Resistance Reference (key values):**
- 160°F: 94 to 100 ohms.
- 180°F: 68 to 73 ohms.
- 200°F: 52 to 54 ohms.
- 220°F: 37 to 40 ohms.
- 240°F: 26 to 27 ohms. (Alarm threshold)

---

## Problem 5 — Hydraulic Oil Temperature Alarm

**Symptoms:** Hydraulic oil temperature alarm is active.

**Step 1.** Check the hydraulic oil level.

**Step 2.** Verify the actual hydraulic oil temperature using a laser probe or mechanical gauge.
- **If temperature is ABOVE 180°F** → Continue with Step 3.
- **If temperature is BELOW 180°F** → Skip to Step 9 (electrical issue).

**Step 3.** Check for filter restriction. Inspect the gauges on the filter bases. Replace any damaged or broken gauge.

**Step 4.** Check for debris trapped in front of the hydraulic cooler. Debris may indicate a hydraulic or cooling system leak.

**Step 5.** Check for debris trapped between the hydraulic cooler and the engine radiator.

**Step 6.** Try to identify the source of the heat. Check the relief manifold, block, quick couplings, hydraulic fittings, and hoses.

**Step 7.** Verify the hydraulic system is plumbed correctly, especially through the hydraulic cooler.

**Step 8.** Check hydraulic pressures to make sure they are not above allowable limits. Refer to Problem 14 if needed.

**Step 9.** Check the connection at the temperature sensor on the hydraulic reservoir tank for a loose or bad connection.

**Step 10.** Disconnect the sensor wire and check if the alarm stops.
- **If the alarm stops** → Verify sensor resistance using the same chart as Problem 4 (Water Temperature Resistance Reference).
- **If the alarm continues** → Go to Step 11.

**Step 11.** Check the connection at computer plug P2.

**Step 12.** Check wiring from sensor to computer pin P2-PIN 17.

**Step 13.** Check wiring for any short to ground.

---

## Problem 6 — Gate Sensor Failure Alarm (Rexroth Computer)

**Symptoms:** Gate sensor failure alarm — the digital display will indicate which side has the failure.

**Step 1.** Check the gate transducer on the side shown by the digital display.

**Step 2.** Check for a disconnected plug at the sensor. Also look for broken or pinched wiring and bad, corroded, or loose connections.

**Step 3.** Identify which type of transducer is installed.

---

**For units with a SOLID STATE transducer (wiring colors: red, blue, black):**

Note: An adapter (Etnyre part number 7050350) is available so wires do not need to be cut or stripped for testing.

- Make sure the gate is fully closed before testing.
- Do NOT unplug the sensor — it must be tested while connected, as readings are based on sensor position.
- Check voltage on the red wire (supply voltage to transducer), grounding through the black wire. Should read 5.0 volts DC.
- Check voltage on the blue wire (transducer signal), grounding through the black wire. Should read between 0.5 and 1.5 volts DC. Ideal is 1.0 volt DC.
- If readings are outside these ranges, rotate the transducer to adjust.
- After any adjustment, re-calibrate the gate (null and scale) in computer setup.
- Important: material application will need to be re-calibrated if the transducer was adjusted.

---

**For units with a RESISTOR TYPE potentiometer (wiring colors: orange, green, black):**

- Make sure the gate is fully closed before testing.
- Unplug the sensor from the harness.
- Check ohms across the orange and green wire terminals at the connector attached to the potentiometer.
- Reading should be between 250 and 270 ohms.
- Important: ohms increase as the gate opens. Do not exceed 270 ohms on this potentiometer.
- Adjust if not within this range.
- After any adjustment, re-calibrate the gate (null and scale) in computer setup.

---

**If failure persists after transducer or potentiometer adjustment:**

**Step 5.** Check wiring for continuity between the transducer or potentiometer and the computer.

**Step 6.** Check connections at the Rexroth computer:
- Fixed hopper or left gate positive: P1-PIN 10, red wire.
- Left gate negative: P1-PIN 18, black wire.
- Left gate wiper: P1-PIN 6, clear wire.
- Right gate positive: P1-PIN 11, red wire.
- Right gate negative: P1-PIN 19, black wire.
- Right gate wiper: P1-PIN 7, clear wire.

---

## Problem 7 — Checking Solid State Gate Transducer (Rexroth Computers)

**Applies to:** Both fixed and variable hopper units.

**Wiring color code:** Red, Blue (or White), Black.

**Step 1.** Verify the gate is fully closed before testing.

**Step 2.** Test with the wiring and sensors still connected. An adapter is available from Etnyre (part number 7050350).

**Step 3.** Check voltage on the red wire — this is the transducer input voltage. Should be 5 volts DC. This is not adjustable. Ground using the black wire.

**Step 4.** Check voltage on the blue wire — this is the transducer signal. Should be between 0.5 and 1.5 volts DC. Ideal is 1.0 volt DC. Ground using the black wire.

**Step 5.** If adjustment was made, re-calibrate the gate null and scale settings in computer setup. Material will need to be re-calibrated if the transducer was adjusted.

**Step 6.** Simulate gate opening by moving the transducer. Watch the signal voltage as you actuate it. Voltage should increase smoothly as the gate opens — by approximately 3 volts DC over a 4-inch gate opening. The sweep must be smooth with no interruptions.

**Signal output reference:**
- Transducer detached from unit: full range is 0 to 5 volts DC.
- Transducer attached to gate assembly: usable range is approximately 3 volts DC.
- Example: if signal is 1 volt DC with gate fully closed, it should not exceed 4 volts DC with gate fully open.

---

## Problem 8 — Gates Open or Close Faster Than the Other Side

**Symptoms:** Left and right gates move at noticeably different speeds.

**Step 1.** Enter computer setup mode. Hold the calibrate switch and turn the ignition to the accessory or on position. Release the switch after the alarm sounds three times. Then use the scroll switch to navigate:

- Scroll to "Right Gate Open" — adjust amps as needed. The higher the amps, the faster the gate moves. Maximum is 1.2 amps.
- Scroll to "Right Gate Closed" — adjust as needed. Maximum 1.2 amps.
- Scroll to "Left Gate Open" — adjust as needed. Maximum 1.2 amps.
- Scroll to "Left Gate Closed" — adjust as needed. Maximum 1.2 amps.

**Notes on machine configuration:**
- On single fixed hopper machines: the left gate open and close settings control gate speed.
- On variable width machines with two rear-spreading hoppers: gate open and close amps can be the same. Gate hold, gate shut hold, and spread roll timer control material stagger for straight-line start and stop.
- On variable width machines with one rear-spreading and one forward-spreading hopper: these amp values are critical for timing the material stagger.

**If adjusting gate speeds does not fix the problem, continue:**

**Step 2.** Check and verify hydraulic pressure on the gate relief valve or valves.

**Step 3.** Check wiring connections at the gate valve.

**Step 4.** Check the Harting (HON) connector mounted on the left outside conveyor rail. On variable width units, the right-side Harting connector is located under the right conveyor above the right front tire.

**Step 5.** Check the output to the gate valve. The amp output should match the threshold set in the computer for gate open and close. At the gate valve connector: terminal 1 (red wire) is power to the valve, terminal 2 (black wire) is ground.

**Step 6.** Check computer connections:
- P4-PIN 5: Right gate open solenoid positive. Ground post is negative.
- P4-PIN 6: Right gate close solenoid positive. Ground post is negative.
- P4-PIN 3: Left gate open solenoid positive. Ground post is negative.
- P4-PIN 4: Left gate close solenoid positive. Ground post is negative.

---

## Problem 9 — Air Gates Out of Adjustment (Very Loud Noise When Master Power Turns On or Off)

**Symptoms:** Very loud noise when master power is switched on or off.

**Step 1.** Identify which type of problem is present:
- **Air gate problem** → Go to Step 2.
- **Hydraulic gate buss arm problem** → Go to Step 3.

**Step 2 — Adjusting Air Gates:**

- Back off the hydraulic gate arm adjustment screws between all hydraulic gate buss arms and air gates.
- Adjust the air gate adjustment screws to achieve a uniform gap of one-sixteenth of an inch across the spreadroll. Make sure air pressure is applied to the gate forcing it closed during this adjustment.
- Check all buss arm assembly bolts to make sure they are tight. Replace any bent or broken bolts.
- Calibrate the gate (null and scale) in computer setup. See the operation manual for the null and scale procedure. The gate transducer may need adjustment if proper calibration cannot be achieved.
- With the machine running and hydraulic pressure applied, turn the air gate master power ON, then turn all individual air gate switches ON, and allow the air gates to open to the hydraulic gate buss arm.
- Adjust the hydraulic gate buss arm adjustment screws to force the air gates to close until the air gate adjustment screws touch and stop movement. Do not force the screws past their contact point — this can alter the transducer setting and arm position. Repeat on each individual gate.
- Repeat the null and scale calibration to verify null is at 0.00 and scale is at 4.00.

**Step 3 — Adjusting Hydraulic Gate Buss Arm:**

- Calibrate the gate (null and scale) in computer setup. See the operation manual for the procedure.
- If transducer adjustment is needed, refer to Problem 8.

---

## Problem 10 — Spreadroll Speed Fluctuating

**Symptoms:** The spread roll motor speed is not steady.

**Step 1.** Check the auxiliary standby pressure. If standby pressure is too low, the pump will not come on stroke quickly enough, resulting in insufficient pressure and flow to the spread roll. Check the applicable chart in the operation manual for proper standby pressure and adjustment procedure.

**Step 2.** Check and adjust spread roll RPM at the flow control cartridge:
- On standard hopper units: the cartridge is in the gate and spread roll manifold.
- On variable width hopper units: the cartridge is in the auger and spread roll manifolds. Left and right spread rolls have separate cartridges.

**If Steps 1 and 2 do not fix the problem:**

**Step 3.** Remove and inspect the spread roll flow control cartridge for contamination or debris.

**If no contamination is found or the problem is not resolved:**

**Step 4.** Monitor auxiliary standby pressure and watch whether spread roll speed follows the pressure changes. For example, does the speed decrease when pressure decreases?

**If this pattern exists:**

**Step 5.** Remove and inspect the two load sense check valves for contamination, debris, worn springs, or pitted seat assemblies:
- On standard hopper units: the two load sense checks are on top of the conveyor manifold.
- On variable width hopper units: the two load sense checks are on top of the auger and spread roll manifolds.

---

## Problem 11 — Hydraulic Standby Pressure Fluctuating (Gauge Needle Is Not Steady)

**Symptoms:** The standby or load sense pressure gauge needle is unstable or bouncing.

**Cause:** This typically happens when too much oil volume is present in the load sense system, due to a missing or contaminated orifice or load sense check valve.

**Step 1.** Check the orifice in the load sense line fitting attached to the auxiliary hydraulic pump's load sense compensator valve:
- Confirm the orifice is installed. It is a set screw inside the fitting with a 0.040-inch hole drilled through it.
- Check the orifice for contamination.
- Verify the orifice size is 0.040 inches.

**Step 2.** Check compensator operation to confirm pressure responds to hydraulic system demand. See the operation manual for the standby pressure checking procedure.

**Step 3.** With the engine shut off, remove the load sense lines from the compensators and cap them off. Check and set standby pressure per the operation manual.
- **If proper standby pressure is achieved and remains steady** → Go to Step 3b.
- **If proper standby pressure cannot be achieved** → A pump or compensator issue is likely.

**Step 3b.** Reattach the load sense lines one at a time to determine which hydraulic manifold block has a bad or contaminated load sense check valve.

**Step 3c.** Inspect the identified load sense check valve for contamination. Replace if needed.

**Note for standard hopper units:** These have one auxiliary pump and one load sense line going to the conveyor manifold block. The load sense line between the conveyor block and the gate and spread roll manifold block must be removed and capped to isolate each block. Each block has "LS" stamped on it to identify the load sense port.

---

## Problem 12 — Overlap or Streak in Center When Hoppers Are Fully Extended

**Symptoms:** Material is either too heavy in the middle (overlap) or leaving a void down the center of the road (streak).

**If material is heavy in the middle (overlap):**
Slide the gate cut-off plate further into the hopper. Adjust both sides evenly.

**If material is leaving a void or streak down the center:**
Slide the gate cut-off plate further out of the hopper. Adjust both sides evenly. If the cut-off plate cannot be moved any further outward, adjust the hopper in-and-out cylinder at the rod end of the cylinder. Adjust both sides evenly.

---

## Problem 13 — No Gradability (Machine Cannot Climb Incline)

**Symptoms:** Machine cannot climb a grade that it should be able to handle.

**Grade capacity reference** (combined weight of chipspreader, dump truck, and aggregate at 80,000 pounds maximum; engine at 2,200 RPM; computer speed set point at 200 FPM):
- 2-wheel drive: 6 to 8 percent grade.
- 4-wheel drive with 107cc motors: 8 to 12 percent grade.
- 4-wheel drive with 160cc motors: 12 to 18 percent grade.
- Motor size in cc is stamped on the tag attached to the top of the drive motor.

**If the grade is within acceptable limits, continue:**

**Step 2 — For 2-Wheel Drive machines:**
- Disconnect the electrical connector attached to the front drive hydraulic motor servo and secure the wire.
- Test the unit on the grade with 80,000 pounds.

**Step 3 — For 4-Wheel Drive machines:**
- Disconnect the electrical connectors on both front and rear drive hydraulic motor servos and secure the wires.
- Test the unit on the grade with 80,000 pounds.

If disconnecting the servo connectors allows the machine to climb the grade, reconnect the servos one at a time to identify which motor servo is causing the problem. The servo is receiving power that is changing the position of the internal swash plate of the hydraulic motor.

**If disconnecting the servos does not improve performance:**

**Step 4.** Check and verify the hydrostat priority override (POR) hydraulic pressure.

**Step 5.** Check and verify hydrostat main hydraulic pressure in forward direction.

**Step 6.** Check and verify hydrostat main hydraulic pressure in reverse direction.

> Procedures for checking hydraulic pressures are in the operation manual for the machine.

---

## Problem 14 — Auxiliary Hydraulic Pressure Will Not Relieve

**Symptoms:** Pressure does not relieve after reaching main pressure. This creates heat, torque loss, and a hard start condition.

**Related problem:** If this is present, it can also cause Problem 5 (Hydraulic Oil Temperature Alarm).

**This issue is discovered while checking pressures on auxiliary hydraulic pumps 2 and 3 (Pump 2 on fixed head units).**

**To correct the problem:**

1. Shut off the machine.
2. Close and shut off the main hydraulic suction valve.
3. Locate and cap off the case drain at the pump.
4. Remove the compensator from the hydraulic pump or pumps.
5. Remove the load sense compensator cartridge.
6. Locate the 2mm allen head orifice inside the housing.
7. Remove the orifice.
8. Clean the orifice using a strand of primary wire or a torch cleaning kit (if small enough).
9. Re-install the orifice.
10. Re-install the cartridge.
11. Re-install the compensator.
12. Uncap and reinstall the case drain hose.
13. Open the suction valve.
14. Install an air regulator to the hydraulic tank through the vent filter connection.
15. Apply 3 to 5 pounds of pressure to the hydraulic system to push out any trapped air.
16. Start the machine and operate all functions to ensure hydraulic oil is circulating.
17. Check and adjust pressures per the operation manual. Make sure you have the correct manual.
18. Confirm that pressure relieves after main pressure is achieved.

**If pressure still cannot be adjusted:** The pump may have sustained damage and won't stroke. Isolation of the pumps will be necessary to determine which pump is affected.

---

## Problem 15 — Gates Will Not Operate (Hydraulic Buss Bar)

**Symptoms:** Gates do not respond to controls.

**Step 1.** Make sure the gate arming switches are turned ON. These are located on the operator's panel behind the joystick.

**Step 2.** Check all fuses and circuit breakers. Confirm there is power on both sides of the fuse holder assembly or circuit breaker assembly.

**Step 3.** Press the gate override button and test gate operation.
- **If the gate operates with override** → There is a likely electrical issue. Go to Steps 5 and 6.
- **If the gate does not operate with override** → There is a likely hydraulic issue. Go to Step 4.

**Step 4.** Check the hydraulic gate valve. Manually override the spool assembly to test operation.
- **If the gate operates with mechanical override** → Go to Step 5.
- **If the gate does not operate with mechanical override** → Refer to the operator's manual for hydraulic pressure testing.

**Step 5.** Check gate potentiometer or transducer adjustments. Refer to Problems 6 and 7.

**Step 6.** Check gate null and scale calibration. Refer to the operation manual for the correct procedure.

**Step 7.** Check the joystick center roller micro switch — is it activating?

**Step 8.** Check power across the gate switch in the joystick handle — is it activating?

**Step 9.** Check relays 2, 3, and 4:
- Relay 2 activates when the joystick is pushed out of neutral and the micro switch connects.
- Relay 3 then activates the left-hand gate when arming switch and gate switch are ON.
- Relay 4 activates the right-hand gate when arming switch and gate switch are ON.

**Important note — Right-hand gate hold feature:** The RH gate uses a gate hold feature, configured in computer setup screens. This is used for a straight-line start on Variable Hopper ChipSpreaders. This feature may prevent the gate from operating when the unit is parked and the operator is trying to clean out or leave a pile for hand work. If the FPM speed function is malfunctioning, the hold feature will not work and the RH gate will not open. Setting the gate hold to 0 in the setup screens will allow the RH gate to operate in manual mode.

---

## Problem 16 — Starter Cranks But Engine Does Not Start

**Symptoms:** Starter motor turns the engine over but the engine does not fire.

**Step 1.** Does the information display show "ENGINE CAN"? This means there is no CAN bus communication to the display.
- **If yes** → Go to Step 2.

**Step 2.** Check the E-Stop button. Make sure it was not bumped or accidentally pressed in. Twist it to pop it out and release it.

**Step 3.** Identify the engine type:
- Cummins QSB and Tier 3 engines have an Engine Controller that requires power to start.
- Older units with B and C series engines have mechanical injector pumps and no engine controllers.

**Step 4.** Check fuses for the Cummins Engine ECM controller. These fuses are near the power and ground distribution hub at the right rear corner of the Cummins engine. There may be up to 6 fuses depending on engine size. Verify fuse size against the machine schematic. Always replace with the same size fuse — never larger.

**Special note on inline yellow rubber fuse holders with glass fuses:** Pull the fuse holder apart and make sure the ring is fully over the end of the fuse — not just touching the metal tip. This matters because a partial contact will pass 12 volts DC until a load is placed on the circuit. Make sure the ring is tight and the solder joint at the wiring end is solid. Inspect, clean, repair, or replace connections as needed.

**Step 5.** Check the E-Stop switch connections. There may be a connection issue on the switch for the fuel solenoid.

**Step 6.** Check for an issue with the fuel solenoid on the Cummins engine.

---

## Problem 17 — Emergency Driveline Disengage Procedure

**IMPORTANT: This procedure is for emergency situations ONLY. Use it only to move the machine off the road or to slowly load it onto a transport trailer. It is NOT for travel or moving the machine any significant distance. Damage may occur if not performed correctly.**

**Purpose:** Allows the machine to be moved slowly (crawl speed) when a breakdown prevents normal movement.

**Required parts:**
- Two fittings: 04MB x 04MJ (Etnyre part number 9410200), one for each test port.
- One 04 x 65-inch hydraulic hose with 04FJX fittings (Etnyre part number 3181497).

**Step 1.** Install the two 04MB x 04MJ fittings — one in each test port of the high pressure distribution block bolted to the side of the pump. This block connects the main drive hydraulic hoses going to the drive motors. Remove the existing 04MB plug from both sides and install the new fittings.

**Step 2.** Install the 65-inch hydraulic hose across the two fittings. This creates a loop on the drive system, bypassing the pump and relief system.

**Step 3.** Disable or release the park brake unit, which is mounted in front of the drive motor on the front axle.

**Step 4.** If the engine does not run, or if there is a pump issue preventing park brake release, a porta-power unit will need to be modified with a 04 FJX connection and attached to the park brake unit to apply pressure. Approximately 280 to 400 PSI is required to release the park brake.

**Step 5.** If the engine runs and you are able to release the park brake, only the loop hose is required. An operator should place the controls in drive mode, push the joystick in the direction of movement, and steer the machine while moving very slowly off the road or onto a transport trailer.

---

## Computer Connector Quick Reference

**Computer model:** Rexroth MDC1 — connectors P1, P2, P3, P4 on the back of the unit. Ground connections are bolted to the computer base.

| Pin | Function |
|-----|----------|
| P1-PIN 6 | Left gate wiper (clear wire) |
| P1-PIN 7 | Right gate wiper (clear wire) |
| P1-PIN 10 | Fixed hopper or left gate positive (red wire) |
| P1-PIN 11 | Right gate positive (red wire) |
| P1-PIN 18 | Left gate negative (black wire) |
| P1-PIN 19 | Right gate negative (black wire) |
| P1-PIN 21 | Speed sensor power (12 VDC) |
| P2-PIN 2 | Oil pressure ground |
| P2-PIN 17 | Hydraulic oil temperature sensor |
| P2-PIN 18 | Oil pressure sender |
| P2-PIN 19 | Fuel sender |
| P2-PIN 20 | Water temperature sensor |
| P3-PIN 10 | Speed sensor signal (9–10 VDC) |
| P4-PIN 3 | Left gate open solenoid positive |
| P4-PIN 4 | Left gate close solenoid positive |
| P4-PIN 5 | Right gate open solenoid positive |
| P4-PIN 6 | Right gate close solenoid positive |

---

## Contact Information

**E.D. Etnyre & Co.**
1333 S. Daysville Road, Oregon, IL 61061

**Service Department:** 1-800-995-2116
**Fax:** 815-732-7400
**Website:** www.etnyre.com

> For any problem not resolved by the steps in this guide, direct the caller to contact the Etnyre service department directly.

---

*Document Reference: M-218-08R | Replaces M-218-08*
*Knowledge base version created: 2026-05-14*
