# Tri-Mode SoC Architecture — References

This document lists the academic papers, technical reports, and official specifications used to derive the workload parameters and validate the simulation model.

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
  https://tosiron.com/papers/2018/SPEC2017_ISPASS18.pdf

- Wait of a Decade: Did SPEC CPU 2017 Broaden the Performance Horizon?
  Song, S. et al.
  University of Texas at Austin, Laboratory for Computer Architecture
  https://lca.ece.utexas.edu/pubs/HPCA_SPEC17_ShuangSong.pdf

- Memory Centric Characterization and Analysis of SPEC CPU2017 Suite
  ICPE 2019 Proceedings
  https://arxiv.org/pdf/1910.00651
  https://research.spec.org/icpe_proceedings/2019/proceedings/p285.pdf

- Performance Characterization of SPEC CPU2006 Integer Benchmarks
  Northeastern University NUCAR Group
  https://ece.northeastern.edu/groups/nucar/publications/SWC06.pdf

---

## 3. Cache Behavior and Memory Hierarchy

- Memory Hierarchy Characterization of SPEC CPU2006 and SPEC CPU2017 on the Intel Xeon Skylake-SP
  Navarro-Torres, A. et al.
  PLoS ONE 14(8), 2019
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6675054/

- Memory Hierarchy Lecture Notes
  Carnegie Mellon University, 15-740 Computer Architecture
  https://www.cs.cmu.edu/afs/cs/academic/class/15740-s18/www/lectures/03-04-memory-hierarchy.pdf

- Memory Hierarchy Lecture Notes
  Simon Fraser University, CMPT 450/750 Computer Architecture
  https://www.cs.sfu.ca/~ashriram/Courses/CS7ARCH/assets/lectures/04_Memory_Hierarchy.pdf

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

- Demystifying Intel Branch Predictors
  Milenkovic, A. and Milenkovic, M.
  University of Alabama in Huntsville
  Workshop on Duplicating, Deconstructing, and Debunking (WDDD), 2002
  https://alexmilenkovich.github.io/publications/files/milenkovic_WDDD02.pdf

- Branch Predictor: How Many "Ifs" Are Too Many?
  Cloudflare Engineering Blog (includes x86 and Apple M1 benchmarks)
  https://blog.cloudflare.com/branch-predictor/

- Intel 64 and IA-32 Architectures Optimization Reference Manual
  Intel Corporation
  https://www.intel.com/content/www/us/en/content-details/671488/
  https://cdrdv2-public.intel.com/671488/248966-046A-software-optimization-manual.pdf

---

## 5. Instruction Encoding and ISA Specifications

### x86-64

- Intel 64 and IA-32 Architectures Software Developer's Manual
  Intel Corporation
  https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html

- x86 Machine Code Statistics
  Analysis of real-world x86 instruction length distribution
  https://www.strchr.com/x86_machine_code_statistics

- Analysis of x86 Instruction Set Usage for Windows 7 Applications
  IEEE Conference, 2010
  https://ieeexplore.ieee.org/document/5645851/

- X86-64 Instruction Encoding
  OSDev Wiki
  https://wiki.osdev.org/X86-64_Instruction_Encoding

### ARM64 (AArch64)

- Arm Architecture Reference Manual for A-profile Architecture (DDI0487)
  Arm Limited
  https://developer.arm.com/documentation/ddi0487/latest

- A64 Instruction Set Architecture Guide
  Arm Limited
  https://developer.arm.com/documentation/102374/latest/

- Arm A-profile A64 Instruction Set Architecture (DDI0602)
  Arm Limited
  https://developer.arm.com/documentation/ddi0602/latest/

### RISC-V

- The RISC-V Instruction Set Manual Volume I: Unprivileged Architecture
  Waterman, A., Lee, Y., Patterson, D., and Asanović, K.
  RISC-V International
  https://riscv.org/specifications/ratified/
  https://riscv.github.io/riscv-isa-manual/snapshot/unprivileged/

