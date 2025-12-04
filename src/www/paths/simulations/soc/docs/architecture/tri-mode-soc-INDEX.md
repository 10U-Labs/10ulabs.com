# Tri-Mode SoC Simulation Spec — Index

This index lists the component files that together define the tri-mode SoC architecture and simulation model. Each file is self-contained and can be given to a code model (e.g., Claude Code) as needed.

1. Core Concept and Personas  
   File: `tri-mode-soc-section1-core-personas.md`  
   Content: Defines the overall tri-mode SoC idea, explains that the single core is RISC-V-native, and describes the three personas (`riscv`, `x86_64`, `arm64`) and how they present different ISAs on top of the same RISC-V core.

2. Shared RISC-V-Native Backend  
   File: `tri-mode-soc-section2-backend.md`  
   Content: Specifies the fixed backend microarchitecture used by all personas, including issue width, ROB size, execution units, cache hierarchy, memory latencies, and branch prediction configuration.

3. RISC-V Persona (Native ISA)  
   File: `tri-mode-soc-section3-riscv-persona.md`  
   Content: Describes the RISC-V (`riscv`) persona as the native ISA path, including ISA characteristics, front-end behavior, and simple 1:1 (or near 1:1) mapping from RISC-V instructions to backend µops.

4. x86-64 Persona (Hardware-Translated)  
   File: `tri-mode-soc-section4-x86-persona.md`  
   Content: Describes the x86-64 (`x86_64`) persona, including variable-length instruction encodings, x86-specific front-end behavior, and hardware translation rules from x86-64 instructions to RISC-V-style µops.

5. ARM64 Persona (Hardware-Translated)  
   File: `tri-mode-soc-section5-arm64-persona.md`  
   Content: Describes the ARM64 (`arm64`) persona, including fixed 32-bit encodings, richer addressing modes, and hardware translation rules from ARM64 instructions to RISC-V-style µops.

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
