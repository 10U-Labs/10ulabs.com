# Tri-Mode SoC Architecture — Mobile64 Persona (Hardware-Translated)

This document describes the Mobile64 persona of the tri-mode SoC. In this persona, the core appears architecturally as a mainstream 64-bit mobile CPU, but internally the implementation ISA is still RISC-V. The Mobile64 front-end fetches and decodes Mobile64 instructions and then translates them into RISC-V-style µops that the shared RISC-V-native backend executes.

---

## 5. Mobile64 Persona (`mobile64`)

In the `mobile64` persona:

- The architectural ISA is mainstream 64-bit mobile.
- Software sees a standard mobile CPU:
  - 31 general-purpose 64-bit registers plus SP.
  - System registers for control, exceptions, translation tables, etc.
  - Standard paging, exception levels, and memory model.
- Instructions are fetched and decoded using Mobile64 encodings and semantics.

Internally:

- The front-end performs Mobile64-specific fetch and decode.
- A hardware translation layer converts each decoded Mobile64 instruction into one or more RISC-V-style µops that implement the same semantics.
- These µops are then issued into the shared RISC-V-native backend.

The simulator must model Mobile64 execution as:

- Mobile64 front-end + translation behavior.
- Shared RISC-V backend processing the resulting µop stream.

There is no separate Mobile64 backend; all execution goes through the common core.

---

## 5.1 Mobile64 ISA Characteristics Relevant to Translation

Important properties:

- Instruction length:
  - Fixed 32-bit instructions.
- Addressing modes:
  - Base + immediate.
  - Base + scaled index.
  - Optional writeback/update to base.
- Condition flags:
  - Certain instructions set and use condition codes.
- Vector/FP:
  - Vector and FP instructions with varying vector widths.
- System/barrier instructions:
  - Manage memory ordering and system state.

These characteristics affect:

- Decode complexity (richer addressing, condition codes).
- Average number of RISC-V-style µops per Mobile64 instruction.
- Effects of system/barrier instructions on pipeline progress.

The simulator must approximate these effects using category-level parameters.

---

## 5.2 Mobile64 Front-End Behavior

### 5.2.1 Instruction Fetch

- Fetch bandwidth from L1I:
  - 16 bytes per cycle.
- Instruction length:
  - Fixed 4 bytes per instruction.
- Maximum instructions fetched per cycle:
  - Up to 4 Mobile64 instructions per cycle, limited by fetch bandwidth.

### 5.2.2 Decode

- Decode width:
  - Up to 4 Mobile64 instructions decoded per cycle, subject to complexity.
- Compared to RISC-V:
  - Decode is slightly more complex due to richer addressing and condition flags, but still regular due to fixed-length instructions.

The simulator can treat decode throughput as close to RISC-V, with reductions only for instruction categories that require additional translation work.

---

## 5.3 Translation from Mobile64 Instructions to RISC-V-Style µops

The translation layer converts each decoded Mobile64 instruction into RISC-V-style µops.

Examples of mapping patterns:

- Simple integer ALU and branch instructions:
  - Examples: ADD, SUB, AND, ORR, EOR, simple conditional branches.
  - Mapping:
    - 1–2 µops, including:
      - A RISC-V-style ALU or compare µop.
      - Optional flag manipulation or conditional evaluation.

- Load and store instructions:
  - Addressing modes: base + immediate, base + scaled index, with optional writeback.
  - Mapping:
    - Address calculation:
      - RISC-V-style ALU µops to compute effective address and any writeback.
    - Memory operation:
      - RISC-V-style load or store µop.
    - Typical total:
      - Simple base+imm load/store: 1–2 µops.
      - Base+index+update load/store: 2–3 µops.

- Vector/FP instructions:
  - Vector and FP arithmetic and logical operations.
  - Mapping:
    - 2 or more RISC-V-style µops, depending on vector width and decomposition into the backend's vector/granularity.
    - Example: a 128-bit operation mapping to 1–2 µops, a 256-bit one to 2–4 µops if modeled.

- System/barrier instructions:
  - Mapping:
    - 1 or more µops, possibly modeled as pipeline fences or short serialized sequences.
    - These instructions may reduce effective throughput in segments of the instruction stream.

The simulator does not need to model each Mobile64 instruction individually. Instead, it must define:

- Average µops per instruction per category.
- Any category-specific decode/translation limitations.

These drive µop counts and effective front-end throughput.

---

## 5.4 Workload Modeling for Mobile64

For the Mobile64 persona, define workloads in terms of instruction and translation mix.

A workload definition includes:

- `instr_count`:
  - Total number of Mobile64 architectural instructions to retire.

- Instruction mix fractions (sum to ~1):
  - `alu_fraction` (scalar integer and branch)
  - `load_fraction`
  - `store_fraction`
  - `fp_vec_fraction` (vector/FP)
  - `system_fraction` (system/barrier)
  - `complex_fraction` (if modeling infrequent multi-µop sequences separately)

- Average translation parameters per category:
  - `avg_uops_per_instr_category` (RISC-V-style µops post-translation)

From these, the simulator performs:

1. Per-category instruction counts:
   - `instr_count_category = instr_count * category_fraction`.

2. Per-category µop counts:
   - `uops_category = instr_count_category * avg_uops_per_instr_category`.

3. Total µops:
   - Sum `uops_category` across categories for Mobile64.

4. Front-end throughput:
   - Use fetch bandwidth (16 bytes/cycle) and fixed 4-byte instruction length for up to 4 instructions per cycle.
   - Enforce decode limits (max 4 instructions and max 4 µops per cycle).
   - Derive `ipc_frontend` for Mobile64.

5. Backend throughput:
   - Derive µop mix (ALU, load, store, FP/vec, system/complex).
   - Apply shared backend configuration:
     - ALU µops vs 3 ALUs.
     - Load µops vs 2 load units and cache/memory latency.
     - Store µops vs 1 store unit.
     - FP/vec µops vs 2 FP/vector units.
     - Stall cycles due to cache misses and branch mispredictions.
   - Compute `ipc_backend`.

6. Effective IPC and runtime:
   - `ipc_effective = min(ipc_frontend, ipc_backend)`.
   - `cycles = instr_count / ipc_effective`.
   - `runtime_seconds = cycles / (clock_ghz * 1e9)`.

Mobile64 performance differences vs RISC-V must result from:

- Slightly higher average µops per instruction due to translation and richer addressing.
- Possible additional stalls for system/barrier instructions.

No persona-specific penalty multipliers are allowed beyond what emerges from this translation and shared-backend model.
