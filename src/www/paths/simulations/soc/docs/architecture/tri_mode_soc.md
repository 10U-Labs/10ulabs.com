# Tri-Mode SoC Architecture

A RISC-V core with hardware translation for conventional desktop and mainstream mobile 64-bit applications, targeting <1% overhead.

> **Disclaimer**: This is an independent research project by 10U Labs. This document describes a hypothetical architecture; the accompanying simulator does not implement, decode, or execute any instruction set. Performance estimates use publicly known architectural characteristics from academic research.

## Prototype Specifications

### Process and Package

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Process node | 130nm | Cost-effective ($15K via chipfoundry.io), sufficient for P4-class performance |
| Package size | 40x40mm BGA | Standard size, adequate for die + routing |
| Ball pitch | 0.8mm | 2,500 balls total, balances density vs manufacturability |
| Signal-to-ground ratio | 1:1 | Signal integrity, required for DDR4 speeds |
| Exit rows | 3 | Manufacturing constraint, limits routable signals to ~282 |

### Core Microarchitecture

| Parameter | Value | Comparable To |
|-----------|-------|---------------|
| Issue width | 3 | Pentium 4, Cortex-A57 |
| ROB entries | 128 | Pentium 4 (126 entries) |
| Pipeline depth | 14 stages | Conservative for 130nm |
| Clock speed | 1.5 GHz | Realistic for 130nm |
| L1 cache | 32 KB I + 32 KB D | Standard for class |
| L2 cache | 512 KB | Single-core adequate |
| Physical registers | 192 INT, 160 FP/Vec | Sufficient for OoO |

### Memory Interface

| Parameter | Value | Pins Required |
|-----------|-------|---------------|
| DDR generation | DDR4 | Modern, available |
| Channels | 2 (dual channel) | ~50 GB/s bandwidth |
| Pins per channel | 122 | Standard DDR4 |
| Total DDR pins | 244 | Fits in budget |

### I/O Budget

| Interface | Pins | Purpose |
|-----------|------|---------|
| DDR4 (2 channels) | 244 | Main memory |
| SPI flash | 6 | Boot ROM |
| JTAG | 5 | Debug |
| UART | 2 | Console |
| GPIO | 8 | LEDs, straps, I2C |
| Clocks/Reset/Misc | 15 | System support |
| **Total signals** | **280** | Under 282 limit |

## Translation Overhead Model

### Overhead Sources

The tri-mode core translates Desktop64 and Mobile64 instructions to RISC-V micro-ops. Overhead comes from:

1. **Flags emulation** - Desktop/Mobile condition flags don't exist in RISC-V
2. **Memory ordering** - Desktop64 TSO is stricter than RISC-V RVWMO
3. **Decode complexity** - Variable-length Desktop64 requires more decode logic
4. **Instruction expansion** - Some Desktop64 instructions become multiple RISC-V ops

### Hardware Optimizations

#### 1. Unified Decode Pipeline (0 extra stages)

Instead of serial translation stages, use parallel decode paths:
- RISC-V decoder lane
- Mobile64 decoder lane
- Desktop64 decoder lane

All emit to the same internal micro-op format. Instruction steering happens at fetch based on mode bits. No pipeline depth penalty.

#### 2. Hardware TSO Mode (0 fence overhead)

Modern mobile processors implement similar TSO modes. The load-store unit has a mode bit:
- When set, enforces TSO ordering in hardware
- Prevents load-store reordering without explicit fences
- Zero cycle overhead vs. RVWMO mode

Desktop64 code runs with TSO bit set. RISC-V/Mobile64 code runs with it cleared.

#### 3. Flags Speculation/Caching (~85-90% hit rate)

Instead of computing flags for every instruction:
- Dedicated flags predictor (256-512 entry table)
- Predicts flag values speculatively
- Only computes flags on predictor miss or when flags are consumed

Reduces flags overhead from 3 uops/flag-use to 0.15 uops/flag-use for Desktop64.

