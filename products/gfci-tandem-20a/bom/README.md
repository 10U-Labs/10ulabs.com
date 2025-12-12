# Bill of Materials

This directory contains BOM files and sourcing notes.

## BOM Files

| File | Description |
|------|-------------|
| `bom_electronics.csv` | PCB components (resistors, ICs, connectors) |
| `bom_mechanical.csv` | Enclosure, terminals, hardware |
| `bom_magnetics.csv` | CT cores, bobbins, wire |

## Key Components (TBD)

### GFCI Controller IC
- Candidate: LM1851 or equivalent
- Qty: 2 (one per channel)
- Sources: Digi-Key, Mouser

### CT Core
- Material: Nanocrystalline or high-perm ferrite
- Size: OD ~10mm, ID ~6mm, H ~5mm
- Sources: TBD (evaluate Vacuumschmelze, Magnetics Inc.)

### Trip Actuator
- Type: Miniature push solenoid
- Voltage: 5V DC
- Force: >1N
- Sources: TBD

### Terminals
- Type: Pressure plate, 14-10 AWG
- Qty: 4 (2x HOT, 2x NEUTRAL)
