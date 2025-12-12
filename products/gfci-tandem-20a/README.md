# 2x20A Tandem GFCI Breaker

Open-source dual 20A Class A GFCI breaker in Siemens QT tandem form factor.

## Specifications

- **Form Factor**: Siemens QT tandem (single-pole width, two circuits)
- **Rating**: 2 x 20A @ 120VAC, 60Hz
- **GFCI Class**: A (5mA trip threshold)
- **Standards Target**: UL 489 (circuit breakers) + UL 943 (GFCI)
- **Circuits**: Two independent GFCI-protected circuits, each with own HOT/NEUTRAL/TEST/RESET

## Project Structure

```
gfci-tandem-20a/
├── kicad/                  # KiCad 8.x project files
│   ├── symbols/            # Custom schematic symbols
│   ├── footprints/         # Custom PCB footprints
│   └── 3dmodels/           # STEP/WRL models for 3D preview
├── mechanical/             # Mechanical CAD (FreeCAD/OpenSCAD)
│   ├── enclosure/          # Housing, covers, bus stab
│   └── internal/           # CT bobbins, trip mechanisms, terminals
├── docs/                   # Technical documentation
│   └── architecture.md     # System architecture overview
├── simulation/             # Circuit simulation
│   └── spice/              # LTspice/ngspice netlists
├── test/                   # Test documentation and fixtures
│   ├── compliance/         # UL 489/943 test procedures
│   └── fixtures/           # Test jig designs
└── bom/                    # Bill of materials, sourcing
```

## Tools Required

- **Schematic/PCB**: KiCad 8.x
- **Mechanical CAD**: FreeCAD 0.21+ or OpenSCAD
- **Simulation**: ngspice or LTspice
- **Documentation**: Markdown, draw.io (for diagrams)

## Getting Started

See `docs/architecture.md` for system-level design overview.