#### 4. Macro-op Fusion

Fuse common patterns during decode:
- `cmp + jcc` → single compare-and-branch micro-op
- `test + jcc` → single test-and-branch micro-op
- `load + op` → fused load-execute

Reduces instruction expansion ratio.

### Achieved Overhead

| Persona | Overhead | Primary Source |
|---------|----------|----------------|
| RISC-V | 0.00% | Native execution |
| Mobile64 | 0.31% | Minimal flags emulation (16% × 0.1 uops) |
| Desktop64 | 0.50% | Flags emulation (25% × 0.15 uops) |

#### Why RISC-V Has 0% IPC Overhead

RISC-V is the native ISA - no translation occurs. The tri-mode infrastructure (wider datapaths, mode detection logic) affects:
- **Die area** - larger structures, more transistors
- **Power consumption** - more switching activity
- **Maximum clock frequency** - longer critical paths

But these do not affect IPC when comparing equivalent microarchitectures at the same clock. The model compares IPC, not absolute performance. Real-world frequency impact from tri-mode complexity would be ~2-5% lower clock, not modeled here.

## Design Tradeoffs

### GPIO: 32 → 8 pins

**Lost:**
- Direct SD card attachment
- Direct LCD interface
- Multiple UARTs
- Raspberry Pi HAT compatibility

**Kept:**
- Boot capability
- Debug (JTAG + UART)
- Basic I2C for config
- Status LEDs

**Rationale:** Prototype validates core, not peripheral ecosystem. Rev 2 can add GPIO.

### Single-core vs Multi-core

**Choice:** Single core

**Rationale:**
- Simpler validation
- Package I/O budget tight with dual DDR4
- Multi-core adds coherency complexity
- Proves translation works before scaling

### DDR4 vs DDR5

**Choice:** DDR4

**Rationale:**
- DDR4 PHY available for 130nm (with level shifters)
- DDR5 requires newer process for PHY
- 50 GB/s bandwidth sufficient for single core
- Lower pin count than DDR5

### Process: 130nm vs 65nm vs 45nm

**Choice:** 130nm

**Rationale:**
- Cheapest shuttle cost (~$15K vs $50K+ for 65nm)
- Open PDK availability (SkyWater)
- Sufficient for P4-class performance
- Proves architecture before expensive respins

## Fabrication Path

### Option 1: chipfoundry.io (130nm)
- Cost: ~$15K
- Timeline: 8-12 weeks
- Risk: Low

### Option 2: Efabless/SkyWater MPW (130nm)
- Cost: Free (Google-sponsored)
- Timeline: 16-24 weeks (shuttle schedule)
- Risk: Schedule uncertainty

### Option 3: MOSIS (65nm)
- Cost: $50K-$100K
- Timeline: 12-16 weeks
- Risk: Medium (higher cost)

## Performance Expectations

### Absolute Performance

At 1.5 GHz with IPC ~0.4-0.6 (backend limited by memory):
- ~600-900 MIPS effective
- Comparable to early 2000s desktop processors

### Relative Performance (vs native)

| Workload | Desktop64 | Mobile64 | RISC-V |
|----------|-----------|----------|--------|
| Integer | 99.5% | 99.7% | 100% |
| FP | 99.3% | 99.6% | 100% |
| Memory-bound | 99.8% | 99.9% | 100% |

Memory-bound workloads see less overhead because translation overhead is hidden by memory latency.

## References

### Flags Emulation
- BINSEC TACAS 2015: Desktop64 flags liveness analysis (25% live rate)
- Mobile64 explicit flag-setting: CMP/SUBS patterns (~16% of instructions)

### Hardware TSO
- Mobile processor TSO modes for compatibility layers
- Desktop64 native TSO implementation

### Macro-op Fusion
- Modern desktop processors (2008+): cmp+jcc fusion
- Agner Fog microarchitecture documentation

### Process Technology
- SkyWater 130nm open PDK
- chipfoundry.io shuttle pricing
- MOSIS educational pricing
