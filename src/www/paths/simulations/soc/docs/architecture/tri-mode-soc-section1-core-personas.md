# Tri-Mode SoC Architecture — Core Concept and Personas

This document describes a tri-mode SoC built around a single physical CPU core that supports three application personas:

- RISC-V (RV64GC) - Native open-standard 64-bit applications
- Desktop64 - Conventional 64-bit desktop applications
- Mobile64 - Mainstream 64-bit mobile applications

The actual implementation ISA of the core is RISC-V. The internal execution engine and its micro-operations are defined in terms of RISC-V semantics. The Desktop64 and Mobile64 personas are implemented as hardware-accelerated translation front-ends that accept Desktop64 or Mobile64 instructions and translate them into the core's internal RISC-V-style µop stream. All three personas share this same RISC-V-native backend.

Differences in performance between personas must emerge from:

- Instruction encoding differences (fixed vs variable length)
- Translation rules (foreign instruction → RISC-V-like µops)
- Decode and fetch bandwidth limits
- Instruction mix (ALU vs load/store vs branch vs FP/vec)
- Interactions with shared backend resources

No arbitrary per-persona penalty multipliers are allowed. Any slowdown in Desktop64 or Mobile64 vs RISC-V must come from the modeled behavior of the front-ends and translator, not from external scaling factors.

---

## 1. SoC and Persona Overview

- The SoC has exactly one CPU core in this prototype.

- At reset, a persona select register is latched to one of three values:
  - `riscv`
  - `desktop64`
  - `mobile64`

- The selected persona defines the architectural view exposed to software:

  - `riscv` persona
    - Exposes the RV64GC ISA natively.
    - Software sees a normal 64-bit RISC-V CPU.
    - Instructions are decoded directly into RISC-V-style µops executed by the backend.

  - `desktop64` persona
    - Exposes a conventional 64-bit desktop ISA.
    - Software sees a standard desktop CPU (registers, flags, paging, privilege levels, memory model).
    - Instructions are fetched and decoded as Desktop64, then translated in hardware into RISC-V-style µops that implement equivalent semantics, which the backend executes.

  - `mobile64` persona
    - Exposes a mainstream 64-bit mobile ISA.
    - Software sees a standard mobile CPU (registers, system registers, page tables, memory model).
    - Instructions are fetched and decoded as Mobile64, then translated in hardware into RISC-V-style µops that implement equivalent semantics, which the backend executes.

- After reset, only one persona is active at a time. Persona changes require a reset in this prototype; there is no runtime switching between ISAs on a single boot.

- Internally, the core is structurally split into:

  - A persona-specific front-end and translator that:
    - Fetches instruction bytes for the selected ISA.
    - Decodes those instructions according to that ISA's encoding.
    - Translates them into a sequence of RISC-V-style µops.

  - A shared RISC-V-native backend that:
    - Renames, schedules, and executes those µops.
    - Applies a single set of resource limits (issue width, ROB size, execution units, caches) regardless of persona.
    - Retires µops in program order and updates the architectural state corresponding to the active persona.

The simulator must model personas as different front-ends feeding the same backend. RISC-V instructions execute natively; Desktop64 and Mobile64 instructions are hardware-translated into RISC-V-style µops that then execute on the same core.
