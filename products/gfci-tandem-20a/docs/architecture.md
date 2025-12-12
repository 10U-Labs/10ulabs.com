# Architecture: 2x20A Tandem GFCI Breaker

## Overview

This document describes the internal architecture of a dual-circuit 20A Class A GFCI breaker designed to fit the Siemens QT tandem form factor. The design provides two fully independent GFCI-protected 120V/20A circuits within a single-pole-width breaker body.

## Mechanical Envelope Constraints

### Siemens QT Tandem Dimensions (Approximate)

| Dimension | Value |
|-----------|-------|
| Width | 0.75" (19.05mm) single-pole |
| Height | ~3.25" (82.55mm) |
| Depth | ~2.75" (69.85mm) |
| Bus stab | QT-style clip-on, 120V leg A or B selectable via stab position |

### Internal Volume Budget

The tandem envelope must accommodate:
- Two thermal-magnetic trip mechanisms (stacked vertically)
- Two current transformers (one per circuit)
- One shared PCB for dual-channel GFCI logic
- Two trip actuators (solenoids or motor-driven releases)
- Four power terminals (2x HOT load, 2x NEUTRAL load)
- Two TEST buttons and two RESET buttons
- Line-side bus stab and neutral pigtail connection

Estimated PCB area: ~15mm x 60mm (single narrow board mounted vertically along one side).

---

## Block Diagram

```
                    PANEL BUS (HOT)
                         │
              ┌──────────┴──────────┐
              │      BUS STAB       │
              │  (staggered teeth   │
              │   for A/B legs)     │
              └──────────┬──────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
    ┌────┴────┐                     ┌────┴────┐
    │ BREAKER │                     │ BREAKER │
    │ MECH 1  │                     │ MECH 2  │
    │ (20A)   │                     │ (20A)   │
    └────┬────┘                     └────┬────┘
         │                               │
    ┌────┴────┐                     ┌────┴────┐
    │  CT 1   │◄── HOT1             │  CT 2   │◄── HOT2
    │(diff CT)│◄── NEU1             │(diff CT)│◄── NEU2
    └────┬────┘                     └────┬────┘
         │                               │
         │    ┌─────────────────────┐    │
         └───►│   GFCI LOGIC PCB    │◄───┘
              │                     │
              │  ┌───────┬───────┐  │
              │  │ CH1   │ CH2   │  │
              │  │ sense │ sense │  │
              │  │ +trip │ +trip │  │
              │  └───┬───┴───┬───┘  │
              │      │       │      │
              │   TRIP1   TRIP2     │
              │  ACTUATOR ACTUATOR  │
              └─────────────────────┘
                     │       │
              ┌──────┘       └──────┐
              ▼                     ▼
         ┌─────────┐           ┌─────────┐
         │ LOAD 1  │           │ LOAD 2  │
         │ HOT+NEU │           │ HOT+NEU │
         └─────────┘           └─────────┘
```

---

## Subsystem Descriptions

### 1. Bus Stab and Line Connection

- **Type**: QT-style clip-on bus stab with staggered teeth to engage panel bus bars.
- **Neutral**: Pigtail wire (white, 10 AWG) to panel neutral bar. Single pigtail splits internally to feed both circuits' neutral paths.
- **Mounting**: Standard Siemens QT rail clip at rear.

### 2. Breaker Mechanisms (x2)

Each circuit has an independent thermal-magnetic trip mechanism:

| Parameter | Specification |
|-----------|---------------|
| Rated current | 20A continuous |
| Thermal trip | Bimetal element, ~135% of rated (27A) for delayed trip |
| Magnetic trip | ~10x rated (200A) instantaneous |
| Interrupting capacity | 10 kAIC target |
| Arc chamber | Stacked steel plates (space-constrained, 5-plate minimum) |

The two mechanisms are stacked vertically within the breaker body, with separate operating handles ganged or independent (TBD based on UL requirements—independent preferred for GFCI).

### 3. Current Transformers (x2)

Each circuit requires a differential current transformer to sense imbalance between HOT and NEUTRAL:

