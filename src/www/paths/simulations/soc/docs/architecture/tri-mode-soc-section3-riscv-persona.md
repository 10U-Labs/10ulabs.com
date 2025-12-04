# Tri-Mode SoC Architecture — RISC-V Persona (Native ISA)

This document describes the RISC-V persona of the tri-mode SoC. In this persona, the core executes RISC-V instructions natively on the RISC-V-based backend with no translation layer.

---

## 3. RISC-V Persona (`riscv`)

In the `riscv` persona:

- The architectural ISA is RV64GC.
- Software sees a standard 64-bit RISC-V CPU:
  - 64-bit general-purpose registers x0–x31.
  - Standard control/status registers.
  - RISC-V privilege levels and memory model.
- Instructions are fetched and decoded as RISC-V instructions and mapped directly to RISC-V-style µops executed by the backend.

The simulator must treat this persona as the **native ISA** path: there is no foreign-ISA translation overhead for RISC-V itself.

---

## 3.1 ISA Characteristics

Key properties of the RISC-V ISA for this model:

- Base ISA: RV64I with standard extensions G (integer, multiplication/division, atomics, compressed, and standard FP).
- Instruction lengths:
  - Standard instructions: 32 bits.
  - Compressed instructions: 16 bits (RVC).
- Load/store architecture:
  - Memory operations use simple base + immediate addressing.
  - No complex scaled index or auto-update addressing built into the core ISA.
- No implicit condition flags:
  - Comparisons and branches use explicit register values.

The combination of fixed/simple encodings and the lack of implicit flags make RISC-V relatively easy to decode and execute.

---

## 3.2 Front-End Behavior

For the RISC-V persona, the front-end is optimized to decode RISC-V instructions directly into backend µops.

### 3.2.1 Instruction Fetch

- Instruction fetch bandwidth from L1I:
  - 16 bytes per cycle.
- Instruction alignment:
  - 32-bit instructions are naturally aligned to 4-byte boundaries.
  - 16-bit compressed instructions may appear in mixed streams but remain aligned to 2-byte boundaries.
- In the best case:
  - Up to 8 compressed (16-bit) or 4 full (32-bit) instructions can be fetched per cycle.

The simulator should treat fetch as capable of supplying more than enough RISC-V instructions per cycle in typical code, constrained primarily by the 16-byte fetch bandwidth.

### 3.2.2 Decode

- Maximum of 4 RISC-V instructions decoded per cycle.
- Decoding is straightforward due to fixed instruction formats and simple field extraction.
- Compressed instructions are expanded to their 32-bit logical forms during decode.

The decode stage outputs RISC-V-style µops for the backend. For RISC-V, decoding is not expected to be a major bottleneck relative to backend capacity.

---

## 3.3 µop Mapping for RISC-V

The mapping from RISC-V instructions to backend µops is simple:

- Simple integer ALU instructions:
  - Example: ADD, SUB, AND, OR, XOR, shifts.
  - Mapping: 1 µop each.

- Branch instructions:
  - Example: BEQ, BNE, BLT, BGE.
  - Mapping: 1 µop each.

- Load instructions:
  - Example: LW, LD, FLW, FLD.
  - Mapping: 1 µop each.

- Store instructions:
  - Example: SW, SD, FSW, FSD.
  - Mapping: 1 µop each.

- Atomic instructions:
  - Example: LR/SC pairs and AMOs.
  - Mapping: 2 µops (address/lock + operation/commit).

- Misaligned accesses (if modeled):
  - Mapping: 2 or more µops (may be decomposed into aligned operations).

- Scalar FP instructions:
  - Example: FADD, FSUB, FMUL, FDIV.
  - Mapping: 1 µop each for add/mul; div modeled with longer latency but still 1 µop.

- Simple vector instructions (if included):
  - Mapping: 2 µops or more depending on vector width and internal representation.

For the initial analytic model, it is acceptable to treat:

- Integer ALU, branch, load, store as 1 µop each.
- Atomics and misaligned as 2 µops each.
- Scalar FP as 1 µop each.
- Vector as 2 µops each.

The simulator must compute total RISC-V µops for a given workload based on these rules and instruction mix.

---

## 3.4 Workload Modeling for RISC-V

For the RISC-V persona, a workload definition should include:

- `instr_count`:
  - Total number of RISC-V architectural instructions to retire in the simulation.

- Instruction mix fractions (sum to ~1):
  - `alu_fraction`
  - `load_fraction`
  - `store_fraction`
  - `branch_fraction`
  - `fp_vec_fraction`
  - `complex_fraction` (for atomics, misaligned, or other multi-µop patterns)

From these and the µop mapping:

1. Compute per-category instruction counts:
   - `instr_count_category = instr_count * category_fraction`

2. Compute per-category µop counts:
   - `uops_category = instr_count_category * avg_uops_per_instr_category`

3. Sum across categories to get total RISC-V µops.

These RISC-V-native µops then feed the shared backend, which is modeled by the configuration in the shared-backend document. No extra translation or decode overhead is applied beyond what is described here for RISC-V.
