# Tri-Mode SoC Architecture — References

This document lists the academic papers and methodological sources used to derive workload parameters and validate the simulation model.

---

## 1. Methodology

- NSF SBIR/STTR Research 101 for Engineers
  https://seedfund.nsf.gov/assets/files/applicants/research_101_for_engineers.pdf

---

## 2. Instruction Mix Characterization

- A Workload Characterization of the SPEC CPU2017 Benchmark Suite
  Limaye, A. and Adegbija, T.
  IEEE International Symposium on Performance Analysis of Systems and Software (ISPASS), 2018
  https://ieeexplore.ieee.org/document/8366949/

- Wait of a Decade: Did SPEC CPU 2017 Broaden the Performance Horizon?
  Song, S. et al.
  University of Texas at Austin, Laboratory for Computer Architecture
  https://lca.ece.utexas.edu/pubs/HPCA_SPEC17_ShuangSong.pdf

- Memory Centric Characterization and Analysis of SPEC CPU2017 Suite
  ICPE 2019 Proceedings
  https://arxiv.org/pdf/1910.00651

---

## 3. Cache Behavior and Memory Hierarchy

- Memory Hierarchy Characterization of SPEC CPU Benchmarks
  PLoS ONE 14(8), 2019
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6675054/

- Memory Hierarchy Lecture Notes
  Carnegie Mellon University, 15-740 Computer Architecture
  https://www.cs.cmu.edu/afs/cs/academic/class/15740-s18/www/lectures/03-04-memory-hierarchy.pdf

---

## 4. Branch Prediction

- Branch Prediction Is Not A Solved Problem: Measurements from the Championship
  Seznec, A. et al.
  arXiv:1906.08170, 2019
  https://arxiv.org/pdf/1906.08170

- Characterizing the Branch Misprediction Penalty
  Eyerman, S. and Smith, J.E.
  ISPASS 2006
  https://users.elis.ugent.be/~leeckhou/papers/ispass06-eyerman.pdf

---

## 5. Instruction Encoding and ISA Specifications

### RISC-V

- The RISC-V Instruction Set Manual Volume I: Unprivileged Architecture
  Waterman, A., Lee, Y., Patterson, D., and Asanović, K.
  RISC-V International
  https://riscv.org/specifications/ratified/

- RISC-V ISA Manual GitHub Repository
  RISC-V International
  https://github.com/riscv/riscv-isa-manual

- The Renewed Case for the Reduced Instruction Set Computer
  Patterson, D. and Waterman, A.
  arXiv:1607.02318, 2016
  https://arxiv.org/pdf/1607.02318

---

## 6. Micro-Op Translation and ISA Studies

- uops.info: Characterizing Latency, Throughput, and Port Usage of Instructions
  Abel, A. and Reineke, J.
  ASPLOS 2019
  https://arxiv.org/abs/1810.04610
  https://www.uops.info/

- Microarchitecture Documentation
  Agner Fog
  https://www.agner.org/optimize/microarchitecture.pdf

- Instruction Tables: Latencies, Throughputs and Micro-Operation Breakdowns
  Agner Fog
  https://www.agner.org/optimize/instruction_tables.pdf

### ISA Comparison Studies

- Power Struggles: Revisiting the RISC vs. CISC Debate
  Blem, E., Menon, J., and Sankaralingam, K.
  HPCA 2013
  https://research.cs.wisc.edu/vertical/papers/2013/hpca13-isa-power-struggles.pdf
  Key finding: ISA differences have implementation implications but modern microarchitecture techniques render them moot

---

## 7. SPEC CPU Benchmark Suite

- SPEC CPU 2017 Results
  Standard Performance Evaluation Corporation
  https://www.spec.org/cpu2017/results/

- SPEC CPU2006 Benchmark Descriptions
  ACM SIGARCH Computer Architecture News
  https://dl.acm.org/doi/abs/10.1145/1186736.1186737

---

## 8. Parameter Derivation Summary

The following table summarizes how each simulation parameter was derived:

| Parameter | Value | Primary Source |
|-----------|-------|----------------|
| ALU fraction | 43% | SPEC CPU2017 characterization (ISPASS 2018) |
| Load fraction | 22% | SPEC CPU2017 characterization (ISPASS 2018) |
| Store fraction | 10% | SPEC CPU2017 characterization (ISPASS 2018) |
| Branch fraction | 18% | SPEC CPU2017 characterization (ISPASS 2018) |
| FP/Vec fraction | 5% | SPEC CPU2017 characterization (ISPASS 2018) |
| Complex fraction | 2% | SPEC CPU2017 characterization (ISPASS 2018) |
| L1D hit rate | 92% | PLoS ONE memory hierarchy study (MPKI ~8) |
| L2 hit rate | 88% | PLoS ONE memory hierarchy study (MPKI3 ~6.6) |
| Branch mispredict rate | 2.5% | arXiv branch prediction study |
| Desktop64 avg instruction length | 4.0 bytes | Variable-length CISC encoding studies |
| Mobile64 avg instruction length | 4.0 bytes | Fixed 32-bit encoding |
| RISC-V avg instruction length | 3.6 bytes | RISC-V ISA Manual, arXiv:1607.02318 |
| Desktop64 avg µops/instruction | ~1.55 | Published empirical measurements (~1.6) |
| Mobile64 avg µops/instruction | ~1.06 | Published processor specifications |
| RISC-V avg µops/instruction | ~1.01 | Native RISC architecture, minimal translation |
| Tri-mode decode overhead (RISC-V) | 2% | Modeled persona detection in decode stage |
| Tri-mode decode overhead (Mobile64) | 3% | Modeled translation complexity |
| Tri-mode decode overhead (Desktop64) | 5% | Modeled variable-length decode + translation |