| Parameter | Specification |
|-----------|---------------|
| Core material | High-permeability ferrite or nanocrystalline |
| Turns ratio | Primary: 1T (pass-through), Secondary: ~1000T |
| Window size | Must pass 10 AWG HOT + 10 AWG NEUTRAL |
| Sensitivity | Detect ≥4mA differential (trip at 5mA ±1mA) |
| Bandwidth | 50-60Hz fundamental, reject high-frequency noise |

**Physical constraint**: Each CT must fit within ~10mm diameter and ~8mm height. Toroidal form factor with both HOT and NEUTRAL conductors passing through center.

### 4. GFCI Logic PCB

A single PCB handles both GFCI channels. This reduces cost and simplifies assembly.

#### 4.1 Sensing Circuitry (per channel)

- CT secondary connects to high-impedance amplifier input.
- Bandpass filter centered at 60Hz, Q ≈ 5, to reject DC offsets and RF noise.
- Peak/RMS detector to measure differential current magnitude.
- Comparator with 5mA threshold (adjustable via resistor divider for calibration).

#### 4.2 GFCI Controller Options

| Approach | Pros | Cons |
|----------|------|------|
| Discrete analog (LM1851 or similar) | Proven, no firmware, fast response | Two ICs needed, larger footprint |
| Dual-channel ASIC (custom or semi-custom) | Smaller, integrated | NRE cost, long lead time |
| Microcontroller (e.g., ATtiny or STM32G0) | Flexible, self-test automation | Firmware certification complexity |

**Baseline choice**: Discrete analog with dual LM1851 or equivalent GFCI controller ICs, one per channel.

#### 4.3 Power Supply

- Derived from LINE-NEUTRAL (always hot when breaker is ON).
- Linear regulator or small flyback for isolation if required.
- Target: 5V @ 10mA typical, 50mA peak during trip actuation.
- Shared supply for both channels; galvanic isolation not required between channels as both reference same neutral.

#### 4.4 Trip Drivers

- Each channel has independent trip driver output.
- Driver circuit: Low-side MOSFET or BJT driving trip actuator coil.
- Energy storage: Capacitor bank to ensure trip completes even if line voltage sags during fault.
- Flyback diode across actuator coil.

### 5. Trip Actuators (x2)

Each GFCI channel requires a trip actuator to mechanically release the breaker latch:

| Parameter | Specification |
|-----------|---------------|
| Type | Solenoid (push or pull) |
| Coil voltage | 5V DC (from onboard supply) |
| Actuation force | ≥1N to release latch |
| Response time | <25ms from GFCI trigger to contacts open |
| Duty cycle | Momentary (trip event only) |

**Mechanical integration**: Solenoid plunger interfaces with breaker mechanism latch. Must be positioned to actuate without interfering with thermal-magnetic trip path.

Alternative: Piezoelectric or SMA (shape-memory alloy) actuator if solenoid cannot fit.

### 6. Neutral Routing

Neutral handling is critical for GFCI operation:

```
PANEL NEUTRAL BAR
        │
        │ (pigtail, 10 AWG white)
        ▼
┌───────────────────────────────────────┐
│           NEUTRAL JUNCTION            │
│  (internal bus bar or splice point)   │
└───────┬───────────────────┬───────────┘
        │                   │
   ┌────┴────┐         ┌────┴────┐
   │ CT 1    │         │ CT 2    │
   │ (NEU1   │         │ (NEU2   │
   │  thru)  │         │  thru)  │
   └────┬────┘         └────┬────┘
        │                   │
        ▼                   ▼
   LOAD NEU 1          LOAD NEU 2
   TERMINAL            TERMINAL
```

- Line-side neutral is shared (single pigtail to panel).
- Each load neutral passes through its respective CT before reaching load terminal.
- This ensures differential sensing works: any leakage current to ground creates imbalance in that circuit's CT.

### 7. Load Terminals

Four terminals total:
- **LOAD HOT 1**: Circuit 1 hot output, downstream of breaker mechanism 1.
- **LOAD NEUTRAL 1**: Circuit 1 neutral, downstream of CT 1.
- **LOAD HOT 2**: Circuit 2 hot output, downstream of breaker mechanism 2.
- **LOAD NEUTRAL 2**: Circuit 2 neutral, downstream of CT 2.

