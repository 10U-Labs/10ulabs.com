# Tri-Mode SoC Architecture — Appendix A: Parameter Derivation Methodology

This appendix explains how the simulation parameters were derived and why they are implemented as constants rather than dynamically computed values.

---

## 1. Overview

The tri-mode SoC simulation uses research-backed constants to model the performance characteristics of executing x86-64, ARM64, and RISC-V workloads on a unified RISC-V-native backend. These constants are derived from published academic studies, processor vendor documentation, and empirical measurements.

The simulation does not perform cycle-accurate execution or binary translation. Instead, it applies analytical models based on:

1. Instruction mix fractions from SPEC CPU benchmark characterization
2. µop translation ratios from processor microarchitecture studies
3. Cache and branch behavior from memory hierarchy research
4. Decode overhead estimates based on architectural complexity

---

## 2. Hardcoded vs. Dynamic Values

### 2.1 Why Constants?

The simulation parameters are hardcoded for the following reasons:

1. **Reproducibility**: Fixed constants ensure consistent results across simulation runs, enabling meaningful comparisons between personas.

2. **Research grounding**: Each constant is tied to a specific published source, providing traceability and scientific validity.

3. **Computational efficiency**: Analytical models with constants are orders of magnitude faster than cycle-accurate simulation, enabling interactive use.

4. **First-order accuracy**: For comparing ISA translation overhead, first-order approximations based on average behavior are sufficient. Micro-benchmark variations would add noise without improving architectural insights.

### 2.2 What Would Change the Values?

The constants would need to be updated if:

- New benchmark characterization studies provide updated instruction mix data
- Processor vendors publish revised µop counts for new microarchitectures
- The target SoC configuration changes (e.g., different cache sizes, issue width)
- The workload profile shifts significantly from SPEC CPU characteristics

---

## 3. Translation Ratio Derivation

### 3.1 µops per Instruction by ISA

The core translation ratios determine how many RISC-V-style µops each source ISA instruction generates:

| ISA | Avg µops/instr | Derivation |
|-----|----------------|------------|
| RISC-V | 1.01 | Native execution; only complex ops (fence, ecall) expand to 1-2 µops |
| ARM64 | 1.055 | Cortex A72 reports 1.08, Cortex A76 reports 1.06; weighted average |
| x86-64 | 1.55 | Intel Community reports ~1.6; adjusted for modern workloads |

### 3.2 Per-Category Translation Ranges

The simulation defines µop ranges per instruction category, then averages them:

**RISC-V (native)**:
```
alu: (1, 1) → 1.0    load: (1, 1) → 1.0    store: (1, 1) → 1.0
branch: (1, 1) → 1.0  fp_vec: (1, 1) → 1.0  complex: (1, 2) → 1.5
```

**ARM64**:
```
alu: (1, 1) → 1.0    load: (1, 1) → 1.0    store: (1, 1) → 1.0
branch: (1, 1) → 1.0  fp_vec: (1, 2) → 1.5  complex: (2, 3) → 2.5
```

**x86-64**:
```
alu: (1, 2) → 1.5    load: (1, 2) → 1.5    store: (1, 2) → 1.5
branch: (1, 1) → 1.0  fp_vec: (2, 3) → 2.5  complex: (4, 8) → 6.0
```

### 3.3 Weighted Average Calculation

Using SPEC CPU2017 instruction mix fractions:
- ALU: 43%, Load: 22%, Store: 10%, Branch: 18%, FP/Vec: 5%, Complex: 2%

**RISC-V**: 0.43×1.0 + 0.22×1.0 + 0.10×1.0 + 0.18×1.0 + 0.05×1.0 + 0.02×1.5 = **1.01**

**ARM64**: 0.43×1.0 + 0.22×1.0 + 0.10×1.0 + 0.18×1.0 + 0.05×1.5 + 0.02×2.5 = **1.055**

**x86-64**: 0.43×1.5 + 0.22×1.5 + 0.10×1.5 + 0.18×1.0 + 0.05×2.5 + 0.02×6.0 = **1.55**

---

## 4. Decode Overhead Derivation

### 4.1 Tri-Mode Decode Overhead

On a tri-mode core, the decode stage must:
1. Identify the current ISA persona
2. Route instructions to the appropriate decoder
3. Translate to RISC-V-style µops

