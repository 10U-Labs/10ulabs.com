# Tri-Mode SoC RTL Project — Master Plan

## Project Overview

A tri-mode SoC with three ISA personas (RISC-V, x86-64, ARM64) sharing a unified RISC-V-native backend, simulated with Verilator.

**RTL Location:** `src/rtl/`

## Phase Summary

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Simple in-order RV64I core | ✅ COMPLETE |
| **Phase 2** | Add OoO (ROB, issue queue, renaming) | 🔲 Not started |
| **Phase 3** | Add cache hierarchy | 🔲 Not started |
| **Phase 4** | Add translation front-ends (ARM64, x86-64) | 🔲 Not started |

---

## Phase 1: In-Order RV64I Core ✅ COMPLETE

**Goal:** 5-stage pipeline (Fetch → Decode → Execute → Memory → Writeback)

**Files Created:** 31 files
- 3 packages (`types_pkg.sv`, `rv64_pkg.sv`, `pipeline_pkg.sv`)
- 16 core modules (regfile, ALU, decoder, pipeline stages, hazards)
- 3 memory/SoC modules
- 9 testbench files (Verilator C++, 5 assembly tests, Makefiles)

**Instructions Supported:** 37 RV64I instructions (ALU, shifts, loads, stores, branches, jumps, W-variants)

**CI Workflow:** `.github/workflows/rtl_verilator.yml`

---

## Phase 2: Out-of-Order Execution 🔲 NOT STARTED

**Goal:** Transform in-order core to 4-wide superscalar OoO

**Key Components to Add:**
1. **Register Renaming**
   - Physical register file: 192 int, 160 FP/vec
   - Register alias table (RAT)
   - Free list management

2. **Reorder Buffer (ROB)**
   - 128 entries
   - In-order retirement
   - Precise exceptions

3. **Issue Queues**
   - Separate queues for ALU, MUL/DIV, FP, Load, Store
   - Out-of-order issue when operands ready

4. **Execution Units**
   - 3 ALU, 1 mul/div, 2 FP/vec, 2 load, 1 store

5. **Load/Store Queue**
   - 64-entry load queue
   - 64-entry store queue
   - Memory disambiguation

**Files to Modify:**
- `src/rtl/core/pipeline/core_top.sv` → major restructure
- `src/rtl/core/regfile/regfile.sv` → expand to physical register file
- New: `src/rtl/core/ooo/rob.sv`, `src/rtl/core/ooo/rat.sv`, `src/rtl/core/ooo/issue_queue.sv`, etc.

---

## Phase 3: Cache Hierarchy 🔲 NOT STARTED

**Goal:** Add realistic memory hierarchy per spec

**Cache Parameters:**
- L1I: 32KB, 4-way, 1-cycle hit
- L1D: 32KB, 8-way, 1-cycle hit
- L2: 512KB, 8-way, 10-cycle hit
- Main memory: 120-cycle latency

**Key Components:**
1. Cache controllers (L1I, L1D, L2)
2. Cache line state machines
3. Miss handling (MSHR)
4. Write buffer
5. Prefetcher (optional)

**Files to Add:**
- `src/rtl/core/cache/l1i_cache.sv`
- `src/rtl/core/cache/l1d_cache.sv`
- `src/rtl/core/cache/l2_cache.sv`
- `src/rtl/core/cache/cache_controller.sv`

---

## Phase 4: Multi-ISA Translation 🔲 NOT STARTED

**Goal:** Add ARM64 and x86-64 hardware translation front-ends

**Architecture:**
```
[ARM64 Fetch/Xlat] ──┐
[x86-64 Fetch/Xlat] ─┼──► [Unified RISC-V Backend]
[RV64 Fetch/Decode] ─┘
```

**Key Components:**
1. **Persona Select Register** - latched at reset
2. **ARM64 Translator**
   - Fixed 32-bit instruction decode
   - 1-2 µops per instruction
3. **x86-64 Translator**
   - Variable-length instruction decode (1-15 bytes)
   - 1-3+ µops per instruction
   - Complex instruction cracking

**Files to Add:**
- `src/rtl/core/frontend/arm64/arm64_decoder.sv`
- `src/rtl/core/frontend/arm64/arm64_translator.sv`
- `src/rtl/core/frontend/x86/x86_decoder.sv`
- `src/rtl/core/frontend/x86/x86_translator.sv`
- `src/rtl/core/frontend/persona_mux.sv`

---

## Architecture Documentation

See `docs/rtl/arch/` for detailed specs:
- `tri-mode-soc-INDEX.md`
- `tri-mode-soc-section1-core-personas.md`
- `tri-mode-soc-section2-backend.md`
- `tri-mode-soc-section3-riscv-persona.md`
- `tri-mode-soc-section4-x86-persona.md`
- `tri-mode-soc-section5-arm64-persona.md`
- `tri-mode-soc-section6-workload-and-api.md`

---

## Next Actions

1. ~~Create CI workflow~~ ✅ Done
2. ~~Copy plan to repo~~ ✅ Done
3. ~~Copy arch docs to repo~~ ✅ Done
4. **Fix any Phase 1 bugs** - Debug failing tests if any
5. **Plan Phase 2 in detail** - Design OoO microarchitecture
6. **Implement Phase 2** - ROB, register renaming, issue queues