Terminal type: Pressure plate or box lug, 14-10 AWG capacity.

### 8. TEST and RESET Mechanisms

Each circuit has independent TEST and RESET:

| Element | Function |
|---------|----------|
| TEST button | Momentary pushbutton, connects ~15mA resistor from HOT to downstream neutral (simulates ground fault, bypasses CT) |
| RESET button | Latching mechanism—resets breaker mechanism after GFCI trip; may be combined with breaker handle or separate |

**Mechanical challenge**: Two TEST and two RESET buttons on a 0.75" wide faceplate. Options:
- Stacked vertically (upper = Circuit 1, lower = Circuit 2)
- Miniature pushbuttons (~4mm diameter)
- Combined TEST/RESET rocker per circuit

---

## Electrical Schematic Partitioning

The KiCad project will be organized into these schematic sheets:

| Sheet | Contents |
|-------|----------|
| `top.kicad_sch` | Top-level block diagram, inter-sheet connections |
| `power_input.kicad_sch` | Bus stab, neutral pigtail, internal distribution |
| `breaker_mech.kicad_sch` | Breaker mechanism symbols (x2), terminals |
| `ct_sense.kicad_sch` | CT symbols, sense amplifier, filter, comparator (x2 channels) |
| `gfci_control.kicad_sch` | GFCI controller ICs, trip drivers, power supply |
| `test_reset.kicad_sch` | TEST circuit resistors, RESET switch connections |

---

## PCB Considerations

- **Layer count**: 2-layer likely sufficient; 4-layer if EMC requires ground plane.
- **Clearances**: Minimum 3mm creepage/clearance for 120VAC per UL requirements.
- **Thermal**: Trip driver MOSFETs may need small copper pour for heat dissipation.
- **Mounting**: Edge-mount or standoff to breaker housing; conformal coat for humidity resistance.

---

## Mechanical CAD Partitioning

FreeCAD/OpenSCAD files will be organized as:

| File | Contents |
|------|----------|
| `enclosure/housing.FCStd` | Main breaker body, QT rail clip, bus stab pocket |
| `enclosure/faceplate.FCStd` | Front cover with TEST/RESET button holes, handle slots |
| `internal/ct_bobbin.FCStd` | CT bobbin/core holder (x2) |
| `internal/trip_mechanism.FCStd` | Thermal-magnetic mechanism placeholder (reference geometry) |
| `internal/solenoid_mount.FCStd` | GFCI trip actuator mounting bracket |
| `internal/terminal_block.FCStd` | Load terminal assembly |

---

## Certification Considerations (UL 489 + UL 943)

This design targets certifiability. Key requirements to design for:

### UL 489 (Circuit Breakers)
- Overcurrent trip calibration (thermal and magnetic)
- Interrupting capacity (10 kAIC)
- Dielectric withstand (1500V for 120V rated)
- Endurance (6000 operations minimum)
- Temperature rise limits

### UL 943 (GFCI)
- Trip threshold: 4-6mA (Class A)
- Trip time: ≤25ms at 250mA, per trip-time curve
- Grounded neutral test
- Rain test, corrosion resistance
- End-of-life indication (for self-testing GFCIs, if implemented)

---

## Open Questions and TBD Items

1. **Handle ganging**: Should both breakers trip together on overcurrent, or operate fully independently? (Affects UL interpretation.)
2. **Self-test**: UL 943 2015 edition requires periodic self-test for receptacle-type GFCIs. Breakers may have different requirements—confirm.
3. **Actuator selection**: Solenoid vs. alternative. Prototype needed to validate fit.
4. **CT core sourcing**: Nanocrystalline vs. ferrite; evaluate sensitivity and cost.
5. **Pigtail vs. plug-on neutral**: Some panels support plug-on neutral. Worth designing for both?

---

## Next Steps

1. Obtain physical Siemens QT tandem breaker for dimensional reference (calipers + 3D scan if possible).
2. Create parametric 3D model of envelope in FreeCAD.
3. Prototype CT with candidate core materials, measure sensitivity.
4. Schematic capture of GFCI sense + trip circuit in KiCad.
5. Breadboard GFCI logic, validate 5mA trip threshold.
