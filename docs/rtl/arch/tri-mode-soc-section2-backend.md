# Tri-Mode SoC Architecture — Shared RISC-V-Native Backend Microarchitecture

All personas use the same backend. The backend’s semantics and micro-operations are RISC-V-based. The simulator must treat this backend as the single physical core that all personas share.

---

## 2. Shared Backend Configuration

These parameters define the SoC’s single core and must be identical for all personas. Together they form the `soc_config` object.

- `issue_width`: 4  (maximum number of µops that can be issued per cycle)
- `backend_dispatch_width`: 4  (maximum number of µops that can be dispatched into the scheduling window per cycle)
- `rob_entries`: 128  (maximum in-flight µops in the reorder buffer)
- `int_phys_regs`: 192  (physical integer registers)
- `fp_vec_phys_regs`: 160  (physical FP/vector registers)
- `load_queue_entries`: 64  (in-flight loads)
- `store_queue_entries`: 64  (in-flight stores)
- `l1i_size_kb`: 32  (L1 instruction cache size)
- `l1d_size_kb`: 32  (L1 data cache size)
- `l2_size_kb`: 512  (L2 cache size)
- `clock_ghz`: 3.0  (core frequency)
- `pipeline_depth_estimate`: 18  (end-to-end pipeline depth used for branch penalty approximation)

The simulation must not change these values per persona. They define the identity and capabilities of the single tri-mode core.

---

## 2.1 Execution Resources

The backend executes RISC-V-style µops using the following functional units and latencies. These units are shared by all personas and must be respected when computing throughput.

Execution units:

- Integer ALUs: 3
- Integer mul/div units: 1
- FP/vector units: 2
- Load units: 2
- Store units: 1

Representative latencies:

- Integer ALU µops: 1 cycle
- Branch µops: 1 cycle execution, resolved in 1–2 cycles
- Integer mul: 3 cycles
- Integer div: 12–20 cycles (use a single representative latency value in the model)
- FP add/mul: 3–4 cycles
- FP div: 12–20 cycles
- Load (L1 hit): 4 cycles from issue to data ready
- Store address µops: 1 cycle (store commit when safe at ROB head and memory system is ready)

The simulator may be cycle-accurate or throughput-based, but it must not allow more µops per cycle than these unit counts and the configured `issue_width` and `backend_dispatch_width`.

---

## 2.2 Memory Hierarchy

The tri-mode core has a shared memory hierarchy for all personas. The simulator must treat caches and memory as common resources.

- L1 instruction cache (L1I):
  - Size: 32 KiB
  - Associativity: 4-way
  - Access latency: 1 cycle hit

- L1 data cache (L1D):
  - Size: 32 KiB
  - Associativity: 8-way
  - Access latency: 1 cycle hit

- L2 cache:
  - Size: 512 KiB
  - Associativity: 8-way
  - Access latency: 10 cycles beyond L1

- Main memory:
  - Access latency: 120 cycles beyond L1

For each workload scenario, the simulator should use the following parameters:

- `l1d_hit_rate`: fraction of loads that hit in L1D
- `l2_hit_rate`: fraction of L1D misses that hit in L2
- Remaining fraction is treated as memory hits

From these, the simulator must compute effective load latencies and the resulting stall behavior. The same parameters and hierarchy apply regardless of persona.

---

## 2.3 Branch Prediction

The tri-mode core uses a single branch prediction subsystem shared by all personas.

Branch predictor configuration:

- Global predictor: 4K entries
- Branch target buffer (BTB): 4K entries
- Return address stack: 32 entries
- Mis-predict penalty: 12 cycles (from fetch of wrong-path instruction to fetch of correct-path instruction)

For each workload scenario, the simulator should use:

- `branch_fraction`: fraction of persona-level instructions that are branches
- `branch_mispredict_rate`: fraction of branches that are mispredicted

The simulator must compute the number of mispredictions and the total mispredict penalty cycles and incorporate these into effective IPC and runtime for each persona. The predictor hardware is the same for all personas; only branch density and mispredict rates differ by workload.