- RISC-V ISA Manual GitHub Repository
  RISC-V International
  https://github.com/riscv/riscv-isa-manual

- An Empirical Comparison of the RISC-V and AArch64 Instruction Sets
  ACM SIGARCH, 2023
  https://dl.acm.org/doi/fullHtml/10.1145/3624062.3624233

- The Renewed Case for the Reduced Instruction Set Computer: Avoiding ISA Bloat with Macro-Op Fusion for RISC-V
  Patterson, D. and Waterman, A.
  arXiv:1607.02318, 2016
  https://arxiv.org/pdf/1607.02318

---

## 6. Micro-Op Translation and Decoder Characteristics

### ARM Cortex Microarchitecture

- ARM's Cortex A72: aarch64 for the Masses
  Chips and Cheese, 2023
  https://chipsandcheese.com/p/arms-cortex-a72-aarch64-for-the-masses
  Key finding: ARM quotes 1.08 micro-ops per instruction ratio on average

- Cortex-A76 Microarchitecture
  WikiChip
  https://en.wikichip.org/wiki/arm_holdings/microarchitectures/cortex-a76
  Key finding: 6% more MOPs than instructions (~1.06 avg)

### x86 Micro-Op Characterization

- uops.info: Characterizing Latency, Throughput, and Port Usage of Instructions on Intel Microarchitectures
  Abel, A. and Reineke, J.
  ASPLOS 2019
  https://arxiv.org/abs/1810.04610
  https://www.uops.info/

- The Microarchitecture of Intel, AMD, and VIA CPUs
  Agner Fog
  https://www.agner.org/optimize/microarchitecture.pdf

- Instruction Tables: Lists of Instruction Latencies, Throughputs and Micro-Operation Breakdowns
  Agner Fog
  https://www.agner.org/optimize/instruction_tables.pdf

- Intel Community Discussion: Average Number of µops per Instruction
  Reported ratio: ~1.6 uops_retired/instruction_retired
  https://community.intel.com/t5/Software-Tuning-Performance/Average-number-of-uops-per-instruction/td-p/958919

### ISA Comparison Studies

- Power Struggles: Revisiting the RISC vs. CISC Debate on Contemporary ARM and x86 Architectures
  Blem, E., Menon, J., and Sankaralingam, K.
  HPCA 2013
  https://research.cs.wisc.edu/vertical/papers/2013/hpca13-isa-power-struggles.pdf
  Key finding: ISA differences have implementation implications but modern microarchitecture techniques render them moot

### x86 Instruction and Addressing Mode Statistics

- x86 Instruction Frequency Analysis
  University of Alaska Fairbanks, CS 641 Lecture
  https://www.cs.uaf.edu/2011/spring/cs641/lecture/01_25_instruction_frequency.html
  Key findings: 42.4% MOV, 48.1% memory accesses, only 1.2% scaled displacement

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

The following table summarizes how each simulation parameter was derived from the references above:

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
| Branch mispredict rate | 2.5% | arXiv branch prediction study, Intel optimization manual |
| x86-64 avg instruction length | 4.0 bytes | strchr.com x86 statistics, Intel SDM |
| ARM64 avg instruction length | 4.0 bytes | ARM Architecture Reference Manual (DDI0487) |
| RISC-V avg instruction length | 3.6 bytes | RISC-V ISA Manual, arXiv:1607.02318 |
| x86 avg µops/instruction | ~1.55 | Intel Community (~1.6), Agner Fog tables |
| ARM64 avg µops/instruction | ~1.06 | Cortex A72 (1.08), Cortex A76 (1.06) |
| RISC-V avg µops/instruction | ~1.01 | Native RISC architecture, minimal translation |
| x86 complex addressing usage | 1.2% | CS 641 instruction frequency analysis |
| Tri-mode decode overhead (RISC-V) | 2% | Modeled persona detection in decode stage |
| Tri-mode decode overhead (ARM64) | 3% | Modeled translation complexity |
| Tri-mode decode overhead (x86) | 5% | Modeled variable-length decode + translation |
