# Etnyre RoadSaver — Voice Agent Knowledge Base

**Version:** 2.0 (draft for Etnyre technical review) · **Built:** 2026-10-22 · **Scope:** RoadSaver truck-mounted slurry seal / micro-surfacing machines only

---

## 0. Read First — Scope, Sources, and Conventions

### 0.1 Source inventory

| Code | Document | Type | What it covers | Authority |
|---|---|---|---|---|
| **OM** | MO-RS-24, *RoadSaver Operations Manual — All RoadSaver Models* (132 pp.) | Manufacturer manual | Systems, controls (Mechanical / Electronic / C.A.N.), emulsion valves, calibration, start-up, safety, maintenance, slurry practice, "Solutions & Suggestions", troubleshooting (§13) | **Primary** |
| **PM** | M-RS3G-23, *RoadSaver IIIG Repair Parts Manual* (141 pp., updated 2026-04-28) | Manufacturer parts manual | IIIG component identification, hydraulic manifold & PVG valve, control panel layout, switch map, wiring legend | **Primary** (component ID only) |
| **ISSA** | MO-RS-ISSA-24, *Supplement to MO-RS-24* (86 pp.) | Industry guidelines bundled by Etnyre | ISSA A105 (Slurry Seal) and A143 (Micro Surfacing), test bulletins, additive-tank and dip-stick charts | **Primary** for job/spec questions; not machine-specific |
| **KBN** | `roadsaver-voice-agent-knowledge-base-09-16-2026.md` | Internal Etnyre notes (unreviewed draft — contains an "(Randy-Please edit)" marker) | Calibration notes, ratio meter, pugmill-won't-start procedure with pin legend, fluids guide, sales FAQs | **Secondary** — used only where it does not conflict with OM; flagged where it does |

> ⚠️ **No customer support call transcripts were present.** The connected `Etnyre` folder is empty, and the `RoadSaver` folder contains only the three PDFs, the 09-16 notes file, and photos. Everything below is therefore derived from manufacturer documentation and internal notes, **not** from call history. Section D (Support Call Insights) is structurally complete but carries zero call counts. When transcripts are supplied, re-run the analysis to add frequency data, real customer phrasing, and confirmed field fixes. See Section C, gap **G-01**.

### 0.2 Model and configuration key (use to scope every answer)

| Term | Meaning | Source |
|---|---|---|
| **RoadSaver II** | Uses a dedicated **side engine** (Cummins QSB3.3 Tier III, 110 HP, 4-cyl. diesel, left-side platform) to run all machine systems | OM 1-1; KBN |
| **RoadSaver IIIG** | No side engine. Machine systems run from the **truck engine via PTO** (KBN: Paccar MX). C.A.N. controls, DP610 display, 7-bank PVG valve | PM §2, §7, Fig 1-17; KBN |
| **Mechanical Flow Control** | Jackshaft & pugmill speed set with **black knobs** at bottom of panel | OM 1-7 |
| **Electronic Flow Control** | Jackshaft & pugmill speed set with **toggle switches** | OM 1-11 |
| **C.A.N. Flow Control** | **11-button keypads** (in-cab, hopper, rear operator panel), C.A.N. joysticks, auger keypads; speed changes require an **ENABLE** press | OM 1-15 to 1-22 |
| **Fender-mounted vs. low-mount emulsion pump** | Two different emulsion valve layouts and colour codes | OM 2-1 to 2-4 |
| **Two-pump vs. three-pump hydraulics** | On three-pump systems the pugmill and oil (emulsion) pump are on their own circuit | OM 1-1 |
| **Smart OPS** | On-screen production / calibration / diagnostics system (menu screens incl. Auto Calibrate, Diagnostics, Fault Screen, Sensor Frequency, Signals, Switch Verification, PPU Diagnostic) | OM 1-24 |

**Agent rule:** If the answer depends on configuration, **ask first**: *"Is your machine a RoadSaver II with the side engine, or a IIIG that runs off the truck?"* and, for controls, *"Do you change jackshaft speed with a knob, a toggle switch, or a keypad with rabbit and turtle buttons?"*

### 0.3 Customer vocabulary map (for retrieval)

| Customers may say… | Etnyre term |
|---|---|
| mixer, mixing box, paddles | **Pugmill** |
| rock, sand, aggregate | **Aggregate** |
| oil, asphalt, emulsion | **Emulsion** (asphalt emulsion) |
| sand belt, rock belt, conveyor | **Aggregate conveyor belt** ("Traction Master" conveyor) |
| sand door, rock gate, gate wheel | **Aggregate gate** (set with small wheel at operator station) |
| cement feeder, fines hopper | **Fines feeder** / dry additive system |
| sulfate, alum, set control, retarder | **Liquid additive** (commonly aluminum sulfate) |
| box, sled, spreader, drag box | **Spreader box** |
| chute flap, flipper | **Diverter** |
| mixer door | **Pugmill gate** |
| shaker, vibrator | **Vibrator beam** (hopper) / fines feeder vibrator |
| one button, auto start, sequencer | **1-button / automatic sequencing** |
| oil valve, three-way | **Three-way emulsion valve** (heat-jacketed, hydraulically positioned) |
| screen, computer, monitor | **Smart OPS display** (IIIG: DP610 C.A.N. display) |
| PTO switch | IIIG power take-off switch (replaces side engine) |

### 0.4 Voice-delivery conventions used in every entry

- **ASK:** = a question the agent asks. Ask **one at a time**, wait for the answer.
- **SAY:** = an instruction the agent gives. Give **one step at a time**, then confirm before continuing.
- **→** = decision branch based on the customer's answer.
- **[INTERNAL]** = for the agent's reasoning or human handoff only. Do not read aloud.
- **Confidence:** **High** = stated explicitly in manufacturer manual (OM/PM/ISSA). **Medium** = stated in internal notes (KBN) or combined from several manual statements. **Low** = logically implied but not explicitly documented — agent must present as a *possibility*, not a fix.
- **Resolution status:** Because there are no call transcripts, "confirmed" below means **"documented by the manufacturer as the corrective action"**, not "confirmed successful in the field".

### 0.5 Global safety rules (apply to every entry — agent must enforce)

1. **Never** guide a customer to put hands, tools, or objects in the **pugmill** or **fines feeder** while the engine is running (or, on IIIG, while the PTO is engaged). Pugmill covers come off only after the engine is shut down and the engine control cover is secured and locked closed. *(OM 1-5, 6-2, 7-1)*
2. **The machine can start and stop without warning.** Box lift, side-shift, and emulsion valve cylinders may actuate without warning. *(OM 6-2)*
3. For any hands-on inspection: shut down, remove keys, put a **"Do Not Operate" tag** on the start switch. *(OM 6-1)*
4. **Hydraulic or fluid leaks:** search with a **board/cardboard**, never a hand. Fluid injection under the skin is a medical emergency. Do not bend or strike high-pressure lines. *(OM 6-1)*
5. Compressed air: face shield, protective clothing, **never above 30 PSI**. *(OM 6-1)*
6. **Never close an emulsion valve before the emulsion pump stops** — lines, hoses, or fittings can split under pressure. *(OM 3-3)*
7. **Never run the emulsion, water, or additive pumps dry.** *(OM 5-1)*
8. **Welding:** disconnect the battery and turn all switches OFF first; **never use an AC welder** (destroys sensors). *(OM 6-1)*
9. Nobody rides on the hopper, top of the machine, or the spreader box. No one moves the truck without the operator's clearance. *(OM 6-2, 8-3)*
10. Additives (sulfates, amines) are corrosive — eye and hand protection; read the SDS. *(OM 6-2, 11-1)*
11. Hot surfaces: engine-heated emulsion pump jackets and three-way valve. *(OM 1-1, 5-1; PM decals)*

**Agent behaviour:** If the customer describes being *in* the hopper, reaching into the pugmill, working under a raised box, or chasing a leak by hand, **stop troubleshooting and give the safety instruction first.**

### 0.6 Global escalation rule

Stop and route to Etnyre technical support (or a qualified technician) when **any** of these is true:
- The fix requires opening hydraulic lines, replacing cartridges/coils, internal pump/motor/gearbox work, wiring repairs, or controller/display replacement.
- A safety-critical function (pugmill kill switch, gate, box lift, emulsion valve) behaves unexpectedly.
- The Smart OPS/C.A.N. display shows a fault code (no fault-code dictionary is available — see gap G-03).
- Two or three documented checks have not solved the problem.
- The customer asks for a specification, setting, or part number not contained in this knowledge base.

[INTERNAL] Contact details differ across sources and must be validated before the agent speaks them: OM lists Etnyre International, 1333 S. Daysville Rd, Oregon, IL 61061, 815-732-2116. PM and the RoadSaver II Troubleshooting Guide cover list 3650 Sabin Brown Rd, Wickenburg, AZ 85390; PM cover lists 1-916-826-1700. (Gap G-14.)

---

# SECTION A — TROUBLESHOOTING GUIDE

**Index**

| ID | Subsystem | Problem |
|---|---|---|
| TS-01 | Pugmill | Pugmill won't turn on / won't run |
| TS-02 | Pugmill | Pugmill jammed or stalled by rock / foreign object |
| TS-03 | Emulsion | Emulsion pump won't turn / no emulsion at start-up |
| TS-04 | Emulsion | Emulsion flow inconsistent, surging, or low |
| TS-05 | Emulsion / Calibration | Emulsion calibration numbers don't repeat |
| TS-06 | Water | No water or low water to the pugmill |
| TS-07 | Water | Sprinklers / spray bars weak or not spraying |
| TS-08 | Liquid additive | No liquid additive flow |
| TS-09 | Aggregate / Conveyor | Aggregate not feeding or feeding unevenly (bridging) |
| TS-10 | Controls / Aggregate | Machine shuts itself down in 1-button (automatic) mode |
| TS-11 | Conveyor | Aggregate belt tracking off, slipping, or damaged |
| TS-12 | Fines feeder | Cement / dry additive not feeding, or fines vibrator issues |
| TS-13 | Controls / Sensors | Smart OPS readings missing, zero, or erratic |
| TS-14 | Hydraulics | Hydraulic filter gauge in yellow/red, or hydraulic oil running hot |
| TS-15 | Hydraulics / Valves | A manifold function won't activate (water pump, vibrator, fines feeder, additive pump, emulsion valve) |
| TS-16 | Spreader box | Box won't raise/lower or side-shift |
| TS-17 | Pugmill gate / Diverter | Gate or diverter not responding |
| TS-18 | Spreader box augers | Box augers won't run or run the wrong way |
| TS-19 | C.A.N. controls | Can't change jackshaft / pugmill speed on keypad |
| TS-20 | Engine (RS II) | Side engine start-up issues, low-oil alarm, air filter indicator |
| TS-21 | Electrical | No power to machine controls |
| TS-22 | Calibration | Aggregate or fines calibration results inconsistent |
| TS-23 | Mix quality | Mix too wet or too dry |
| TS-24 | Mix quality | Mix breaking / setting in the box too fast |
| TS-25 | Mix quality | Bad mix at the start or end of a pass |
| TS-26 | Finished mat | Streaks, drag marks, grooves in the mat |
| TS-27 | Finished mat | Raveling (rock coming loose) |
| TS-28 | Finished mat | Bleeding / fat / shiny black spots |
| TS-29 | Finished mat | Colour differences between passes or machines |
| TS-30 | Mix quality | False slurry / false break |
| TS-31 | Spreading | Uneven mat on crowns, banked curves, or steep grades |
| TS-32 | Jobsite | Slurry tracking on tires or onto concrete |
| TS-33 | Jobsite | Rain on fresh slurry |
| TS-34 | Finished mat | Power-steering / scuff marks |
| TS-35 | Surface prep | Problems laying over crack sealer, thermoplastic, or old seal coats |

> **Note on requested categories:** The RoadSaver documentation describes no *hopper raise/lower* function. The raise/lower hydraulics on a RoadSaver are the **spreader box lift arms** and **side shift** (TS-16). If a customer says "hopper won't raise", the agent should clarify whether they mean the **box lift**, or whether their unit is a non-RoadSaver Etnyre machine (out of scope). There is no "spread roll" on a RoadSaver; aggregate distribution in the box is handled by the **diverter** and optional **box augers** (TS-17, TS-18, TS-31).

---

## A1. PUGMILL

### TS-01 — Pugmill won't turn on

**Applicable models:** All. Switch-level pin legend (Step 6) is from KBN and applies to the panel layout shown there (RoadSaver II / IIIG with signal screens) — verify per machine.

**Customer questions**
- "My mixer won't come on."
- "I push the pugmill button and nothing happens."
- "The paddles aren't turning."
- "Pugmill's dead but everything else runs."

**Symptoms:** Pugmill ON pressed; no paddle rotation; direction indicator lights may be off.

**Possible causes (most to least likely)**
1. **Pugmill Master Kill Switch** (guarded switch) is OFF. *(OM 1-8, 5-2)*
2. **Direction switch in Neutral** (centre). *(OM 1-8)*
3. Jackshaft/pugmill hydraulic system not powered (engine not running / PTO not engaged). *(OM 5-1)*
4. Pugmill speed set to minimum. *(OM 5-2)*
5. Switch, wiring, or signal fault at the pugmill push-button / F-N-R switch. *(KBN)*
6. Mechanical jam — see TS-02.

**Diagnostic questions**
1. ASK: "Is the engine running — or on a IIIG, is the PTO switch on?"
2. ASK: "Is the red-covered pugmill kill switch flipped up to ON?"
3. ASK: "Is the pugmill direction switch pulled back toward you, in Forward?"
4. ASK: "Is the blue or green 'forward' light on above the pugmill switch?"
5. ASK: "Does the pugmill try to turn and stop, or does it do nothing at all?"

