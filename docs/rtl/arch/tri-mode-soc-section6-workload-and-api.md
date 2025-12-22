# Tri-Mode SoC Architecture — Workload Modeling, Throughput, and API Shape

This document describes how workloads are modeled across personas, how throughput and runtime are computed from the tri-mode SoC architecture, and the expected input/output shape of a simulation API.

---

## 6. Workload Modeling Across Personas

Workloads are modeled at the level of aggregated instruction mixes, not full instruction traces. Each persona has its own instruction-level view and translation rules into RISC-V-style µops, but all workloads share the same basic structure.

For any persona `p` ∈ {`riscv`, `x86_64`, `arm64`}, a workload definition includes:

- `instr_count_p`:
  - Total number of architectural instructions for persona `p` to retire in the simulation.
- Instruction mix fractions for persona `p` (must sum to approximately 1):
  - `alu_fraction_p`
  - `load_fraction_p`
  - `store_fraction_p`
  - `branch_fraction_p`
  - `fp_vec_fraction_p`
  - `complex_fraction_p` (e.g., atomics, microcoded, barriers, system instructions)
- Per-category translation parameters for persona `p`:
  - `avg_bytes_per_instr_category_p` (only required for x86-64; fixed 4 bytes for ARM64 and 2–4 bytes for RISC-V depending on compressed usage if modeled)
  - `avg_uops_per_instr_category_p` (RISC-V-style µops post-translation)
- Branch behavior for persona `p`:
  - `branch_mispredict_rate_p`
- Memory behavior (shared form across personas):
  - `l1d_hit_rate`
  - `l2_hit_rate`

Using these definitions, the simulator must:

1. Compute per-category instruction counts:
   - `instr_count_category_p = instr_count_p * category_fraction_p`.

2. Compute per-category µop counts using persona-specific translation parameters:
   - `uops_category_p = instr_count_category_p * avg_uops_per_instr_category_p`.

3. Sum across categories to get total µops for persona `p`:
   - `total_uops_p = Σ uops_category_p`.

These µops represent RISC-V-style operations fed into the shared backend.

---

## 7. Throughput and Runtime Computation

The simulator must compute, for each persona `p`:

- A front-end limited IPC: `ipc_frontend_p`.
- A backend limited IPC: `ipc_backend_p`.
- An effective IPC: `ipc_effective_p`.
- A runtime in seconds: `runtime_seconds_p`.

All of these values must emerge from:

- Persona-specific front-end and translation behavior.
- Shared backend resource limits and latencies.
- Workload-level instruction and µop mixes.

No persona-specific penalty multipliers may be applied outside these modeling steps.

### 7.1 Front-End Limited IPC

For each persona `p`, the simulator must estimate a front-end limited IPC `ipc_frontend_p` based on:

- Instruction fetch bandwidth:
  - `fetch_bytes_per_cycle = 16`.
- Instruction length characteristics:
  - `avg_bytes_per_instr_p` (fixed 4 bytes for ARM64, 2–4 bytes for RISC-V including compressed if modeled, persona- and category-specific averages for x86-64).
- Decode limits:
  - Max instructions decoded per cycle: 4.
  - Max µops emitted per cycle: 4.

A simplified approach:

1. Compute an approximate maximum instructions per cycle:
   - `max_instrs_by_fetch_p = fetch_bytes_per_cycle / avg_bytes_per_instr_p`.

2. Limit by decode and µop emission:
   - `max_instrs_by_decode_p = 4`.
   - `max_uops_by_frontend_p = 4` µops per cycle.

3. Use persona-specific translation parameters to determine:
   - Average µops per instruction: `avg_uops_per_instr_p`.

4. Compute an instruction-per-cycle limit:
   - `instrs_per_cycle_frontend_p = min(max_instrs_by_fetch_p, max_instrs_by_decode_p, max_uops_by_frontend_p / avg_uops_per_instr_p)`.

5. By definition, front-end limited IPC for persona `p`:
   - `ipc_frontend_p = instrs_per_cycle_frontend_p`.

The simulator may refine this model by using per-category averages, but the final `ipc_frontend_p` must be derived mechanically from fetch/decoding and translation rules, not from a raw persona tag.

### 7.2 Backend Limited IPC

For each persona `p`, the simulator must compute a backend limited IPC `ipc_backend_p` by:

1. Deriving µop mix from instruction mix and translation rules:
   - Determine fractions of µops that are:
     - Integer ALU µops.
     - Load µops.
     - Store µops.
     - FP/vector µops.
     - Branch µops.
     - Complex/system µops.

