# Tri-Mode SoC Simulation Spec — Index

This index lists the component files that together define the tri-mode SoC architecture and simulation model. Each file is self-contained and can be given to a code model (e.g., Claude Code) as needed.

## Disclaimer

This simulator is an independent research project by 10U Labs. It is not affiliated with, endorsed by, or sponsored by any processor vendor.

This simulator does not implement, emulate, or translate any instruction set. It does not decode, execute, or process actual instructions. It provides analytical performance modeling using publicly known architectural characteristics (instruction lengths, µop ratios, cache behavior) derived from published academic studies and independent measurements.

The tri-mode SoC supports three application personas:
- **RISC-V**: Native open-standard 64-bit applications
- **Desktop64**: Conventional 64-bit desktop applications
- **Mobile64**: Mainstream 64-bit mobile applications

1. Core Concept and Personas
   File: `tri-mode-soc-section1-core-personas.md`
   Content: Defines the overall tri-mode SoC idea, explains that the single core is RISC-V-native, and describes the three personas and how they present different application compatibility layers on top of the same RISC-V core.

2. Shared RISC-V-Native Backend
   File: `tri-mode-soc-section2-backend.md`
   Content: Specifies the fixed backend microarchitecture used by all personas, including issue width, ROB size, execution units, cache hierarchy, memory latencies, and branch prediction configuration.

3. RISC-V Persona (Native)
   File: `tri-mode-soc-section3-riscv-persona.md`
   Content: Describes the RISC-V persona as the native path, including characteristics, front-end behavior, and simple 1:1 (or near 1:1) mapping from RISC-V instructions to backend µops.

4. Desktop64 Persona (Hardware-Translated)
   File: `tri-mode-soc-section4-desktop64-persona.md`
   Content: Describes the Desktop64 persona for conventional 64-bit desktop applications, including variable-length instruction encodings, front-end behavior, and hardware translation rules.

5. Mobile64 Persona (Hardware-Translated)
   File: `tri-mode-soc-section5-mobile64-persona.md`
   Content: Describes the Mobile64 persona for mainstream 64-bit mobile applications, including fixed 32-bit encodings, richer addressing modes, and hardware translation rules.

6. Workload Modeling, Throughput, and API Shape
   File: `tri-mode-soc-section6-workload-and-api.md`
   Content: Defines how workloads are represented (instruction mix and translation parameters per persona), how front-end and backend limited IPC are computed, how runtime is derived, and the JSON input/output shape for a simulation API.

7. References
   File: `tri-mode-soc-section7-references.md`
   Content: Lists academic papers, technical reports, and industry sources used to derive workload parameters (instruction mix, cache behavior, branch prediction, instruction encoding) and validate the simulation model.

8. Appendix A: Parameter Derivation Methodology
   File: `tri-mode-soc-appendix-a-parameter-derivation.md`
   Content: Explains why simulation parameters are hardcoded constants, how each value was derived from research, the weighted average calculations for µop translation ratios, and validation approach.

You can give these files to a code model individually (for focused tasks) or together (for full-context implementation of the tri-mode SoC simulator and its API).
