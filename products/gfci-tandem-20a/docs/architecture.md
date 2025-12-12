# GFCI Tandem 20A - High-Level Internal Architecture

## Physical Layout

- Two "stories" inside one Siemens QT tandem body
  - Top = Circuit 1
  - Bottom = Circuit 2

## Per-Circuit Components (Circuit 1 & Circuit 2)

- Thermal-magnetic breaker mechanism
- CT (current transformer) around hot + neutral conductors
- Trip actuator
- HOT load terminal
- NEUTRAL load terminal

## Shared PCB

- Runs down the side/back of the breaker body
- Dual-channel GFCI logic (ch1/ch2)
- Power supply
- Auto self-test circuitry
- Drivers for the two trip actuators

## Line Side

- Two bus connections for the two hots
- One shared neutral feed (pigtail or plug-on-neutral) into the PCB

## Load Side

- Four terminals total:
  - HOT1
  - NEUTRAL1
  - HOT2
  - NEUTRAL2
- Neutrals routed through their respective CTs