**Step-by-step**
1. SAY: "Make sure the engine is running, or the PTO is engaged on a IIIG." → If not, start per normal start-up (FAQ OP-01) and retry.
2. SAY: "Check the guarded pugmill master kill switch. It must be ON." → If it was OFF: turn ON, retry. Resolved? Done.
3. SAY: "Pull the pugmill direction switch back toward the operator — that's Forward." The blue/green light should come on. → Light on but no rotation: go to 4. Light never comes on: go to 6.
4. SAY: "Turn the pugmill speed control up a little." *(Knob, toggle, or keypad — on C.A.N. press ENABLE first; see TS-19.)* Normal operating speed is 90–110 RPM for standard Type II slurry or micro. → Turns: resolved.
5. ASK: "When you push ON, does it hum or try to move, then stop?" → Yes: suspect jam → **TS-02**.
6. **Signal-screen check (KBN procedure):**
   a. SAY: "On the main computer screen, press 7 for the signal screens, then scroll to the pugmill signals."
   b. SAY: "Turn on the pugmill power under the red switch cover, pull Forward/Reverse toward the rear of the machine, then press pugmill ON/OFF."
   c. Look for: **"Pugmill ON" indicator green.**
   d. SAY: "Now push the direction switch toward the front for Reverse and hold it." Look for: **"Pugmill ON" and "Pugmill REVERSE" both green.**
   → Both indicators behave correctly but pugmill doesn't turn: inputs are reaching the controller → hydraulic/valve/motor side → **escalate**.
   → An indicator does not light: switch or wiring fault → step 7.
7. **Qualified technician only:** remove the tail lights above the switches and test the switch with a volt meter or test light.
   [INTERNAL] KBN pin legend: SW4-P1 12 V · SW4-P2 supply to PM push-button · SW10-P2 inlet to PM push-button · SW10-P1 outlet to PM F-N-R switch · SW3-P5/P2 inlet from PM push-button · SW3-P1/P6 PM reverse · SW3-P3 PM forward · SW3-P4 PM reverse light.

**Recommended resolution:** Restore kill switch / direction / speed settings. If signal check fails, replace or repair the faulty switch or wiring (technician). If signals are good, escalate for hydraulic diagnosis.

**Safety:** Never reach into the pugmill to "help it turn". Reverse is spring-loaded and must be held — release to stop.

**Escalation:** Signal screen shows correct inputs but no rotation; any wiring work; repeated stalling.

**Source & confidence:** OM 1-5, 1-8, 5-2; KBN "Pugmill will not turn on". Documented procedure; not field-confirmed. Multiple sources agree on kill switch/direction. **Confidence: High (steps 1–5), Medium (steps 6–7, KBN only).** Gap: screen number "7" and pin legend need validation per model (G-05).

---

### TS-02 — Pugmill jammed or stalled by rock or foreign object

**Applicable models:** All.

**Customer questions**
- "Something's stuck in the mixer."
- "Pugmill locked up mid-pass."
- "A big rock jammed the paddles."

**Symptoms:** Pugmill stops or labours; unusual knocking; may coincide with oversized rock or clumped aggregate.

**Possible causes:** Oversized rock or foreign object lodged between paddles *(OM 5-2, 10-6)*; agglomerated aggregate balls *(OM 10-6)*; tools dropped in hopper *(OM 8-10: never put squeegees/shovels in the hopper)*.

**Diagnostic questions**
1. ASK: "Did it stop suddenly, like something caught?"
2. ASK: "Is the jackshaft and material still feeding?"

**Step-by-step**
1. SAY: "First, stop the material — aggregate, water, emulsion, and additive off — and close the pugmill gate."
2. SAY: "Hold the pugmill direction switch forward toward the front of the machine — that's Reverse — for a moment, then release it." The red reverse light should be on while held. *(Reverse is intended only to clear foreign objects.)*
3. SAY: "Release to neutral, then switch back to Forward." → Runs freely: resolved; inspect aggregate source (TS-26).
4. → Still jammed: SAY: "Shut the engine down, lock the engine control cover, take the keys, and tag the start switch before anyone opens a pugmill cover."
5. → Removal of the object with the machine locked out is a qualified-personnel task. Escalate if paddles, tips, or shafts look damaged.

**Recommended resolution:** Momentary reverse to free; if unsuccessful, full lockout and manual removal. Screen aggregate if oversize rock recurs *(OM 10-6)*.

**Safety:** Absolutely no hands in pugmill with engine running/PTO engaged. Kill switch is not a substitute for engine shutdown before opening covers.

**Escalation:** Visible damage to paddles/carbide tips/shafts; timing-gear noise; repeated jams.

**Source & confidence:** OM 1-5, 1-8, 5-2, 10-6. **Confidence: High.** Gap: no documented procedure for paddle/tip replacement or timing gear inspection beyond "inspect every 500 h" (G-08).

---

## A2. EMULSION SYSTEM

### TS-03 — Emulsion pump won't turn / no emulsion at start-up

**Applicable models:** All. Valve numbering differs: **fender-mounted pump** vs **low-mount pump**.

**Customer questions**
- "Oil pump won't turn when I start up."
- "No emulsion going to the mixer."
- "Pump's locked up first thing in the morning."
- "I hit the oil button and nothing comes out."

**Symptoms:** Jackshaft engaged but emulsion pump doesn't rotate; or pump turns but nothing circulates/delivers.

**Possible causes**
1. **Machine not warmed up.** The emulsion pump and three-way valve are heated by engine coolant; the pump will not work until hot water circulates through its jackets. Required: **160 °F / 71 °C**. *(OM 5-1, 5-2)*
2. Tank **supply/return valves** not in normal-operating position. *(OM 2-1–2-4, 5-1)*
3. Jackshaft not engaged. *(OM 5-2)*
4. Three-way valve set to recirculate (normal when idle). *(OM 1-2)*
5. Blockage — asphalt slugs or buildup in lines/valves. *(OM 3-5, 13-1)*

**Diagnostic questions**
1. ASK: "Is this a side-engine machine or a PTO machine?"
2. ASK: "How long has it been running? Is the engine temperature up to about 160 degrees?"
3. ASK: "Is the jackshaft switched on?"
4. ASK: "Is your emulsion pump up on the fender, or mounted low under the tank?"
5. ASK: "Can you read me the colours of the valves that are open?"

**Step-by-step**
1. SAY: "Let the machine warm up. Side engine: run at about 1,000 RPM until the engine reaches 160 degrees. PTO machine: turn on the pump heater switch in the cab." → Pump turns once warm: resolved (normal cold-start behaviour).
2. SAY: "Check the valves for normal operation."
   - **Fender-mounted pump:** blue valve 1 and red valve 4 **open**; all others closed and cam-locked.
   - **Low-mount pump:** blue valves 1 and 2 and red valve 4 **open**; all others closed and cam-locked; uncoloured valve 6 **closed**.
   → Corrected a valve: retry.
3. SAY: "Push the Jackshaft button." Emulsion should circulate tank → pump → back to tank. → Circulates: system OK; emulsion to pugmill is controlled by the oil/emulsion button or 1-button start.
4. → Warm, valves right, jackshaft on, still no flow: likely blockage → **TS-04**.

**Recommended resolution:** Warm-up to 160 °F; correct valve line-up; clear blockage.

**Safety:** Hot jackets and valve. Never run pump dry. Never close a discharge valve with the pump running.

**Escalation:** Pump hot, valves correct, no rotation (possible mechanical seizure / hydraulic drive fault). Pump internal service → manufacturer's pump manual (not supplied — G-09).

**Source & confidence:** OM 1-2, 2-1–2-4, 5-1, 5-2. **Confidence: High.**

---

### TS-04 — Emulsion flow inconsistent, surging, or low

**Applicable models:** All.

**Customer questions**
- "Oil flow keeps changing."
- "Emulsion's surging."
- "Not getting enough oil — mix looks lean."
- "Pump sounds like it's cavitating."

**Symptoms:** Emulsion delivery varies; mix colour/richness changes; calibration won't repeat (see TS-05); pump noise.

**Possible causes**
1. **Blockage in lines** — asphalt slugs, "schmeg", buildup on valve faces. *(OM 3-5, 13-1 — "usually a blockage")*
2. **Pump cavitation** — inlet/outlet ports clogged. *(OM 3-5)*
3. Emulsion that has stood 2–3+ days developing sieve, pellets, or skin. *(OM 9-7)*
4. Cold machine (pump jackets not hot). *(OM 5-1)*
5. Pump mechanical wear after starvation or misuse. *(OM 3-5)* KBN adds: variable pumps that change flow with RPM indicate starvation/worn tolerances.

**Diagnostic questions**
1. ASK: "Is the machine fully warmed up?"
2. ASK: "How long has this load of emulsion been in the tank or tanker?"
3. ASK: "Are you seeing strings or little balls of asphalt in the mat?"
4. ASK: "Does the flow change when the jackshaft speed changes?"

**Step-by-step**
1. Confirm warm-up (TS-03 step 1).
2. → Old emulsion or shot/strings in the mat: SAY: "The emulsion may be developing sieve. Check the tanker. Minor cases can be filtered and recirculated." Suggest contacting the emulsion supplier.
3. SAY: "The manual's first fix for inconsistent flow is to flush the system with hot liquid asphalt." → Improves: resolved.
4. → Hot asphalt unavailable or didn't work: "The lines need to be removed and cleaned." For heavy buildup, the tank is entered **empty** through the clean-out and scraped, and all lines tank→pump→pugmill removed and cleaned.
   [INTERNAL] Tank entry is a confined-space activity — agent must not coach this; refer to customer's confined-space procedures and qualified personnel.
5. → Flow varies with RPM (variable-pump machines): KBN suggests setting the pump at 100 % and re-testing (~15.1 expected); if accurate there, tolerances need resetting at the working % → **call the shop/Etnyre**.

**Recommended resolution:** Flush with hot asphalt; else remove and clean lines; clean tank if needed; address pump wear via Etnyre.

**Safety:** Shut down and relieve pressure before opening any emulsion line. Hot material. Tank entry = confined space.

**Escalation:** Suspected pump wear, any pump disassembly, any need for tank entry guidance.

**Source & confidence:** OM 3-5, 9-7, 13-1; KBN. **Confidence: High** for blockage/flush/clean; **Medium** for the variable-pump check (KBN only; conflicts with OM statement that newer pumps are fixed — see C-03).

---

### TS-05 — Emulsion calibration numbers don't repeat

**Applicable models:** All (Smart OPS Auto Calibrate on machines so equipped).

**Customer questions**
- "My three oil calibration runs don't match."
- "Calibration's all over the place."
- "Pounds per count keeps changing."

**Symptoms:** Lbs (kg) per count differs across runs by more than the **2 %** tolerance (each run within 2 % of the average of three runs of at least 300 gal / 1,135 L).

**Possible causes — "the obvious"** *(OM 3-5)*
1. Weighing error: truck not straight on scale, misread scale, **driver in the truck one time and out the next**.
2. Tanker hose **not pre-filled** before run 1.
3. Discharge valve not opened just before / closed just after the pump start/stop → siphoning.
4. Head-pulley reference counts misread.
5. Scale resolution (10/20 lb rounding) with too small a sample. *(OM 3-2)*

**"The not so obvious"** *(OM 3-5)*
6. Asphalt slugs/crud in lines or on valve faces (TS-04).
7. Pump cavitation — ports clogged.
8. Pump mechanical damage from starvation/misuse.

**Diagnostic questions**
1. ASK: "Was the same driver in the truck for every weighing?"
2. ASK: "Did you pump off enough to fill the hose before the first run?"
3. ASK: "Who opens and closes the valve at the hose connection, and is it timed with the pump?"
4. ASK: "What does your scale read to — nearest pound, ten, or twenty?"
5. ASK: "How big was each run?"

**Step-by-step**
1. Correct any procedure issue from questions 1–5 and re-run three tests. (Full procedure: FAQ CAL-02.)
2. → Procedure good, still inconsistent: treat as blockage/cavitation → TS-04.
3. → Still inconsistent after cleaning: escalate (pump condition).

**Recommended resolution:** Fix procedure; clean system; escalate pump issues.

**Safety:** The valve must **never** be closed before the pump stops — lines can fracture.

**Escalation:** Clean system + correct procedure still out of tolerance.

**Source & confidence:** OM 3-2–3-5; KBN repeats. **Confidence: High.**

---

## A3. WATER SYSTEM

### TS-06 — No water or low water to the pugmill

**Applicable models:** All. Water valve is **air-actuated** (butterfly), so it depends on **truck air pressure**.

**Customer questions**
- "No water going in the mix."
- "Water flow's really low."
- "Water button's on but nothing."
- "Mix is coming out dry."

**Symptoms:** Water meter (Smart OPS, GPM/LPM) reads zero/low; mix dry.