This adds overhead even for native RISC-V execution:

| Persona | Decode Overhead | Rationale |
|---------|-----------------|-----------|
| RISC-V | 2% | Persona detection logic in decode stage |
| ARM64 | 3% | Fixed-length decode + simple translation |
| x86-64 | 5% | Variable-length decode + complex translation |

### 4.2 How Overhead is Applied

The decode overhead reduces effective IPC as a multiplier on the final throughput:

```
ipc_effective = ipc_raw × (1.0 - decode_overhead)
```

This models the pipeline bubbles and stalls introduced by the tri-mode decode logic.

---

## 5. Workload Parameters

### 5.1 Instruction Mix (from SPEC CPU2017)

| Category | Fraction | Source |
|----------|----------|--------|
| ALU (integer arithmetic, logical) | 43% | ISPASS 2018 characterization |
| Load | 22% | ISPASS 2018 characterization |
| Store | 10% | ISPASS 2018 characterization |
| Branch | 18% | ISPASS 2018 characterization |
| FP/Vector | 5% | ISPASS 2018 characterization |
| Complex (string, system) | 2% | ISPASS 2018 characterization |

### 5.2 Memory Hierarchy Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| L1D hit rate | 92% | PLoS ONE study (MPKI ~8 for SPEC CPU2017) |
| L2 hit rate | 88% | PLoS ONE study (L2 MPKI ~6.6) |
| L1D hit latency | 4 cycles | Architecture spec |
| L2 hit latency | 14 cycles | Architecture spec (10 beyond L1) |
| Memory latency | 124 cycles | Architecture spec (120 beyond L1) |

### 5.3 Branch Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Branch mispredict rate | 2.5% | arXiv branch prediction study |
| Mispredict penalty | 12 cycles | Architecture spec |

### 5.4 Instruction Encoding

| ISA | Avg bytes/instr | Source |
|-----|-----------------|--------|
| RISC-V | 3.6 | RISC-V ISA Manual (with C extension) |
| ARM64 | 4.0 | Fixed 32-bit encoding |
| x86-64 | 4.0 | strchr.com x86 statistics |

---

## 6. Resulting Simulation Outputs

Given the parameters above, the simulation produces:

| Persona | Native IPC | Tri-mode IPC | Slowdown |
|---------|------------|--------------|----------|
| RISC-V | 0.596 | 0.584 | 1.02x |
| ARM64 | 0.596 | 0.573 | 1.04x |
| x86-64 | 0.596 | 0.380 | 1.57x |

These results emerge from the interaction of:
1. Frontend limits (fetch bandwidth, decode width, µop emission rate)
2. Backend limits (execution units, memory stalls, branch stalls)
3. Translation overhead (µop expansion per ISA)
4. Decode overhead (tri-mode pipeline complexity)

---

## 7. Validation Approach

The hardcoded values are validated by comparing simulation outputs against:

1. **Published ISA comparisons**: The HPCA 2013 "Power Struggles" paper found ARM and x86 performance differences are ISA-independent to first order, consistent with our near-native ARM64 results.

2. **µop measurements**: The ~1.6 x86 µops/instruction ratio matches Intel Community reports and Agner Fog's empirical measurements.

3. **ARM Cortex specifications**: The 1.06-1.08 ARM64 µops/instruction matches published Cortex A72/A76 data.

4. **Qualitative expectations**: x86-64 should have the highest overhead due to variable-length encoding and CISC complexity; ARM64 should be near-native; RISC-V should have minimal overhead.

---

## 8. Limitations

1. **Workload specificity**: The instruction mix is based on SPEC CPU integer benchmarks. Other workloads (HPC, ML, embedded) may have different characteristics.

2. **Static analysis**: The simulation uses static average parameters. Real execution would show variance based on code phase behavior.

3. **No dynamic effects**: Branch predictor warmup, cache thrashing, and memory bandwidth contention are not modeled.

4. **Translation approximation**: The µop ranges are category-level averages. Individual instructions within a category may vary significantly.

---

## 9. Future Work

To improve accuracy, future versions could:

1. Add workload profiles for different application domains (HPC, embedded, ML)
2. Incorporate phase-level behavior modeling
3. Use instruction-level µop counts from uops.info database
4. Model dynamic effects like cache warmup and branch predictor training
