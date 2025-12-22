# Tri-Mode SoC Architecture — x86-64 Persona (Hardware-Translated)

This document describes the x86-64 persona of the tri-mode SoC. In this persona, the core appears architecturally as an x86-64 CPU, but internally the implementation ISA is still RISC-V. The x86-64 front-end fetches and decodes x86-64 instructions and then translates them into RISC-V-style µops that the shared RISC-V-native backend executes.

---

## 4. x86-64 Persona (`x86_64`)

In the `x86_64` persona:

- The architectural ISA is 64-bit x86-64.
- Software sees a standard x86-64 CPU:
  - 16 general-purpose registers (RAX, RBX, etc.).
  - Flags register (EFLAGS/RFLAGS) and its condition codes.
  - x86-64 paging and segmentation behavior (segmentation largely flat in 64-bit mode).
  - x86 privilege levels and memory model.
- Instructions are fetched and decoded according to x86-64 encodings and semantics.

Internally:

- The front-end performs x86-64-specific fetch and decode.
- A hardware translation layer converts each decoded x86-64 instruction into one or more RISC-V-style µops that implement the same observable behavior.
- These µops are then issued into the same RISC-V-native backend described in the shared-backend document.

The simulator must model x86-64 execution as a combination of:

- x86-64 front-end and translation rules.
- Shared RISC-V backend processing the resulting µop stream.

No separate x86-64 backend exists; everything passes through the common RISC-V-native core.

---

## 4.1 x86-64 ISA Characteristics Relevant to Translation

Important properties:

- Variable-length instruction encoding:
  - Instructions range from 1 to 15 bytes.
  - Prefix bytes (REX, operand-size override, SSE/AVX prefixes).
- Complex addressing modes:
  - Base + index × scale + displacement.
- Implicit flags:
  - Many arithmetic and logical instructions implicitly read and write condition flags.
- Rich instruction set:
  - Scalar integer, FP, and vector (SSE/AVX).
  - System instructions, string operations, etc.
- Some instructions are internally implemented via microcode.

These characteristics impact:

- Average instruction length (bytes/instruction).
- Complexity of decode.
- Average number of RISC-V-style µops per x86-64 instruction.

The simulator must approximate these effects via instruction mix and translation rules.

---

## 4.2 x86-64 Front-End Behavior

### 4.2.1 Instruction Fetch

- Fetch bandwidth from L1I:
  - 16 bytes per cycle.
- Instruction boundaries:
  - Not aligned; instructions are variable-length.
  - A pre-decode stage identifies instruction boundaries in the fetched bytes.

Simplified model:

- Assume an average x86-64 instruction length parameter, `avg_x86_bytes_per_instr` (e.g., 3–5 bytes).
- Maximum instructions fetched per cycle:
  - Approximately `16 / avg_x86_bytes_per_instr`, subject to decode limits.
- Occasional extra cycles can be attributed to complex or long instructions, effectively reducing fetch/decode throughput for those categories.

### 4.2.2 Decode

- Decode width:
  - Up to 4 “simple” x86-64 instructions decoded per cycle.
- Complex or long instructions:
  - May reduce effective decode width (e.g., fewer than 4 per cycle).
- For the analytic model:
  - Assign decode cost by instruction category and enforce:
    - A maximum number of instructions per cycle.
    - A maximum number of emitted µops per cycle.

The simulator should derive a front-end limited instruction throughput for x86-64 based on fetch and decode limits combined.

---

## 4.3 Translation from x86-64 Instructions to RISC-V-Style µops

The translation layer converts each decoded x86-64 instruction into one or more RISC-V-style µops that preserve x86 semantics. Examples of mapping patterns:

- Simple integer ALU and branch instructions:
  - Examples: ADD, SUB, AND, OR, XOR, CMP, TEST, simple conditional branches.
  - Mapping:
    - 1–2 µops, including:
      - A RISC-V-style ALU or compare µop.
      - Explicit flag-update or condition evaluation modeled by RISC-V-style operations if needed.

- Load and store instructions:
  - x86 addressing modes: base + index × scale + displacement.
  - Mapping:
    - Address calculation:
      - Sequence of RISC-V-style ALU µops (e.g., ADD, MUL, ADD).
    - Memory operation:
      - One RISC-V-style load or store µop.
    - Typical total: 2–3 µops per x86 load/store.

- SSE/AVX vector instructions:
  - Mapping:
    - Multiple RISC-V-style vector or scalar µops, depending on vector width and how it is split.
    - Example: a 256-bit vector add may become 2–4 µops in the backend.

- Complex/microcoded instructions:
  - Examples: some string instructions, multi-step operations, certain system instructions.
  - Mapping:
    - Longer sequences, e.g., 8–32 µops representing a short RISC-V-type micro-routine.

The simulator does not need to model each exact instruction; instead it must define, for each x86 instruction category:

- Average µops per instruction after translation.
- Decode and translation cost per instruction.

These category-level averages drive total µop counts and front-end throughput.

---

## 4.4 Workload Modeling for x86-64

For the x86-64 persona, the workload should be defined at the instruction mix level. A workload definition includes:

- `instr_count`:
  - Total number of x86-64 architectural instructions to retire.

- Instruction mix fractions (sum to ~1):
  - `alu_fraction` (simple scalar integer and branch)
  - `load_fraction`
  - `store_fraction`
  - `fp_vec_fraction` (SSE/AVX)
  - `complex_fraction` (microcoded, multi-step, or otherwise expensive)
  - Optional `other_fraction` if needed

- Average translation parameters per category:
  - `avg_bytes_per_instr_category` (for fetch modeling; especially important for x86-64)
  - `avg_uops_per_instr_category` (RISC-V-style µops post-translation)
  - Category-specific decode cost if needed

From these, the simulator performs:

1. Per-category instruction counts:
   - `instr_count_category = instr_count * category_fraction`.

2. Per-category µop counts:
   - `uops_category = instr_count_category * avg_uops_per_instr_category`.

3. Total µops:
   - Sum all `uops_category`.

4. Front-end throughput:
   - Use fetch bandwidth (16 bytes/cycle), `avg_bytes_per_instr` values, and decode width (max instructions and µops per cycle) to compute `ipc_frontend` for x86-64.

5. Backend throughput:
   - Derive µop mix (ALU, load, store, FP/vec, branch, complex).
   - Apply the shared backend configuration:
     - ALU µops vs 3 ALUs.
     - Load µops vs 2 load units and cache/memory latency.
     - Store µops vs 1 store unit.
     - FP/vec µops vs 2 FP/vector units.
     - Stall cycles from cache misses and branch mispredictions.
   - Compute `ipc_backend`.

6. Effective IPC and runtime:
   - `ipc_effective = min(ipc_frontend, ipc_backend)`.
   - `cycles = instr_count / ipc_effective`.
   - `runtime_seconds = cycles / (clock_ghz * 1e9)`.

All of these steps must be based on the RISC-V-native backend and the x86-64 translation rules described above. No separate x86-specific backend or arbitrary penalty multipliers are allowed.