**Possible causes** *(OM 13-1 unless noted)*
1. **Diaphragm valve closed** (1½" valve, yellow internal position indicator visible from rear). *(OM 1-4, 5-3)*
2. **No truck air pressure** — air actuates the water valve.
3. **Debris around the foot valve / 2" strainer** inside the water tank.
4. Water pump switch in **neutral**, or in auto with the jackshaft off. *(OM 1-8, 5-3)*
5. Tank empty / low (check sight gauge). *(OM 1-3)*
6. Pump/valve not energised — see TS-15 manual override test. *(OM 1-1)*

**Diagnostic questions**
1. ASK: "Is there water in the tank? What does the sight gauge show?"
2. ASK: "Is the truck building air pressure?"
3. ASK: "Where's your water pump switch — back for automatic, middle, or forward for manual?"
4. ASK: "From the back of the machine, can you see the yellow indicator on the diaphragm valve — is it open?"

**Step-by-step**
1. SAY: "Check the water sight gauge." → Empty: refill. Never run the pump dry.
2. SAY: "Make sure the truck has air pressure up." → Low air: build air, retry.
3. SAY: "Set the water pump switch back to Automatic — then the pump runs whenever the jackshaft turns. Or forward to Manual to run it on its own."
4. SAY: "Open the diaphragm valve. For practice mix, the manual starts at three-quarters of a turn open." Watch the yellow indicator.
5. → Still low: SAY: "With the pump off, check the strainer and foot valve inside the water tank for leaves or debris." Clean.
6. → Still no flow: perform TS-15 manual override test on the water pump cartridge; escalate if pump runs but no flow.

**Recommended resolution:** Restore air, open diaphragm valve, correct switch mode, clean strainer.

**Safety:** Pump off before reaching into tank. Don't run pump dry.

**Escalation:** Pump not running with switch/override; air valve not actuating with good air pressure.

**Source & confidence:** OM 1-3, 1-4, 1-8, 5-3, 13-1. **Confidence: High.**

---

### TS-07 — Sprinklers / spray bars weak or not spraying

**Applicable models:** All. Four electrically controlled valves at rear of water tank: front bar, left seam, right seam, tire sprays. C.A.N. units use keypad buttons (cab and rear panel).

**Customer questions**
- "Front spray bar isn't wetting the road."
- "Tire sprayers quit."
- "Seam spray is just dribbling."

**Possible causes** *(OM 13-1)*
1. Sprinkler switches off (master + selector + tire).
2. **Sprinkler filter** (brass in-line strainer at the water pump) dirty.
3. Clogged **sprinkler tips**.
4. Water pump not running / no water (TS-06).

**Diagnostic questions**
1. ASK: "Which sprays aren't working — front, left, right, or tires?"
2. ASK: "Is the sprinkler main switch on?" *(C.A.N.: "Is the red light on next to that sprinkler button?")*
3. ASK: "Is water flowing to the pugmill normally?"

**Step-by-step**
1. SAY: "Turn on the sprinkler main switch, then the selector for the sprays you want." *(Mechanical/Electronic rear panel: left = main, centre = up-right / centre-both / down-left, right = tires. C.A.N.: press FRONT ON etc.; red LED stays on.)*
2. → No water anywhere: TS-06.
3. SAY: "With the pump off, clean the sprinkler filter next to the water pump."
4. SAY: "Remove and clean the sprinkler tips."
5. → One spray dead, others fine, filter & tips clean: possible solenoid/wiring → escalate.

**Safety:** Pump off before opening filter.

**Source & confidence:** OM 1-4, 1-9, 1-15, 1-19, 13-1. **Confidence: High.**

---

## A4. LIQUID ADDITIVE SYSTEM

### TS-08 — No liquid additive flow

**Applicable models:** All. Tank ~80 gal (fender), hydraulic pump, flow meter usable 0.5–5.0 GPM.

**Customer questions**
- "Sulfate isn't flowing."
- "Additive meter reads zero."
- "Set control isn't going in — mix is setting up fast."

**Possible causes** *(OM 13-1 unless noted)*
1. **Valve at tank** not on.
2. **Air lock** in pump.
3. **Additive stainless filter** clogged.
4. Metering valve at base of the additive meter closed. *(OM 5-3)*
5. Additive button not on. *(OM 5-3)*

**Diagnostic questions**
1. ASK: "Is there additive in the tank?"
2. ASK: "Is the valve at the bottom of the tank turned on?"
3. ASK: "Did you just refill or work on the additive system?" (air lock more likely)

**Step-by-step**
1. SAY: "Turn the tank valve on."
2. SAY: "Press the Additive button, then open the valve at the base of the additive meter." Typical starting flow: 2 GPM (practice-mix example uses 2.5 GPM).
3. → No flow: SAY: "Loosen the bleed screw on the additive pump to bleed off trapped air, then snug it back." Wear eye and hand protection.
4. → Still none: SAY: "Shut it off and clean the stainless additive filter."
5. → Still none: TS-15 manual override on additive cartridge; escalate.

**Safety:** Aluminum sulfate is corrosive — goggles and gloves; read the SDS.

**Escalation:** Pump not turning with override; meter fault.

**Source & confidence:** OM 1-5, 5-3, 5-4, 6-2, 13-1. **Confidence: High.**

---

## A5. AGGREGATE, CONVEYOR & FINES FEEDER

### TS-09 — Aggregate not feeding or feeding unevenly (bridging)

**Applicable models:** All. Hopper 12 yd³ (9.2 m³); V-shaped vibrator beam suspended by chains.

**Customer questions**
- "Rock's hanging up in the hopper."
- "Belt's running but no sand coming through."
- "Aggregate flow keeps cutting in and out."

**Possible causes**
1. Material **bridging** in hopper — use vibrator. *(OM 1-4, 1-9, 1-22)*
2. **Aggregate gate** set too low / set screw loose. *(OM 1-4, 5-4)*
3. Wet, clumped, or low-sand-equivalent aggregate balling. *(OM 10-6)*
4. Conveyor not running (sand conveyor button off; jackshaft off). *(OM 5-2)*
5. Ice on conveyor in cold weather. *(OM 7-3)*

**Diagnostic questions**
1. ASK: "Is the belt moving?"
2. ASK: "Is there plenty of rock in the hopper but it's not dropping?"
3. ASK: "What's your gate set at?"
4. ASK: "Is the stockpile wet or clumpy?"

**Step-by-step**
1. → Belt not moving: SAY: "Make sure the jackshaft is on, then press Sand Conveyor." Still not moving → escalate (conveyor drive / hydraulic).
2. SAY: "Press and hold the vibrator button on the right joystick to shake the material loose. Release to stop." → Flows: resolved; use as needed.
3. SAY: "Measure your gate opening with a tape and make sure the set screw is tight."
4. → Clumpy aggregate: stockpile handling problem; screening may be required.

**Safety:** **Never** climb into or sit in the hopper with the engine running. Never use a bar/shovel in the hopper while running — and never store squeegees/shovels in it (can cut belt).

**Escalation:** Conveyor won't run; vibrator inoperative (→ TS-15).

**Source & confidence:** OM 1-4, 1-9, 1-22, 5-4, 6-2, 7-3, 8-10, 10-6. **Confidence: High.**

---

### TS-10 — Machine shuts itself down in 1-button (automatic) mode

**Applicable models:** All with automatic sequencing / 1-button start.

**Customer questions**
- "Everything shuts off by itself in the middle of a pass."
- "Auto mode keeps cutting out."
- "One-button start stops after a few seconds."

**Symptoms:** Aggregate, water, emulsion, additive stop together (sequenced shutdown).

**Possible causes**
1. **Aggregate below the preset level for more than 3 seconds** at the gate sensor → system initiates sequenced shutdown (designed behaviour). *(OM 1-4)*
2. Bridging (TS-09) or empty hopper.
3. Sensor out of position or failed (TS-13).

**Diagnostic questions**
1. ASK: "Is the hopper getting low, or is rock hanging up?"
2. ASK: "Does it happen right when flow at the gate drops?"

**Step-by-step**
1. SAY: "That shutdown is a safety feature — if rock at the gate drops low for about three seconds, the machine shuts the mix off so you don't lay lean material."
2. Check hopper level and bridging (TS-09). Restart with 1-button.
3. → Shuts down with good aggregate flow: suspect gate sensor → TS-13; escalate.

**Source & confidence:** OM 1-4. **Confidence: High** for the behaviour; **Low** for sensor-fault diagnosis (sensor location/adjustment not documented — G-04).

---

### TS-11 — Aggregate belt tracking off, slipping, or damaged

**Applicable models:** All ("Traction Master" conveyor, hydraulically driven through jackshaft).

**Customer questions**
- "Conveyor belt is walking to one side."
- "Belt's rubbing the side."
- "Belt got cut."

**Possible causes:** Belt tension/alignment drift (check **each load during first week**); road **crowns** shifting alignment *(OM 8-6)*; worn side rubbers/gate rubbers; tools in hopper cutting belt *(OM 8-10)*.

**Diagnostic questions**
1. ASK: "Is this a new machine — first week or so?"
2. ASK: "Is the belt drifting, slipping, or physically damaged?"

**Step-by-step**
1. SAY: "Check belt position and tension. If it needs adjustment, make small, even adjustments." (No take-up procedure or tension value is documented — technician task.)
2. SAY: "Check it daily — working on crowned roads can move it out of alignment."
3. Inspect conveyor and side rubbers / gate side rubbers for wear (500-h item).
4. Cuts/damage → escalate for replacement.

**Safety:** Lock out before touching belt or rollers.

**Source & confidence:** OM 5-4, 7-2, 8-6, 8-10; calibration prerequisite OM 3-2. **Confidence: Medium** (what to check is documented; *how* to adjust is not — G-07).

---

### TS-12 — Cement / dry additive not feeding, or fines vibrator issues

**Applicable models:** All with fines feeder (7 ft³ hopper, hydraulic auger, anti-bulking device, hydraulic vibrator).

**Customer questions**
- "Cement isn't feeding."
- "Fines feeder isn't turning."
- "Fines vibrator won't shut off / won't come on."

**Possible causes**
1. Fines feeder switch: **Auto** runs only when the conveyor belt moves; Neutral = off; Forward = manual. *(OM 1-8)*
2. Fines feeder **speed/ratio set too low**. *(OM 1-7, 3-7)*
3. Hopper empty / cement bridged.
4. **Fines vibrator** runs only with the hopper vibrator button and only if its **two-position hydraulic ball (vent) valve** (rear of liquid additive tank) directs oil to it. *(OM 1-5, 5-3)*

**Diagnostic questions**
1. ASK: "Where's your fines feeder switch — auto, middle, or manual?"
2. ASK: "Is the belt running?" (Auto requires it.)
3. ASK: "Is the problem the auger, or the fines vibrator?"

**Step-by-step**
1. SAY: "In Auto, the fines feeder only runs when the conveyor belt is moving." Start belt and recheck.
2. SAY: "Turn up the fines feeder speed control beside the hopper and watch the speed on the Smart OPS screen."
3. Vibrator: SAY: "Check the two-position hydraulic valve at the back of the liquid additive tank. One position sends oil to the fines vibrator; the other sends it back to tank and turns that vibrator off."
4. → Auger won't run in Manual: TS-15 override; escalate.

**Safety:** **Never** put hands or objects in the fines feeder with engine running.

**Source & confidence:** OM 1-4, 1-5, 1-7, 1-8, 5-3, 6-2. **Confidence: High.**

---
## A6. CONTROLS, SENSORS & SMART OPS

### TS-13 — Smart OPS readings missing, zero, or erratic

**Applicable models:** All with Smart OPS / C.A.N. display. Rates are read from speed/flow sensors: jackshaft/head pulley, water paddle-wheel sensor, additive flow monitor, fines feeder speed, pugmill sensor.

**Customer questions**
- "Water rate shows zero but water is flowing."
- "Jackshaft RPM is jumping around."
- "My totals don't make sense."
- "Screen's showing a fault."

**Possible causes** *(OM 13-1)*
1. External **sensor loose or too far from its target wheel** — must be tight and **within 1/8"** of the wheel.
2. Sensor/wiring failure.
3. Meter power switch off. *(OM 1-8)*
4. Calibration values wrong/unlocked edits. *(OM 4-2)*

**Diagnostic questions**
1. ASK: "Which reading is wrong — water, additive, jackshaft, fines, or pugmill?"
2. ASK: "Is it reading zero, or jumping around?"
3. ASK: "Is there a fault message on the screen? Can you read it to me?"

**Step-by-step**
1. SAY: "Make sure the meter power switch is on."
2. SAY: "Open the Diagnostics screen and check the Fault Screen." Record any code. [INTERNAL] No fault-code list exists in sources — do not interpret codes; capture and escalate.
3. SAY: "Diagnostic steps differ by function, so let's focus on just the one reading." (OM 13-1.)
4. For external sensors — SAY (machine shut down): "Check that the sensor is tight and sits within one-eighth of an inch of the wheel it reads." → Adjust, retest via **Sensor Frequency** screen.
5. → Still wrong: SAY: "Etnyre needs to look at this one." Escalate with function name, symptom, and fault text.

**Safety:** Shut down before touching sensors near rotating parts.

**Escalation:** Always after step 4 fails; any fault code.

**Source & confidence:** OM 1-24, 13-1. **Confidence: High** for steps; **gap** — sensor locations, Signals/Switch Verification/PPU Diagnostic screen use not documented in supplied files ("Production Tracking Screens" booklet missing — G-02).

---

### TS-19 — Can't change jackshaft or pugmill speed on the C.A.N. keypad

**Applicable models:** **C.A.N. Flow Control only.**

**Customer questions**
- "Rabbit and turtle buttons don't do anything."
- "Speed won't change."
- "Pugmill speed is stuck."

**Cause:** Speed changes require pressing **SPEED UP/DOWN ENABLE** first. The enable **resets to off after a few seconds** for safety (LED goes off). *(OM 1-16, 1-19)*
[INTERNAL] OM text is internally inconsistent on what the lit LED means ("LED will remain on to show the operator that the speed can not be changed") — likely an editorial error; button operation text says press once to turn on, LED on, resets off. Flag C-07.

**Step-by-step**
1. SAY: "Press the speed enable button once — the red light comes on."
2. SAY: "Right away, press the rabbit side to speed up or the turtle side to slow down."
3. SAY: "If you wait, the enable turns itself off after a few seconds — just press it again."
4. → Still no change: check the reading on screen; escalate.

**Source & confidence:** OM 1-16, 1-19. **Confidence: High.**

---

## A7. HYDRAULIC SYSTEM

### TS-14 — Hydraulic filter gauge in yellow or red, or hydraulic oil running hot

**Applicable models:** All. Reservoir 95–120 gal, filled to ~85 %; one or two return filters with differential-pressure gauge.

**Customer questions**
- "Filter gauge on the hydraulic tank is in the yellow."
- "Hydraulic oil seems hot."
- "Do I need to change the hydraulic filter?"

**Gauge meaning** *(OM 1-1)*: **Green** = normal · **Yellow** = filters becoming contaminated · **Red** = change filters now.
**Normal hydraulic temperature:** ambient **+20 °F**. *(OM 1-1)*

**Diagnostic questions**
1. ASK: "Is the machine still cold, or has it been running a while?"
2. ASK: "Green, yellow, or red?"
3. ASK: "Is the oil level on the sight gauge where it should be?"

**Step-by-step**
1. → Cold start and yellow: SAY: "That's normal with cold oil. Let it warm up — it should drop back to green." → Back to green: resolved.
2. → Yellow when warm: SAY: "The filters are getting dirty — plan to change them soon."
3. → Red: SAY: "Change the hydraulic filters now."
4. → Running hot: check level; check radiator/heat-exchanger area is clean (Low confidence); escalate if well above ambient +20 °F.

**Resolution:** Filter change per schedule — after first **two weeks** (break-in), then **annually** or when the gauge shows restriction; hydraulic fluid annually. *(OM 7-2, 7-3)*

**Safety:** Shut down and relieve pressure before opening filter housings; hot oil.

**Escalation:** Red returns quickly after a change (contamination source); overheating.

**Source & confidence:** OM 1-1, 7-2, 7-3. **Confidence: High** (gauge), **Low** (overheat causes — not documented, G-10). Fluid spec conflict — see C-01.

---

### TS-15 — A manifold function won't activate (water pump, vibrator, fines feeder, additive pump, emulsion valve)

**Applicable models:** All with the electric-over-hydraulic main manifold.

**Customer questions**
- "Vibrator won't come on."
- "Water pump isn't running."
- "Oil valve won't open."
- "One function quit, everything else works."

**How it works:** The pressure-compensated manifold gives electric-over-hydraulic on/off control of water pump, vibrator, fines feeder, liquid additive pump, and emulsion valve. **Each has a built-in manual override** — knurled steel top inside each control unit — turn **counter-clockwise and raise** to turn the unit on for testing or non-electrical operation. *(OM 1-1)*

**Diagnostic questions**
1. ASK: "Which single function isn't working?"
2. ASK: "What's the manifold pressure gauge reading?" (record value; no normal value documented — G-10)
3. ASK: "Is the switch for it in auto or manual?"

**Step-by-step**
1. Rule out switch mode (auto vs manual) per relevant entry.
2. **Qualified operator/technician:** SAY: "With the machine running and everyone clear, use the manual override on that function's valve — turn the knurled top counter-clockwise and lift. Then return it."
   → Function **works on override**: hydraulics OK → **electrical** (switch, coil, connector, wiring, controller) → escalate.
   → **Doesn't work on override**: hydraulic side (cartridge, flow control, motor) → escalate.

**Safety:** Override activates the function immediately — keep hands clear of vibrator, augers, pumps. Return override to normal before resuming operation.

**Escalation:** Always after override test. [INTERNAL] PM lists IIIG manifold cartridges incl. conveyor cartridge **pre-set 280 PSI** and emulsion cartridge **pre-set 500 PSI**, main pressure relief, sequence valve — technician reference only; do not ask customers to adjust.

**Source & confidence:** OM 1-1; PM Fig 3-3. **Confidence: Medium** (override procedure documented; diagnostic inference electrical vs hydraulic is logical, not explicitly stated).

---

## A8. SPREADER BOX, GATE, DIVERTER, AUGERS

### TS-16 — Spreader box won't raise/lower or side-shift

**Applicable models:** All with box lift arms; side shift optional on some models. C.A.N.: box lift ~2½ ft travel, side shift ~1 ft each way. IIIG: PVG valve sections for box lift and side shift.

**Customer questions**
- "Box won't come up."
- "Lift arms won't drop."
- "Side shift doesn't move."
- "Hopper won't raise" (clarify — see note under index).

**Controls** *(OM 1-9, 1-21)*: **Left joystick** — forward/back raises/lowers box (C.A.N.: toward the lift arm to lower, away to raise); side-to-side = side shift.

**Possible causes (Low — not documented):** hydraulic system not powered; side-shift bar not attached; mechanical obstruction; valve section/coil fault.

**Diagnostic questions**
1. ASK: "Is the engine running or PTO engaged and the jackshaft system up?"
2. ASK: "Is it lift, side shift, or both?"
3. ASK: "Is the side-shift bar attached to the bracket under the pugmill?"

**Step-by-step**
1. Confirm power/hydraulics on.
2. SAY: "Make sure everyone is clear of the box and lift arms before moving anything."
3. Verify joystick direction per configuration.
4. → No movement → **escalate** (no documented diagnostic procedure).

**Safety:** **Never** work under a raised box or lift arms. Cylinders may actuate without warning. Set truck parking brake when hooking up.

**Source & confidence:** OM 1-9, 1-21, 5-4, 6-2; PM Fig 1-17. **Confidence: Low** for causes → escalate quickly. Gap G-06.

---

### TS-17 — Pugmill gate or diverter not responding

**Applicable models:** All. **Right joystick**: back = open gate, forward = close (C.A.N.: away from user = open, toward = close); side-to-side = diverter.

**Customer questions**
- "Mixer door won't open."
- "Diverter won't swing."
- "Material won't come out of the pugmill."

**Diagnostic questions**
1. ASK: "Is it the gate, the diverter, or both?"
2. ASK: "Has the gate area been cleaned recently?" — Gate and diverter areas must be cleaned thoroughly at start and end of each work period *(OM 7-1)*; buildup is a plausible cause (Low).

**Step-by-step**
1. Verify joystick direction for the control type.
2. → Buildup suspected: shut down, lock out, clean gate/diverter areas.
3. → Still no movement: escalate.

**Safety:** Lockout before cleaning near gate/pugmill.

**Source & confidence:** OM 1-9, 1-22, 7-1. **Confidence: Low** for cause; High for controls.

---

### TS-18 — Box augers won't run or run the wrong way

**Applicable models:** Augured, rut, or C.A.N. boxes with hydraulic augers (optional).

**Customer questions**
- "Augers in the box aren't turning."
- "Augers pushing material the wrong way."

**Step-by-step**
1. **Mech/Electronic:** SAY: "Turn on the auger system master switch on the rear panel, then set each auger direction switch inboard or outboard." *(OM 1-9)*
2. **C.A.N.:** SAY: "Auger main power switch ON. Then press ON on the auger keypad — the amber light should stay lit. Then choose FWD or REV — another amber light shows the direction. Use the rabbit/turtle RPM button for speed." *(OM 1-20)*
3. Wrong direction momentarily: right-joystick rocker reverses augers momentarily *(OM 1-9, 1-22)*.
4. → Still no rotation: escalate.

**Source & confidence:** OM 1-9, 1-20, 1-22. **Confidence: High.**

---

## A9. ENGINE / POWER & ELECTRICAL

### TS-20 — Side engine start-up issues, low-oil alarm, air filter indicator (RoadSaver II)

**Applicable models:** **RoadSaver II (side engine) only.** IIIG has no side engine (truck PTO).

**Customer questions**
- "Low oil alarm's going off when I start."
- "Air filter indicator is yellow."
- "Side engine won't start."

**Documented facts** *(OM 5-1, 7-1)*
- Before start: engine oil, coolant, air filter indicator, hydraulic level; **all switches OFF/neutral; System Start OFF**.
- Low oil alarm/warning light comes on with power ON and **stays on after start until oil pressure reaches 5 PSI and is rising** (normal).
- Air filter indicator: green → yellow → red. **Yellow: change filter. Red: shut down the engine.**
- Warm-up ~1,000 RPM to 160 °F; normal operating 1,800 RPM; max 2,100 RPM.

**Step-by-step**
1. → Alarm briefly after start: SAY: "That's normal until oil pressure passes 5 PSI and keeps climbing."
2. → Alarm stays on: SAY: "Shut it down and check the oil level." → Level OK but alarm persists → escalate (don't run).
3. → Air filter yellow/red: per rule above.
4. → Won't start: check all switches off/neutral, master shutdown switch (TS-21), then refer to Cummins service/escalate.

**Source & confidence:** OM 5-1, 7-1, 7-2. **Confidence: High.** Engine-internal diagnosis is out of scope (Cummins).

---

### TS-21 — No power to machine controls

**Applicable models:** All (12 V DC negative ground; normally fed from truck batteries; 65 A alternator, 100 A optional; auto-resetting circuit breakers).

**Customer questions**
- "Nothing on the panel lights up."
- "Machine's completely dead."

**Possible causes:** **Master shutdown switch** OFF — on the engine side, just behind the radiator, **unmarked** *(OM 1-10)*; ignition/system power switch off (guarded); truck battery; tripped breaker (auto-resetting).

**Step-by-step**
1. SAY: "Check the master shutdown switch on the engine side, just behind the radiator — it isn't labelled."
2. SAY: "Flip up the guard on the ignition or system power switch and turn it on."
3. ASK: "Do the truck's own lights and starter work?" → No: truck battery issue.
4. → Still dead: escalate (wiring/relays/breakers).

**Safety:** Disconnect battery before any electrical repair or welding; DC welder only.

**Source & confidence:** OM 1-10, 5-1, 6-1. **Confidence: Medium** (location of master switch documented for side-engine layout; IIIG location not documented — G-05).

---

## A10. CALIBRATION

### TS-22 — Aggregate or fines calibration results inconsistent

**Applicable models:** All.

**Customer questions**
- "My aggregate runs don't line up."
- "Graph isn't a straight line."
- "Cement calibration numbers keep changing."

**Possible causes**
- **Aggregate:** moisture not corrected; gate not verified with tape; spilled material past gate not removed; **washing with hose** instead of sweeping; driver weight changes; too small a run (need ≥3 tons/gate, start 100 counts); belt not tracking/tensioned. *(OM 3-2, 3-10)*
- **Fines:** ratio meter not verified; sample too small (~20 lb / 9 kg recommended); not three runs. *(OM 3-7; KBN)*

**Tolerances:** Aggregate — each run within **2 %** of average of three runs of ≥3 tons; results across gate settings should plot a **straight line**. *(OM 3-10)*

**Step-by-step**
1. ASK: "Did you correct for moisture?" Moisture factor = 1 + (moisture % ÷ 100); divide wet lbs/count by it. (7 % → 1.07.)
2. ASK: "Did you measure the gate with a tape and lock the set screw?"
3. ASK: "How did you clean up the spill past the gate?" → Hose: re-run, **sweep only**.
4. ASK: "Same driver, staying in the truck every weighing?"
5. Fines: KBN — mark head pulley and auger, count turns to verify the ratio meter reads 1.00 at equal speed.
6. Re-run. Still inconsistent → escalate.

**Safety:** Keep hands out of the pugmill when removing spilled material — engine off, cover locked.

**Source & confidence:** OM 3-1–3-14; KBN. **Confidence: High.**

---

## A11. MIX QUALITY & APPLICATION (operational problems)

> These entries address the slurry itself. The agent should frame answers as **operating guidance**, remind the customer that the **mix design** governs all proportions, and suggest involving their **emulsion supplier / mix-design lab** when chemistry is suspected.

### TS-23 — Mix too wet or too dry

**Applicable models:** All.

**Customer questions:** "Slurry's running into the gutter." · "Mix is too stiff to spread." · "Rock sinks and it looks black and shiny." · "It's breaking in the box."

**Symptoms:** Too wet → runs to gutter, won't hold straight lines, coarse rock settles, fines/asphalt float (black shiny surface). Too dry → can't mix uniformly, streaking/lumping, may break/set in the box. *(OM 9-22; ISSA A105 §12.1)*

**Quick test:** Draw a line in the slurry with a stick — **if the groove fills with fluid, there's too much water.** *(OM 10-6)*
**Target:** consistency like fresh Portland cement concrete *(OM 9-22)*; pre-wet water typically 6–11 % of dry aggregate, aim mid-range (~9 % in manual's example), avoid >11 % *(OM 9-7)*. **Do not spray extra water into the spreader box** *(ISSA A105 §6.4, §11.4)*.

**Step-by-step**
1. ASK: "Is it running and shiny, or stiff and lumpy?"
2. SAY (wet): "Do the stick test. If the line fills in, cut back the water a little at the diaphragm valve."
3. SAY (dry): "Open the water slightly. Don't add water in the box — adjust it at the machine."
4. Remind: aggregate moisture changes during the day; reset water and sulfate each morning *(OM 8-6)*.

**Source & confidence:** OM 9-7, 9-22, 10-6, 8-6; ISSA A105. **Confidence: High.**

---

### TS-24 — Mix breaking / setting in the box too fast

**Applicable models:** All (critical for micro-surfacing).

**Customer questions:** "It's setting up in the box." · "Micro's breaking before I can spread it." · "Hot day, mix won't stay workable."

**Possible causes** *(OM 10-1, 10-2, 10-7)*
1. **Hot emulsion** (delivered ambient–120 °F; above ~115 °F increases reactivity for micro).
2. **Hot road surface.**
3. Mix too dry (TS-23).
4. Insufficient set-control additive (TS-08 if additive isn't flowing).
5. Emulsion formulation (emulsifier content) — supplier issue.
6. Box material not kept moving (micro needs augers/paddles).

**Step-by-step**
1. ASK: "Is your liquid additive actually flowing?" → No: TS-08.
2. ASK: "How hot is the emulsion and the road?"
3. SAY: "Options from the manual: add a bit more water and/or more additive to slow the break; wet the road with the spray bars to cool it; carry a little less material in the box; start earlier in the day when the road is cooler; or let hot emulsion cool."
4. Micro: keep material moving with augers; consider supplier on emulsifier content/curing time.
5. → Stays a problem: involve emulsion supplier/lab.

**Source & confidence:** OM 9-8, 10-1, 10-2, 10-7. **Confidence: High** (manual guidance).

---

### TS-25 — Bad mix at the start or end of a pass

**Applicable models:** All; mostly machines using manual sequencing.

**Diagnosis** *(OM 10-1)*: **Too wet** at start → water started too soon. **Too rich (asphalt)** → emulsion started too soon.

**Correct manual sequence** *(OM 5-5)*: Start — **Additive ON, then immediately Aggregate, Emulsion, Water ON.** Stop (~40 ft / 10 m before end) — **Aggregate & Water OFF, then Emulsion & Additive OFF**; drag out remaining material with jackshaft still turning. Or use 1-button automatic sequencing.

**Step-by-step**
1. ASK: "Are you starting the materials by hand or with the one-button start?"
2. SAY the documented sequence; recommend 1-button mode.

**Source & confidence:** OM 5-4, 5-5, 10-1. **Confidence: High.**

---

### TS-26 — Streaks, drag marks, or grooves in the mat

**Customer questions:** "Long lines in the slurry." · "Box is leaving streaks." · "Grooves behind the box."

**Possible causes** *(OM 10-6, 8-10, 9-2; ISSA A105 §6.4, §11.1)*
1. **Oversized rock** caught under the rear strike-off rubber.
2. **Agglomerated aggregate balls** (wet, low sand equivalent).
3. Coarse aggregate applied too thin.
4. Dirty box / strike-off buildup; **burlap drag stiffened** with hardened slurry.
5. Broken mix (TS-24).

**Step-by-step**
1. ASK: "Are there rocks or clumps stuck under the back rubber?" → Clean strike-off.
2. SAY: "Clean the strike-off and buildup on the box regularly. Replace a burlap drag that has gone stiff."
3. → Recurring oversize/clumps: screen aggregate; check stockpile/loader practice.
4. → Coarse aggregate: increase application thickness per mix design.

**Source & confidence:** as cited. **Confidence: High.**

---

### TS-27 — Raveling (rock coming loose)

**Customer question:** "Rock's coming off the new slurry." · "Lots of loose stone after we opened it."

**Key message:** Some shedding in the first days is **normal but should be minimal**. *(OM 10-1)*
**Causes** *(OM 10-1)*: insufficient embedment; cool temps slowing cure; application rate too low; asphalt too low; poor aggregate; lack of fines; opened to traffic too soon; rain before set.
**Agent action:** Ask about temperature, timing of traffic, rain, and whether calibration/mix design were verified; recommend checking calibration and mix design with lab. **Confidence: High.**

---

### TS-28 — Bleeding / fat / shiny black spots

**Causes** *(OM 10-1)*: too much emulsion, or asphalt floating from too much water/emulsion, or heavy overlapping.
**Fix:** verify machine calibration; minimise overlaps (slurry max 6" overlap, micro max 3" — ISSA A105 §11.3, A143 §11.3). **Confidence: High.**

---

### TS-29 — Colour differences between passes or machines

**Causes** *(OM 9-23, 10-3)*: machines not calibrated to same proportions (shows next day); temperature (≈50 °F laying can look "rusty" vs ≥80 °F — uniform, fades with traffic); cement (dull black/grey), sulfate water-spot stains (temporary); excess water (slick black); hand-hose washing emulsion off; shaded areas.
**Agent action:** ASK "Is the difference pass-to-pass uniformly, or machine-to-machine?" Machine-to-machine → recalibrate all units to the same mix. Temperature-related → cosmetic, fades. **Confidence: High.**

---

### TS-30 — False slurry / false break

**False break ("tender mix")** *(OM 10-5)*: very hot, low-humidity conditions form a skin that traps moisture and delays cure.
**False slurry** *(OM 10-5)*: asphalt agglomerates on fines during mixing; signs — **excessive foaming, grey wet mix, many uncoated large particles**. **Field test:** put fresh mix from the box in a beaker of water — true slurry turns the water **brown**; false slurry barely discolours it.
**Agent action:** Walk through the beaker test; if false slurry suspected, stop and involve the emulsion supplier/lab. Hot emulsion is a known contributor *(OM 10-1)*. **Confidence: High.**

---

### TS-31 — Uneven mat on crowns, banked curves, or steep grades

*(OM 10-6, 10-7)*
- **Crowns/banks:** slurry flows to the low side. Partial fix: divert all mix to the high compartment. Full fix: **box augers** (TS-18) to push material laterally.
- **Grades steeper than ~8 %:** **uphill** — slightly more fluid mix; **downhill** — slightly stiffer mix (prevents escape under the front rubber).
- **Partial-width passes:** set diverter to the used portion; use augers.
**Confidence: High.**

---

### TS-32 — Slurry tracking on tires or onto concrete

*(OM 1-4, 10-4, 10-5)*
- Use **tire sprinklers** / spray bars / hand hose to wet tires and pavement so slurry doesn't stick.
- Spills on concrete: squeegee/shovel before set; hand hose. If set: dust with cement or broom on a fine cement mix; extreme cases water/sand blast.
- Prevent tracking across gutters/sidewalks: sand or cement-dust them, pre-wet, wash immediately, or lay felt paper weighted with aggregate.
**Confidence: High.**

---

### TS-33 — Rain on fresh slurry

*(OM 10-4)* Chemical set can occur in ~5 min (fast-setting) to 15–30 min (normal quick-set).
- **Light rain:** keep road closed until dry, then open.
- **Moderate rain:** let it set, sweep off loose rock; re-apply over it if damage is severe.
- **Heavy rain:** sweep and re-slurry; clean emulsion from gutters.
Weather limits (ISSA A105/A143 §8): don't apply if pavement or air is **below 50 °F and falling**; may apply when both are **above 45 °F and rising**; not if freezing is possible within **24 h**. **Confidence: High.**

---

### TS-34 — Power-steering / scuff marks

*(OM 9-24, 10-2)* Expected on new slurry in hot weather and tight-turn areas; generally roll out with traffic. Reduce with harder base asphalt, **latex/polymer additives (most successful)**, rubber-tired rolling, placing in cooler months, or sanding (unsightly). **Confidence: High.**

---

### TS-35 — Problems over crack sealer, thermoplastic markings, or old seal coats

*(OM 9-16, 10-3, 10-5, 10-10)*
- **Crack sealer:** incompatible solvent/rejuvenator fillers bleed through; rubber fillers disbond; uncured or tacked fillers stick to tires; **overbanded** fillers catch box skids → gouges/uneven mat. Prevent: compatible materials, no overfill, proper cure.
- **Thermoplastic:** slurry won't stick unless well worn; remove (mandatory on highways), tape/paper, or box out the marking. Micro: remove plastic markings.
- **Coal tar sealcoats:** slurry fails unless coal tar is old/worn/coarse.
- **Leaks** of sulfate, hydraulic oil, diesel from equipment cause adhesion failure.
**Confidence: High.**

---
# SECTION B — FREQUENTLY ASKED QUESTIONS

Format: **Q** · *Alt phrasings* · **A** (spoken answer) · Details · Models · Source.

## B1. General Equipment Information

**GEN-01 — What is a RoadSaver?**
*Alt:* "What does this machine do?" · "What's a slurry truck?"
**A:** A RoadSaver is Etnyre's truck-mounted machine for slurry seal and micro-surfacing. It carries aggregate, emulsion, water, and additives, mixes them in a pugmill, and lays the mix through a spreader box behind the truck.
**Details:** Designed to produce all ISSA grades of slurry seal and micro-surfacing (Type I, II, III), including combination treatments such as cape seals (KBN).
**Models:** All · **Source:** OM 1-1–1-5, 9-2; KBN.

**GEN-02 — What's the difference between a RoadSaver II and a IIIG?**
*Alt:* "Does mine have its own engine?" · "What's the G?"
**A:** The RoadSaver II has its own side engine — a Cummins diesel — to run the machine. The IIIG has no side engine; it runs everything off the truck engine through a PTO.
**Details:** KBN (sales notes, unverified): IIIG uses the Paccar MX; benefits cited — lower weight/higher payload, no side-engine fuel/maintenance, quieter. Outside the US, choice depends on clean-diesel availability for the MX.
**Models:** RS II, IIIG · **Source:** OM 1-1; PM §2; KBN.

**GEN-03 — How do I know which control system I have?**
*Alt:* "Mechanical, electronic, or CAN?"
**A:** Look at how you set jackshaft speed. Black knobs means Mechanical Flow Control. Toggle switches means Electronic Flow Control. Keypads with rabbit and turtle buttons means C.A.N.
**Source:** OM 1-6, 1-7, 1-11, 1-16.

**GEN-04 — What's the warranty?**
*Alt:* "Is this covered?"
**A:** Etnyre's operations manual states 12 months from in-service date, or 18 months from shipment, whichever is shorter, for defects in material and workmanship with proper maintenance. Etnyre will need to confirm coverage for your specific machine.
**Details:** Excludes wear items (filters, belts), damage from misuse or lack of maintenance, and separately warranted components (e.g., engine). [INTERNAL] PM warranty page still shows legacy Rayner Equipment Systems 180-day terms — conflict C-05; agent must not quote 180 days.
**Source:** OM Limited Warranty; PM p.2.

**GEN-05 — How much can the pugmill produce?**
**A:** Etnyre's notes describe the RoadSaver pugmill as producing over four tons per minute.
**Details:** KBN (sales material, unverified). Twin shafts with twin hydraulic motors, timed gears, carbide-tipped replaceable paddles (OM 1-5).
**Source:** KBN; OM 1-5. **Confidence:** Medium.

## B2. Operating Procedures

**OP-01 — How do I start up the machine?**
*Alt:* "What's the start-up procedure?" · "Morning start-up?"
**A:** Check fluids first. Then make sure every switch is off or in neutral, with System Start off. Turn on the ignition or system power, then start the side engine or pull the PTO switch. Warm it up until the engine reaches 160 degrees before running the emulsion pump.
**Details:** Side engine checks: engine oil, coolant, air-filter indicator; all: hydraulic level; emulsion supply/return valves open for recirculation; unlock security covers. Low-oil alarm clears above 5 PSI rising. Side engine warm-up ~1,000 RPM; operating 1,800, max 2,100. PTO machines: turn on pump heater switch in cab. Load emulsion, water, additives; leave hopper empty until ready.
**Models:** All (engine items RS II only) · **Source:** OM 5-1.

**OP-02 — What should the jackshaft and pugmill speeds be?**
**A:** A good starting point for the jackshaft is about 600 RPM. Normal pugmill speed is 90 to 110 RPM for standard Type II slurry or micro.
**Details:** Calibrate at the speed you'll actually operate. Different materials may need different pugmill speeds.
**Source:** OM 3-2, 5-2, 5-4.

**OP-03 — How does the 1-button (automatic) start work?**
*Alt:* "Auto sequence?"
**A:** The 1-button start automatically turns the oil valve, additive, water, and sand conveyor on and off in sequence. Press the red button on the left joystick to start; press again to stop.
**Details:** In auto mode, if aggregate at the gate falls below a preset level for over 3 seconds, the system does a sequenced shutdown (TS-10). Water pump must be in Auto.
**Source:** OM 1-4, 1-9, 1-21.

**OP-04 — What's the right order if I start materials manually?**
**A:** Additive on first, then immediately aggregate, emulsion, and water. To stop, about 40 feet before the end: aggregate and water off, then emulsion and additive off. Keep the jackshaft turning to drag out what's left.
**Source:** OM 5-5, 10-1.

**OP-05 — How do I make a pass?**
**A:** Lower the box and pull forward until the chains are tight and the rear rubber lies flat. Engage the jackshaft, confirm water pressure with water in Auto, start materials, open the gate with the diverter centred, fill the box about half full, then signal the driver to pull at 3 to 5 miles per hour.
**Source:** OM 5-5.

**OP-06 — How do I hook up the spreader box?**
**A:** Back up to the box and set the parking brake. Hook the drag chains. Make sure everyone is clear, lower the lift arms, and hook the lift chains. Attach the side-shift bar to the bracket under the pugmill, then lift the box.
**Source:** OM 5-4.

**OP-07 — How do I set the emulsion valves for loading, unloading, and normal running?**
**A:** It depends on whether your pump is fender-mounted or low-mounted. Which do you have?
**Details:**

| Mode | Fender-mounted pump | Low-mount pump |
|---|---|---|
| **Normal operating** | Blue 1 & Red 4 open; rest closed & cam-locked | Blue 1, Blue 2 & Red 4 open; rest closed & cam-locked |
| **Tanker loading** (tanker's pump) | Green 3 open | Valves 1, 2, 3 open; Red 4, Red 5, Valve 6 closed |
| **Self-loading** (RoadSaver pump) | Blue 1 closed; Blue 2 open; Red 4 open; Red 5 closed | Valve 3 & Red 4 open; Blue 1, 2, Red 5, Valve 6 closed |
| **Unloading** | Blue 1 & Red 5 open; Blue 2, Green 3, Red 4 closed | Blue 1, 2 & Red 5 open; Green 3, Red 4, Valve 6 closed |
| **Flushing** | — | Valve 6 open **only** when flushing pump/lines with water or cleaner |

[INTERNAL] OM's fender-pump "tanker loading" line names only green valve 3; full line-up for other valves in that mode is not stated (G-11). Agent should read one valve at a time and confirm.
**Source:** OM 2-1–2-4.

**OP-08 — What does the pugmill reverse switch do?**
**A:** Reverse is only for clearing a rock or foreign object from the paddles. The switch is spring-loaded, so you must hold it; let go and it returns to neutral. The red light shows reverse.
**Source:** OM 1-8, 5-2.

**OP-09 — What does the pugmill kill switch do?**
**A:** It's the guarded master switch that shuts off all power and hydraulics to the pugmill instantly and prevents it from moving. It must be on for the pugmill to run.
**Note:** It is not a substitute for engine shutdown before opening pugmill covers.
**Source:** OM 1-8, 5-2, 7-1.

**OP-10 — What do the water pump and fines feeder switch positions mean?**
**A:** Back is Automatic, middle is off, and forward is Manual. In Auto, the water pump runs when the jackshaft turns, and the fines feeder runs when the conveyor belt moves.
**Source:** OM 1-8.

**OP-11 — How do I signal the driver on a C.A.N. machine?**
**A:** Use the rocker switch on the left joystick. It flashes the lights on the in-cab keypad — top lights for speed up, bottom lights for slow down. On some machines the same switch changes side engine RPM instead.
**Source:** OM 1-21.

**OP-12 — How do I mix a practice batch?**
**A:** The manual's practice settings are: engine 1,800 to 2,100 RPM, jackshaft 600, mixer 110, water in auto with the valve three-quarters of a turn open, additive 2.5 gallons per minute, gate at three and a half inches. Run materials five seconds, shut off, then open the mixer gate.
**Source:** OM 5-4. [INTERNAL] Practice values only — not a mix design.

## B3. Routine Maintenance

**MNT-01 — What do I check every day?**
**A:** Check all fluid levels before starting, grease all bearings, and clean the machine at the start and end of each work period — especially the diverter and pugmill gate areas. At day's end, inspect for wear and leaks and lock all covers and emulsion valves.
**Details — grease points (multipurpose high-temp grease):** conveyor belt bearings; 2 pugmill bearings; 4 box lift arm bearings; 4 fines feeder bearings; 2 water pump fittings; side-shift fittings; emulsion pump shaft support bearings; emulsion valve button-valve bearings. Weekly: inspect undercarriage and truck chassis mounts.
**Source:** OM 7-1, 7-2.

**MNT-02 — What's the service schedule?**
**A:** Break-in: change hydraulic filters after two weeks. Every 25 hours: air cleaner, gearbox oil levels, mounting bolts, fittings, leaks. Every 200 hours: engine oil and filter, and coolant filter. Every 500 hours: conveyor, rubbers, emulsion pump drive oil, head-pulley reducer oil, pugmill timing gears. Annually: all hydraulic fluid and filters.
**Details:**
- **25 h:** air cleaner elements; aggregate belt drive gearbox oil (left of head pulley from operator station); engine power splitter gearbox oil (two hex plugs in the "I" casting — fill until it runs from the lower hole; fill point is the side bolt 1½" above the full-level plug); side engine mount bolts; fittings; hydraulic leaks.
- **200 h:** engine oil & filter (sooner in severe conditions); engine cooling filter.
- **500 h:** conveyor & side rubbers; gate side rubbers; emulsion pump drive oil; head-pulley gear reducer oil; pugmill timing gears.
- **Annual:** hydraulic fluid; all hydraulic filters (or sooner per gauge).
- Engine break-in/service: follow Cummins.
**Models:** All; engine items RS II · **Source:** OM 7-2, 7-3.

**MNT-03 — How do I winterize the RoadSaver?**
**A:** Clean everything, flush and drain the emulsion system, and completely drain the water system. Then put about 25 gallons of RV antifreeze in the water tank and run it through. Drain and flush the additive system and add 2 gallons of RV antifreeze. Wash out the hopper, belt, and fines feeder.
**Details:** Disconnect 3-way-valve-to-pugmill line and drain. Water: drain pump & filters, open a hose bib, back-blow with air (≤30 PSI rule applies) without running the pump, cycle each sprinkler until dry, clean tank, add RV antifreeze, run pump to fill lines; drain/flush in spring. Check engine coolant protection. Extreme cold: plywood over vibrator support area to stop ice on conveyor. KBN adds: inspect/replace wipers & squeegees, grease all bearings, check tire pressure.
**Source:** OM 7-3; KBN.

**MNT-04 — What cleaners can I use on the machine?**
**A:** Be careful. Don't use harsh cleaners on meters, electrical parts, gauges, or plastic covers. Soybean and orange-extract cleaners remove asphalt well, but they can seriously damage hydraulic lines, plastic fittings, connectors, and wire insulation.
**Source:** OM 7-3.

**MNT-05 — How do I read the hydraulic filter gauge?**
**A:** Green is normal, yellow means the filters are getting dirty, red means change them now. It can read yellow on a cold start — that's normal and should return to green when warm.
**Source:** OM 1-1.

## B4. Component Identification and Function

**CMP-01 — What is the jackshaft?**
**A:** The jackshaft drives the aggregate conveyor and the emulsion pump together, so rock and emulsion stay in proportion. Its speed sets how fast material feeds the pugmill.
**Details:** On the load-sensing Jackshaft/Pugmill circuit (also joystick functions, pugmill gate & diverter, box lift & side shift). Emulsion pumps are connected to the jackshaft, so jackshaft speed represents pump speed. Some machines electronically synchronise separate motors (Smart OPS "Oil Pump/Jackshaft Sync" screen on machines with 2 separate motors).
**Source:** OM 1-1, 1-24, 5-2; KBN.

**CMP-02 — What is the head pulley, and why does calibration use it?**
**A:** The head pulley turns the aggregate belt. It has an accurate counter, so all calibrations use head-pulley counts as the common reference.
**Details:** "Reference" always means head-pulley counts — never jackshaft counts, speeds, or RPM.
**Source:** OM 3-2.

**CMP-03 — What does the three-way emulsion valve do?**
**A:** It sends emulsion from the pump either into the pugmill or back to the tank. It's heated by engine coolant, positioned hydraulically, and controlled electrically from the operator station.
**Source:** OM 1-2.

**CMP-04 — What does the diaphragm valve do?**
**A:** It's the 1½-inch valve that precisely controls water flow into the pugmill. A yellow indicator inside shows its position from the rear of the machine.
**Source:** OM 1-4.

**CMP-05 — What's the vibrator beam?**
**A:** It's a V-shaped beam hanging on chains in the middle of the hopper. It vibrates hydraulically to stop rock from bridging so it flows steadily to the belt. Hold the button on the right joystick to run it.
**Source:** OM 1-4, 1-9.

**CMP-06 — What hydraulic pumps are on the machine?**
**A:** There are two or three pumps, each dedicated to one system: a load-sensing pump for the jackshaft and pugmill functions, and a pressure-compensated pump for the main manifold. On three-pump machines, the pugmill and oil pump have their own circuit.
**Details:** Manifold controls water pump, vibrator, fines feeder, liquid additive pump, emulsion valve (electric-over-hydraulic, manual overrides). IIIG: front pump load-sensing, rear pump pressure-compensated (PM Fig 2-1); 7-bank PVG valve: oil pump, conveyor, pugmill, box lift, side shift, pugmill gate, diverter (PM Fig 1-17).
**Source:** OM 1-1; PM.

**CMP-07 — Where's the master shutdown switch?**
**A:** On the engine side of the machine, just behind the radiator. It's not labelled. Use it to disable the machine when not in service or to kill all electrical power in an electrical problem.
**Source:** OM 1-10. [INTERNAL] IIIG location unverified (G-05).

**CMP-08 — What spreader boxes are available?**
**A:** Standard 12-foot-6 box, an augured box, an expandable box with a variable compartment, and a 5- to 6-foot rut-filling box with augers.
**Source:** OM 1-10.

**CMP-09 — What does a ratio meter reading mean on the fines feeder?**
**A:** It's the fines feeder auger speed compared to the head pulley. 1.00 means equal speed; 2.0 means the auger turns twice per head-pulley turn, delivering more cement.
**Source:** KBN; OM 3-7. **Confidence:** Medium.

**CMP-10 — What's on the IIIG hopper-stand control panel?**
**Details (technician reference):** Switches 1–11: 1 Pugmill Fwd/Rev · 2 Pugmill On/Off · 3 Water Pump Auto/Manual · 4 Do not use · 5 System Start-up · 6 Fines Feeder Auto/Manual · 7 Meter On/Off · 8 Aux Lights On/Off · 9 N/A · 10 Additive On/Off · 11 Aux light power plug. Also PTO On/Off, DP610 display with programming lock/key, CAN Module 1 (valves), main system solenoid, 40 A relays, circuit breakers.
**Source:** PM Fig 7-1–7-4, Schematics. **Confidence:** High (IIIG only).

## B5. Adjustments and Calibration

**CAL-01 — Why do I need to calibrate?**
**A:** To set the machine to your mix design using your actual job materials, to make multiple machines lay the same mix, and to build a record for that machine.
**Details:** Calibrate per aggregate source and type — unit weights vary 80–115 lb/ft³. Recalibrate when materials change significantly or proportioning equipment is replaced. See C-04 for validity period conflict.
**Source:** OM 3-1, 9-4, 9-24; ISSA §7.

**CAL-02 — How do I calibrate emulsion?**
**A:** It's a two-person job plus a supervisor. Empty the aggregate, fill with emulsion, and weigh the truck. Pump off enough to fill the hose to a tanker, then weigh. Run a set number of head-pulley counts — usually 100 or 200 — reweigh, and divide pounds pumped by counts. Do three runs.
**Details:** Use Smart OPS Auto Calibrate → Oil Calibration (press #2 to set counts — box turns yellow, arrows, OK; #6 start; #7 pause; #8 stop). Assistant opens the hose valve exactly as pump starts and closes it right after pump stops. **Never close the valve before the pump stops.** Same driver in the truck every weighing. Tolerance: each run within 2 % of average of three runs ≥300 gal (1,135 L). Order emulsion at the expected average job temperature.
**Source:** OM 3-2–3-6.

**CAL-03 — How do I calibrate aggregate?**
**A:** Correct for moisture, then run three gate settings — usually 3, 4, and 5 inches — with three runs each of at least three tons. Weigh before and after each run and divide by head-pulley counts.
**Details:** Verify gate with tape; pre-run to fill the gate, then **sweep** (never hose) spilled material; weigh; Auto Calibrate → Aggregate (100 or 200 counts); remove spill; reweigh. Dry lbs/count = wet lbs/count ÷ moisture factor (1 + %/100). Results should plot a straight line. If you normally run higher, use 3½, 4½, 5½". Smaller gates may need more counts.
**Source:** OM 3-9–3-14.

**CAL-04 — How do I calibrate the fines feeder?**
**A:** With no aggregate in the hopper, run about 20 pounds of cement into a weighed pan while counting auger turns. Weigh it, subtract the pan, and divide by the turns. Repeat three times.
**Details:** A standard 7 ft³ fines feeder normally delivers about **1.2 lb (544 g) per revolution**. Setting: Ratio = (aggregate lb/rev × desired dry additive %) ÷ calibrated lb/rev. KBN: physically verify the ratio meter reads 1.00 at equal speeds before trusting it.
**Source:** OM 3-7, 3-8; KBN.

**CAL-05 — How do I enter calibration values in Smart OPS?**
**A:** Go to Setup, then Cal Factors. Insert and turn the calibration key — the key icon turns from grey to red. Hold the number next to the value until it turns yellow, change it with the arrows, and press OK.
**Details:** Holding the number plus arrows changes in larger steps. Grey key = view only.
**Source:** OM 4-2, 4-3.

**CAL-06 — How does moisture affect my gate setting?**
**A:** Wet rock "bulks" — the same volume holds less dry rock. So as moisture goes up, the gate needs to go up to deliver the same dry aggregate.
**Details:** Example: at 5 % and 10 % moisture you get ~95 % and ~90 % of the desired dry rock at the same gate. Check stockpile moisture and set the machine accordingly (ISSA A105 §12.2).
**Source:** OM 3-1; ISSA.

**CAL-07 — What emulsion pump setting should I use?**
**A:** The manual says to select the ratio before calibration and lock it with the key — 45 for slurry or micro. Newer RoadSavers have a fixed pump with no adjustment. Etnyre should confirm which applies to your machine.
**Source:** OM 5-4; KBN. **Confidence:** Low — conflicting sources (C-03).

## B6. Replacement Parts and Fluids

**RPL-01 — What filters does the RoadSaver II use?**
**A:** I can give you the cross-reference numbers from the manual. Which filter do you need?
**Details (OM 7-4):**

| Filter | Fleetguard | Baldwin | Wix |
|---|---|---|---|
| Oil | LF-3345 | BT-427 | 51602 |
| Fuel #1 | FF-215 | BF-586-D | 33472 |
| Fuel #2 | FF-5018 | BF-988 | 33358 |
| Air #1 | AF-1735K | PA-2426-FN | 42522 |
| Air #2 | AF-4156 | PA-2427 | 46560 |
| Hydraulic | HF-6110 | PT-707-HD10 | 51407 |
| Water | WF-2052 | BW-5137 | 24071 |

[INTERNAL] Table is RoadSaver II. Verify the machine/engine before quoting; read one number at a time and have the customer repeat it back. No IIIG filter table in sources (G-12).
**Source:** OM 7-4. **Confidence:** High (RS II).

**RPL-02 — What fluids go in the gearboxes, engine, and hydraulic tank?**
**A:** Etnyre's fluid guide lists: jackshaft miter gearbox — 75W-90 synthetic; conveyor right-angle gearbox — ISO 680; hydraulic pump drive — 85W-140; Cummins Tier 3 — 15W-40; Tier 4 — 5W-40; hydraulic tank — ISO 68 hydraulic oil to mid sight-gauge. Note the operations manual recommends Chevron Tractor Hydraulic Fluid or Cat TO-2 for hydraulics, so confirm with Etnyre.
**Details:** Fill points (KBN): miter box — max fill plug on back side; conveyor gearbox — bottom mark on dipstick, do not overfill; pump drive — bottom plug on side; engines — Cummins guide.
**Models:** RS II & IIIG (per KBN) · **Source:** KBN; OM 7-3. **Confidence:** Medium — conflict C-01.

**RPL-03 — Where do I find part numbers for the IIIG?**
**A:** They're in the RoadSaver IIIG Repair Parts Manual, M-RS3G-23, organised by system. For ordering, Etnyre parts can confirm the exact number for your serial number.
[INTERNAL] Several PM entries show placeholder numbers ("11000xxxx") — do not quote those (G-13).
**Source:** PM.

**RPL-04 — How do I replace a safety decal?**
**A:** If a safety decal is unreadable or torn, replace it as soon as possible — Etnyre provides them. Don't clean decals with solvents or gasoline; they can fall off.
**Source:** OM 6-1; PM decal section.

## B7. Specifications and Operating Limits

**SPEC-01 — Tank and hopper capacities?**
**A:** Aggregate hopper 12 cubic yards. Fines feeder 7 cubic feet. Liquid additive tank about 80 gallons. Hydraulic reservoir 95 to 120 gallons, filled to about 85 percent.
**Details:** Emulsion and water tank capacities are not stated in the supplied manuals; Etnyre dip-stick charts exist for 600, 750, and 800-gallon tanks and an additive-tank calibration chart (ISSA supplement 14-80–14-84) — refer customer to the chart for their tank (G-15).
**Source:** OM 1-1, 1-4, 1-5.

**SPEC-02 — Water pump specs?**
**A:** Centrifugal pump rated 130 gallons per minute at 110 PSI, fed through a 2-inch suction line.
**Source:** OM 1-3.

**SPEC-03 — Side engine and electrical specs (RoadSaver II)?**
**A:** Cummins QSB3.3 Tier III, 110 horsepower, 4-cylinder turbo diesel, water cooled. 12-volt negative-ground electrics with a 65-amp alternator, 100-amp optional.
**Source:** OM 1-1, 1-10.

**SPEC-04 — Liquid additive meter range?**
**A:** The meter reads accurately from 0.5 to 5 gallons per minute. A typical starting point is 2 gallons per minute.
**Source:** OM 5-3.

**SPEC-05 — What temperatures can I lay slurry or micro in?**
**A:** Per ISSA guidelines, don't apply if the pavement or air temperature is below 50°F and falling. You can apply when both are above 45°F and rising. Don't apply if freezing is possible within 24 hours.
**Source:** ISSA A105 §8, A143 §8.

**SPEC-06 — What are typical application rates?**
**A:** Slurry seal: Type I, 8 to 12 pounds per square yard; Type II, 10 to 18; Type III, 15 to 22. Micro-surfacing: Type II, 10 to 20; Type III, 15 to 30. Those are dry-aggregate weights — your mix design and surface govern.
**Details:** Manual suggests Type III micro no heavier than 30 lb/yd² per lift; above that, multiple lifts. Ruts ≥½" → rut box (5 or 6 ft); >1½" may need multiple passes; overfill ⅛–¼" per inch of depth; 24 h under traffic before more lifts.
**Source:** ISSA A105 §11.2, A143 §11.2 & §6.4.2; OM 9-23, 10-11.

**SPEC-07 — Typical emulsion and residual asphalt ranges?**
**A:** Emulsion by dry aggregate weight: Type I 13–18 %, Type II 12–16 %, Type III 10–15 %. Your lab mix design sets the actual number.
**Details:** ISSA residual asphalt — slurry Type I 10–16 %, II 7.5–13.5 %, III 6.5–12 %; micro 5.5–10.5 %; mineral filler 0–3 %; micro polymer ≥3 % solids of bitumen weight. Additives up to ~1 %.
**Source:** OM 9-8, 9-10; ISSA A105 §5.2, A143 §6.

**SPEC-08 — How fast should the truck move while laying?**
**A:** The manual says to start pulling at 3 to 5 miles per hour once the box is about half full, and keep the amount in the box roughly constant.
**Source:** OM 5-5, 9-24.

**SPEC-09 — Engine RPM limits (RS II)?**
**A:** Warm up around 1,000 RPM, normal operating 1,800, maximum 2,100.
**Source:** OM 5-1.

## B8. Job-Site & Application Practice

**APP-01 — Do I need a tack coat?**
**A:** Usually not, unless the surface is very dry and raveled, or it's concrete or brick. A typical tack is one part emulsion to three parts water.
**Details:** Rate conflict: OM 0.05–0.10 gal/yd²; ISSA 0.05–0.15 gal/yd² (C-06).
**Source:** OM 9-16; ISSA A105 §10.2.

**APP-02 — How should I treat cracks before slurry?**
**A:** ISSA recommends sealing cracks wider than a quarter inch first — with a compatible sealer, not overbanded, and fully cured.
**Source:** ISSA A105 §10.3; OM 10-3.

**APP-03 — Can I spray water into the box to loosen the mix?**
**A:** No. ISSA guidelines don't allow spraying extra water into the spreader box. Adjust water at the machine instead.
**Source:** ISSA A105 §6.4, §11.4.

**APP-04 — How long until I can open to traffic?**
**A:** It depends on the system and weather. Quick-set systems can chemically set in 5 to 30 minutes; full cure can take two to four weeks. Your mix design's cohesion test sets the expected traffic time.
**Source:** OM 9-6, 10-4; ISSA.

**APP-05 — Should I roll slurry?**
**A:** Usually not on roads. For airports and parking lots, use a rubber-tired roller — never steel — for at least two passes once the slurry won't pick up.
**Details:** OM: 10–12-ton nine-wheel; ISSA: 10-ton maximum pneumatic (C-08).
**Source:** OM 10-2; ISSA A105 §11.7.

**APP-06 — How often should I test materials on the job?**
**A:** Typical practice: aggregate gradation once per 500 tons, emulsion sieve once a day or per load, mineral filler type once a day, and water pH at job start or when the source changes.
**Source:** OM 9-11.

**APP-07 — How long can emulsion sit in the tank?**
**A:** Emulsion sitting more than two to three days can start developing sieve, pellets, or a skin. Check it before use; minor problems can be filtered and recirculated.
**Source:** OM 9-7.

---
# SECTION C — KNOWLEDGE GAPS AND ITEMS REQUIRING ETNYRE VALIDATION

## C1. Conflicting information across sources

| ID | Topic | Source A | Source B | Agent behaviour until resolved | Priority |
|---|---|---|---|---|---|
| **C-01** | Hydraulic fluid type & fill level | OM 7-3: Chevron Tractor Hydraulic Fluid, Cat TO-2 or equal; OM 1-1: fill to ~85 % of max | KBN: ISO 68 hydraulic oil, fill to mid sight gauge | State both, recommend confirming with Etnyre before topping off. Never advise mixing fluids. | **P1** |
| **C-02** | Hydraulic filter interval | OM 7-2 lists "change hydraulic system filter annually unless gauges show restriction" under the *200-hour* heading | OM 7-3: all hydraulic filters annually; OM 7-2: after first 2 weeks | Use: 2-week break-in, then annually or when gauge shows yellow/red. | P3 |
| **C-03** | Emulsion pump adjustability | OM 5-4: "select desired ratio … lock with supplied key (45 for Slurry/Micro)" | KBN: newer machines have a **fixed** pump, 15 turns per head-pulley turn, no scale/adjustment; variable pumps "usually about 15.1" at 100 % | Ask Etnyre; agent says pump setting depends on machine generation. | **P1** |
| **C-04** | Calibration validity | OM 9-24: previous calibration acceptable if done "during that calendar year" | ISSA A105/A143 §7: within previous **60 days**; recalibrate after any proportioning component replacement | Advise the project spec governs; ISSA default 60 days. | P2 |
| **C-05** | Warranty | OM: Etnyre, 12 months in-service / 18 months shipment | PM p.2: Rayner Equipment Systems, 180 days, return to Sacramento | Quote OM only, with "Etnyre will confirm". Update PM warranty page. | P2 |
| **C-06** | Tack coat rate | OM 9-16: 0.05–0.10 gal/yd² | ISSA: 0.05–0.15 gal/yd² | Defer to project spec. | P3 |
| **C-07** | C.A.N. speed ENABLE LED meaning | OM 1-16/1-19 description: LED on "shows … speed can not be changed" | Same pages, button operation: press once → LED on → resets off after a few seconds | Agent uses operational wording (press enable, then rabbit/turtle). Fix manual wording. | P2 |
| **C-08** | Roller size | OM 10-2: 10–12-ton nine-wheel rubber-tired | ISSA A105 §11.7: 10-ton maximum pneumatic | Defer to project spec. | P3 |
| **C-09** | Starting additive flow | OM 5-3: 2 GPM | OM 5-4 practice mix: 2.5 GPM | Present both as starting points, not settings. | P3 |
| **C-10** | Contact / address | OM: Oregon, IL, 815-732-2116 | PM & Troubleshooting Guide cover: Wickenburg, AZ; PM phone 1-916-826-1700; PM warranty: Sacramento (Rayner) | **Do not speak a number until validated.** | **P1** |
| **C-11** | Stale cross-references | OM 5-2 "see page 13 for machine type" (no such page) | — | Editorial fix. | P3 |

## C2. Missing documentation / incomplete procedures (prioritised)

Priority = frequency (expected) × operational impact × safety consequence. Frequency is **estimated** — no call data.

| ID | Gap | Why it matters | Impacted entries | Priority |
|---|---|---|---|---|
| **G-01** | **No support call transcripts supplied** (Etnyre folder empty) | Cannot measure frequency, resolution rates, real customer phrasing, or undocumented technician know-how — the core objective of this KB | All; Section D | **P1** |
| **G-16** | Machine-specific **"RoadSaver II Troubleshooting Guide"** referenced in OM 13-1 (cover shown) but not supplied | Likely the richest diagnostic source; OM §13 contains only 4 short checklists | TS-01–TS-21 | **P1** |
| **G-03** | No **fault / alarm code dictionary** for Smart OPS / C.A.N. DP610 | Agent must escalate every code | TS-13 | **P1** |
| **G-02** | Smart OPS **"Production Tracking Screens"** bi-fold addendum missing | Signals, Switch Verification, PPU Diagnostic, Sensor Frequency, Sync screens cannot be explained | TS-01, TS-13, CAL-02–05 | **P1** |
| **G-06** | No troubleshooting for **box lift, side shift, pugmill gate, diverter** (safety-critical hydraulics) | High-consequence functions currently "escalate only" | TS-16, TS-17 | **P1** |
| **G-10** | No **normal operating pressures** (manifold, sand conveyor/jackshaft gauges), relief settings for RS II, or hydraulic overheating diagnosis | Agent can't interpret gauge readings customers report | TS-14, TS-15 | **P1** |
| **G-17** | OM TOC lists **Micro-1 Controller, Micro-1 Programmer, Sonar Probe calibration** (13-2 to 13-6) — pages absent from PDF | Older/optional controller fleet unsupported | TS-13 | P2 |
| **G-04** | Aggregate **low-level gate sensor**: location, preset, adjustment | Auto-shutdown complaints can't be diagnosed beyond bridging | TS-10 | P2 |
| **G-05** | **IIIG-specific** gaps: master shutdown switch location, PTO engagement/RPM limits & warm-up, pump heater switch details; validation of KBN signal-screen "press 7" and pin legend per model | IIIG is the current US product | TS-01, TS-03, TS-21 | P2 |
| **G-07** | Conveyor **belt tension/tracking procedure** and values | Frequent on new machines (checked every load first week) | TS-11 | P2 |
| **G-09** | **Emulsion pump** manufacturer manual (OM: "see appendix") not supplied; fixed vs variable pump identification | Pump wear/cavitation can't be addressed | TS-03–TS-05, CAL-07 | P2 |
| **G-08** | Pugmill **paddle / carbide tip replacement**, timing-gear inspection criteria, bearing service | Wear item on every machine | TS-02 | P2 |
| **G-11** | Fender-mounted pump **tanker-loading** full valve line-up (only valve 3 stated) | Mis-set valves → spills | OP-07 | P2 |
| **G-12** | **IIIG filter & fluid table** (Paccar MX, PTO, pump drive) | RPL questions on IIIG | RPL-01, RPL-02 | P2 |
| **G-14** | Validated **escalation path**: phone, hours, after-hours, dealer network, parts ordering | Agent's core handoff | 0.6 | **P1** |
| **G-13** | Parts manual **placeholders**: "11000xxxx" part numbers, "Section xx", "Circuit Breakers (size?)", "_____ Controller", "Clutch—delete" | Agent can't quote those parts | RPL-03 | P3 |
| **G-15** | **Emulsion & water tank capacities**; dip-stick & additive-tank charts exist only as images (ISSA 14-80–14-84) | Common "how many gallons left" question | SPEC-01 | P2 |
| **G-18** | RS II electrical schematic / relay & breaker map; IIIG schematic labels incomplete | Electrical escalations | TS-01, TS-21 | P3 |
| **G-19** | Spreader box rubber (strike-off, side, front) replacement & adjustment; runner/skid wear limits | Crew asks frequently (implied by OM 8-10) | TS-26 | P3 |
| **G-20** | Torque values, fastener specs, gearbox oil capacities | Maintenance FAQs | MNT-02 | P3 |

## C3. Items marked unverified in this KB (need Etnyre sign-off)

- All **KBN-only** content: pugmill signal-screen procedure & pin legend (TS-01 steps 6–7), variable-pump check (TS-04 step 5), fluids table (RPL-02), ratio-meter explanation (CMP-09), pugmill output and sales comparisons (GEN-02, GEN-05).
- **Low-confidence diagnostic inferences:** TS-15 electrical-vs-hydraulic split, TS-16/TS-17 causes, TS-14 overheating causes.
- **Safety-adjacent:** confined-space tank cleaning (TS-04) is intentionally *not* coached — Etnyre should decide whether to provide an approved procedure.

## C4. Recommended media to produce

| Topic | Format |
|---|---|
| Emulsion valve line-ups (both pump mounts) | Labelled photo + one-page card per mode |
| Manual override locations on manifold | Photo with callouts |
| Sensor-to-wheel 1/8" gap check | Short video |
| Smart OPS / DP610 menu map | Screen-by-screen screenshots |
| Belt tracking adjustment | Video |
| Box lift / side shift / gate / diverter hydraulic layout | Diagram (PVG sections on IIIG) |
| Grease point map | Diagram |
| Dip-stick & additive tank charts | Transcribed tables (machine-readable) |

---

# SECTION D — SUPPORT CALL INSIGHTS

> **No support call transcripts were supplied**, so call counts and resolution rates are **0 / Unknown**. "Common causes" below come from manufacturer documentation, not call data. Re-run the analysis when transcripts arrive. Then this table becomes the frequency driver for Section C prioritisation.

| Problem category | Number of calls | Resolution rate | Common causes (documented) | Knowledge gaps |
|---|---|---|---|---|
| Pugmill (won't run, jams) | 0 | Unknown | Kill switch off; direction neutral; oversize rock | G-02, G-05, G-08, G-16 |
| Emulsion system (no flow, erratic, calibration) | 0 | Unknown | Not warmed to 160 °F; valve line-up; asphalt blockage; cavitation; procedure errors | C-03, G-09, G-11 |
| Water & sprinklers | 0 | Unknown | Diaphragm valve closed; no truck air; strainer/filter/tips clogged | — |
| Liquid additive | 0 | Unknown | Tank valve off; air lock; filter clogged | — |
| Aggregate feed & conveyor | 0 | Unknown | Bridging; gate setting; low-level auto shutdown; belt tracking | G-04, G-07 |
| Fines feeder | 0 | Unknown | Auto mode requires belt; speed/ratio; vent valve | — |
| Controls / Smart OPS / sensors | 0 | Unknown | Sensor loose or >1/8" from wheel; meter power; C.A.N. enable timeout | G-02, G-03, G-17 |
| Hydraulics | 0 | Unknown | Dirty filters; manifold valve/coil fault | C-01, G-10 |
| Spreader box, gate, diverter, augers | 0 | Unknown | Auger power/direction not selected | G-06, G-19 |
| Engine / power / electrical | 0 | Unknown | Master switch off; switches not neutral; low oil; air filter | G-05, G-18 |
| Calibration | 0 | Unknown | Moisture not corrected; driver weight; hose not pre-filled; hosing spill | C-03, C-04 |
| Mix quality & application | 0 | Unknown | Water/emulsion balance; temperature; sequencing; aggregate quality | — |
| Maintenance / fluids / parts | 0 | Unknown | — | C-01, C-02, G-12, G-13, G-20 |

---

# SECTION E — SOURCE TRACEABILITY

Page references are the printed page labels in each manual (e.g., OM 3-5 = MO-RS-24 page "3-5").

| Entry | Primary source(s) | Secondary | Model scope | Confidence |
|---|---|---|---|---|
| TS-01 | OM 1-5, 1-8, 5-2 | KBN Troubleshooting › Pugmill | All (pin legend: verify) | High / Medium |
| TS-02 | OM 1-5, 1-8, 5-2, 6-2, 10-6 | — | All | High |
| TS-03 | OM 1-2, 2-1–2-4, 5-1, 5-2 | — | All; valve sets by pump mount | High |
| TS-04 | OM 3-5, 9-7, 13-1 | KBN calibration troubleshooting | All | High / Medium |
| TS-05 | OM 3-2–3-6 | KBN | All | High |
| TS-06 | OM 1-3, 1-4, 1-8, 5-3, 13-1 | — | All | High |
| TS-07 | OM 1-4, 1-9, 1-15, 1-19, 13-1 | — | All | High |
| TS-08 | OM 1-5, 5-3, 5-4, 6-2, 13-1 | — | All | High |
| TS-09 | OM 1-4, 1-9, 1-22, 5-4, 6-2, 7-3, 8-10, 10-6 | — | All | High |
| TS-10 | OM 1-4 | — | Auto-sequence machines | High / Low |
| TS-11 | OM 3-2, 5-4, 7-2, 8-6, 8-10 | — | All | Medium |
| TS-12 | OM 1-4, 1-5, 1-7, 1-8, 5-3, 6-2 | — | Fines feeder equipped | High |
| TS-13 | OM 1-24, 13-1 | PM schematic sensor legend | Smart OPS / C.A.N. | High |
| TS-14 | OM 1-1, 7-2, 7-3 | — | All | High / Low |
| TS-15 | OM 1-1 | PM Fig 3-3 | All | Medium |
| TS-16 | OM 1-9, 1-21, 5-4, 6-2 | PM Fig 1-17, §8 | All | Low |
| TS-17 | OM 1-9, 1-22, 7-1 | PM Fig 1-17 | All | Low |
| TS-18 | OM 1-9, 1-20, 1-22 | PM Fig 7-5 | Auger boxes | High |
| TS-19 | OM 1-16, 1-19 | — | C.A.N. | High |
| TS-20 | OM 5-1, 7-1, 7-2 | — | RS II | High |
| TS-21 | OM 1-10, 5-1, 6-1 | — | All | Medium |
| TS-22 | OM 3-1–3-14 | KBN | All | High |
| TS-23 | OM 8-6, 9-7, 9-22, 10-6 | ISSA A105 §6.4, §11.4, §12.1 | All | High |
| TS-24 | OM 9-8, 10-1, 10-2, 10-7 | — | All | High |
| TS-25 | OM 5-4, 5-5, 10-1 | — | All | High |
| TS-26 | OM 8-10, 9-2, 10-6 | ISSA A105 §6.4, §11.1; A143 §11.1 | All | High |
| TS-27 | OM 10-1 | — | All | High |
| TS-28 | OM 10-1 | ISSA A105/A143 §11.3 | All | High |
| TS-29 | OM 9-23, 10-3 | — | All | High |
| TS-30 | OM 10-1, 10-5 | — | All | High |
| TS-31 | OM 10-6, 10-7 | — | All | High |
| TS-32 | OM 1-4, 10-4, 10-5 | — | All | High |
| TS-33 | OM 10-4 | ISSA A105/A143 §8 | All | High |
| TS-34 | OM 9-24, 10-2 | ISSA A105 §9.2 | All | High |
| TS-35 | OM 9-16, 10-3, 10-5, 10-10 | — | All | High |
| GEN-01 | OM 1-1–1-5, 9-2 | KBN | All | High |
| GEN-02 | OM 1-1; PM §2 | KBN | RS II / IIIG | High / Medium |
| GEN-03 | OM 1-6, 1-7, 1-11, 1-16 | — | All | High |
| GEN-04 | OM Limited Warranty | PM p.2 (conflict) | All | Medium |
| GEN-05 | OM 1-5 | KBN | All | Medium |
| OP-01 | OM 5-1 | — | All | High |
| OP-02 | OM 3-2, 5-2, 5-4 | — | All | High |
| OP-03 | OM 1-4, 1-9, 1-21 | — | All | High |
| OP-04 | OM 5-5, 10-1 | — | All | High |
| OP-05 | OM 5-5 | — | All | High |
| OP-06 | OM 5-4 | — | All | High |
| OP-07 | OM 2-1–2-4 | — | By pump mount | High (gap G-11) |
| OP-08 | OM 1-8, 5-2 | — | All | High |
| OP-09 | OM 1-8, 5-2, 7-1 | — | All | High |
| OP-10 | OM 1-8 | PM schematic | All | High |
| OP-11 | OM 1-21 | — | C.A.N. | High |
| OP-12 | OM 5-4 | — | All | High |
| MNT-01 | OM 7-1, 7-2 | — | All | High |
| MNT-02 | OM 7-2, 7-3 | — | All | High |
| MNT-03 | OM 7-3 | KBN | All | High |
| MNT-04 | OM 7-3 | — | All | High |
| MNT-05 | OM 1-1 | — | All | High |
| CMP-01 | OM 1-1, 1-24, 5-2 | KBN | All | High |
| CMP-02 | OM 3-2 | — | All | High |
| CMP-03 | OM 1-2 | — | All | High |
| CMP-04 | OM 1-4 | — | All | High |
| CMP-05 | OM 1-4, 1-9 | — | All | High |
| CMP-06 | OM 1-1 | PM Fig 2-1, 3-3, 1-17 | All / IIIG detail | High |
| CMP-07 | OM 1-10 | — | RS II confirmed | Medium |
| CMP-08 | OM 1-10 | — | All | High |
| CMP-09 | OM 3-7 | KBN | All | Medium |
| CMP-10 | PM Fig 7-1–7-4, Schematics | — | IIIG | High |
| CAL-01 | OM 3-1, 9-4, 9-24 | ISSA §7 | All | High |
| CAL-02 | OM 3-2–3-6 | KBN | All | High |
| CAL-03 | OM 3-9–3-14 | KBN | All | High |
| CAL-04 | OM 3-7, 3-8 | KBN | All | High |
| CAL-05 | OM 4-2, 4-3 | — | Smart OPS | High |
| CAL-06 | OM 3-1 | ISSA A105 §12.2 | All | High |
| CAL-07 | OM 5-4 | KBN (conflict) | Unclear | Low |
| RPL-01 | OM 7-4 | — | RS II | High |
| RPL-02 | KBN | OM 7-3 (conflict) | RS II & IIIG | Medium |
| RPL-03 | PM | — | IIIG | High |
| RPL-04 | OM 6-1 | PM decals | All | High |
| SPEC-01 | OM 1-1, 1-4, 1-5 | ISSA 14-80–14-84 (charts) | All | High |
| SPEC-02 | OM 1-3 | — | All | High |
| SPEC-03 | OM 1-1, 1-10 | — | RS II | High |
| SPEC-04 | OM 5-3 | — | All | High |
| SPEC-05 | ISSA A105 §8, A143 §8 | — | All | High |
| SPEC-06 | ISSA A105 §11.2, A143 §11.2, §6.4.2 | OM 9-23, 10-11 | All | High |
| SPEC-07 | OM 9-8, 9-10 | ISSA A105 §5.2, A143 §6 | All | High |
| SPEC-08 | OM 5-5, 9-24 | — | All | High |
| SPEC-09 | OM 5-1 | — | RS II | High |
| APP-01 | OM 9-16 | ISSA A105 §10.2 | All | Medium (C-06) |
| APP-02 | ISSA A105 §10.3 | OM 10-3 | All | High |
| APP-03 | ISSA A105 §6.4, §11.4 | — | All | High |
| APP-04 | OM 9-6, 10-4 | ISSA | All | High |
| APP-05 | OM 10-2 | ISSA A105 §11.7 | All | Medium (C-08) |
| APP-06 | OM 9-11 | — | All | High |
| APP-07 | OM 9-7 | — | All | High |

---

## Appendix — Integration notes for the voice agent pipeline

- **Chunking:** one retrieval chunk per entry ID (TS-xx, GEN/OP/MNT/CMP/CAL/RPL/SPEC/APP-xx). Each entry is self-contained by design.
- **Metadata per chunk:** `id`, `subsystem`, `models` (RS II / IIIG / All / C.A.N. / Mech / Elec), `confidence`, `sources`, `safety_flag` (true for TS-01, 02, 04, 09, 12, 15, 16, 17, 20, 21; MNT-03; CAL-02, CAL-03).
- **TTS filtering:** strip lines beginning `[INTERNAL]`, the Source/Confidence lines, and tables marked technician reference before speech.
- **Slot to collect early:** `machine_model` (II vs IIIG), `control_type` (Mech / Elec / C.A.N.), `pump_mount` (fender / low) — these gate which steps are valid.
- **Hard guardrails:** any utterance indicating a person in the hopper/pugmill/fines feeder, under a raised box, or touching a pressurised leak → interrupt with Section 0.5 safety instruction before anything else.
- **Escalation payload:** model, control type, entry ID reached, steps completed with results, any fault text, gauge readings.