2. Applying shared backend resource limits:
   - Integer ALU capacity: 3 ALU µops per cycle.
   - Load unit capacity: 2 load µops per cycle.
   - Store unit capacity: 1 store µop per cycle.
   - FP/vector unit capacity: 2 FP/vec µops per cycle.
   - ROB capacity: 128 entries, bounding in-flight work.
   - Load/store queues: 64 entries each, bounding memory-level parallelism.

3. Incorporating memory behavior:
   - For each load µop:
     - Probability of L1 hit: `l1d_hit_rate`.
     - Probability of L2 hit given L1 miss: `l2_hit_rate`.
   - Effective latency computed from shared memory hierarchy:
     - L1D hit: 4-cycle effective load latency.
     - L2 hit: 4 + 10 cycles.
     - Memory hit: 4 + 120 cycles.
   - These latencies, combined with load queue size and instruction window, determine whether loads become a performance limiter.

4. Incorporating branch behavior:
   - Total branches: `instr_count_p * branch_fraction_p`.
   - Mispredictions: `branch_mispredicts_p = total_branches * branch_mispredict_rate_p`.
   - Penalty per misprediction: 12 cycles.
   - Accumulated stall cycles from mispredictions must be amortized over total instructions to reduce achievable IPC.

5. Solving for steady-state `ipc_backend_p`:
   - The backend limited IPC is determined by the slowest resource (ALUs, loads, stores, FP/vec, branch penalties, memory latency) given the µop mix and queue sizes.
   - A simplified throughput model might treat:
     - `ipc_backend_p` as `min(ipc_by_alus, ipc_by_loads, ipc_by_stores, ipc_by_fpvec, ipc_by_branch, ipc_by_memory)`.

The exact analytic method can be chosen based on model complexity, but it must be derived strictly from resource limits, latencies, and µop mix.

### 7.3 Effective IPC and Runtime

For each persona `p`:

- Effective IPC:
  - `ipc_effective_p = min(ipc_frontend_p, ipc_backend_p)`.

- Total cycles:
  - `cycles_p = instr_count_p / ipc_effective_p`.

- Runtime:
  - `runtime_seconds_p = cycles_p / (clock_ghz * 1e9)`.

The simulator must report all of these values per persona. Relative performance between personas is determined by comparing their `ipc_effective_p` and `runtime_seconds_p` values.

---

## 8. Simulation API Shape

This section defines a simple API shape for driving the simulation from an external client. Implementation details (e.g., how workloads are chosen) can be internal as long as they respect the architectural model.

### 8.1 Input

For a minimal API, persona is the only explicit input, and workloads are fixed internally per persona.

Request body:

```json
{
  "persona": "riscv"
}
```

Where:

- `persona` ∈ { `"riscv"`, `"x86_64"`, `"arm64"` }.

If needed, a later extension could allow an additional optional field for a workload profile identifier, but that is not required in this minimal spec.

### 8.2 Output

The simulation output should be a JSON object that includes:

- `persona`: the persona used for simulation.
- `soc_config`: the shared core configuration, including:
  - `issue_width`
  - `backend_dispatch_width`
  - `rob_entries`
  - `int_phys_regs`
  - `fp_vec_phys_regs`
  - `load_queue_entries`
  - `store_queue_entries`
  - `l1i_size_kb`
  - `l1d_size_kb`
  - `l2_size_kb`
  - `clock_ghz`
  - `pipeline_depth_estimate`
- `instr_count`: total architectural instructions for this persona.
- `frontend_metrics`:
  - `ipc_frontend`
- `backend_metrics`:
  - `ipc_backend`
- `ipc_effective`: effective IPC for this persona.
- `runtime_seconds`: runtime in seconds.

Optional additional fields may include:

- `total_uops`: total RISC-V-style µops executed.
- `branch_mispredicts`: number of branch mispredictions.
- `memory_stats`: derived statistics about L1/L2/memory accesses.

Example response structure (values illustrative only):

```json
{
  "persona": "x86_64",
  "soc_config": {
    "issue_width": 4,
    "backend_dispatch_width": 4,
    "rob_entries": 128,
    "int_phys_regs": 192,
    "fp_vec_phys_regs": 160,
    "load_queue_entries": 64,
    "store_queue_entries": 64,
    "l1i_size_kb": 32,
    "l1d_size_kb": 32,
    "l2_size_kb": 512,
    "clock_ghz": 3.0,
    "pipeline_depth_estimate": 18
  },
  "instr_count": 1000000000,
  "frontend_metrics": {
    "ipc_frontend": 2.9
  },
  "backend_metrics": {
    "ipc_backend": 2.7
  },
  "ipc_effective": 2.7,
  "runtime_seconds": 0.123
}
```

All numeric values must be derived from:

- The RISC-V-native backend configuration.
- Persona-specific front-end and translation parameters.
- Workload definition for the selected persona.

No arbitrary persona-specific penalty multipliers may be used in computing these outputs.
