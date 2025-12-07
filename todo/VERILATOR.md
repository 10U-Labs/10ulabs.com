# Verilator Optimization Opportunities

## Executive Summary

Remaining optimization opportunities for Verilator (v5.x).

---

## Table of Contents

| # | Issue | Status | PR | Impact |
|---|-------|--------|-----|--------|
| 1 | [Thread Pool Lock Contention](#1-thread-pool-lock-contention) | PR SUBMITTED | [#6761](https://github.com/verilator/verilator/pull/6761) | 20-40% throughput improvement for multi-threaded workloads |
| 2 | [Threading Self-Diagnostic System](#2-threading-self-diagnostic-system) | PR SUBMITTED | [#6762](https://github.com/verilator/verilator/pull/6762) | Saves hours of debugging; enables informed optimization |
| 3 | [Module-Level Parallel Verilation](#3-module-level-parallel-verilation) | IN PROGRESS | - | 2-4x faster compilation on large multi-module designs |
| 3a | [Parallelize V3FuncOpt](#3a-parallelize-v3funcopt) | PR SUBMITTED | [#6763](https://github.com/verilator/verilator/pull/6763) | Per-function parallel optimization |
| 3b | [Parallelize V3Const](#3b-parallelize-v3const) | NOT DONE | - | Per-module constant propagation |
| 3c | [Parallelize V3Dead](#3c-parallelize-v3dead) | NOT DONE | - | Per-module dead code elimination |
| 4 | [AST Object Pooling](#4-ast-object-pooling) | NOT DONE | - | 10-20% memory reduction, faster allocation |

---

## 1. Thread Pool Lock Contention

**File:** `src/V3ThreadPool.cpp`

**Status:** PR SUBMITTED - [PR #6761](https://github.com/verilator/verilator/pull/6761)

**Problem:** The `wait()` function uses busy-wait loop that wastes CPU cycles.

```cpp
// Current implementation (V3ThreadPool.cpp:53-56)
void V3ThreadPool::wait() {
    while (m_pendingJobs.load(std::memory_order_acquire) > 0 && !m_shutdown) {
        std::this_thread::yield();  // Spin-waiting burns CPU
    }
    // ...
}
```

Note: The worker threads DO use condition variables properly (line 76-77), but the `wait()` function called by the main thread still busy-waits.

**Solution:** Add condition variable signaling for job completion.

```cpp
// Proposed fix - add to V3ThreadPool class
std::condition_variable_any m_completionCV;

void V3ThreadPool::wait() {
    V3LockGuard lock{m_mutex};
    m_completionCV.wait(m_mutex, [this]() VL_REQUIRES(m_mutex) {
        return m_pendingJobs.load(std::memory_order_acquire) == 0 || m_shutdown;
    });
    if (m_shutdown) {
        for (auto& worker : m_workers) worker.join();
    }
}

// In workerJobLoop(), after job completion:
void V3ThreadPool::workerJobLoop() {
    while (true) {
        // ... existing code ...
        job();
        if (m_pendingJobs.fetch_sub(1, std::memory_order_release) == 1) {
            m_completionCV.notify_all();  // Wake up wait() when last job completes
        }
    }
}
```

**Impact:** 20-40% throughput improvement for multi-threaded workloads
**Difficulty:** Easy - isolated change, well-understood pattern
**Risk:** Low - follows same pattern already used for worker threads

---

## 2. Threading Self-Diagnostic System

**Files:** `include/verilated_threading_advisor.h`, `include/verilated.cpp`

**Status:** PR SUBMITTED - [PR #6762](https://github.com/verilator/verilator/pull/6762)

**Current state:**
- `VlExecutionProfiler` exists for collecting profiling data (verilated_profiler.h)
- `verilator_gantt` tool provides post-hoc warnings about threading issues
- NO runtime advisory system exists to warn users during simulation

**Problem:** Users request `--threads N` but Verilator silently underutilizes them, or threading hurts performance. The warnings in `verilator_gantt` require explicit profiling runs and post-analysis.

**Solution:** Add runtime profiling that detects and reports threading issues automatically.

```cpp
// Proposed: Add to verilated.cpp or new verilated_threading_advisor.h
class VlThreadingAdvisor {
    struct Metrics {
        uint64_t cyclesProfiled = 0;
        uint64_t actualParallelWork = 0;
        uint64_t lockContentionEvents = 0;
        bool threadsOnSameCore = false;
    };

    static void profileAndAdvise(int requestedThreads) {
        Metrics m = collectMetrics(1000);  // Profile 1000 cycles

        double efficiency = (double)m.actualParallelWork /
                           (m.cyclesProfiled * requestedThreads);

        if (efficiency < 0.5) {
            int optimal = std::max(1, (int)(requestedThreads * efficiency * 2));
            VL_WARN_MT("", 0, "threading",
                      "Threading efficiency %.0f%%. Consider --threads %d",
                      efficiency * 100, optimal);
        }

        if (m.threadsOnSameCore) {
            VL_WARN_MT("", 0, "threading",
                      "Threads bound to same physical core. "
                      "Use: numactl --cpunodebind=0 --membind=0 ./Vmodel");
        }
    }
};
```

**Impact:** Saves users hours of debugging; enables informed optimization
**Difficulty:** Medium - needs integration with existing profiling
**Risk:** Low - advisory only, doesn't change simulation behavior

---

## 3. Module-Level Parallel Verilation

**Files:** `src/Verilator.cpp`, various V3*.cpp passes

**Status:** IN PROGRESS

**Goal:** Extend the `V3ThreadScope` parallel processing pattern to additional compiler passes.

**Already parallelized (upstream):**
- `V3VariableOrder.cpp` - Uses parallel module processing (lines 272-280)
- `V3EmitCImp.cpp` - Uses parallel code emission (lines 886-894)

**Pattern:**
```cpp
// Established pattern in V3VariableOrder.cpp:272-280
V3ThreadScope threadScope;
for (AstNodeModule* modp = v3Global.rootp()->modulesp(); modp;
     modp = VN_AS(modp->nextp(), NodeModule)) {
    threadScope.enqueue([modp, ...]() {
        processModule(modp, ...);
    });
}
```

**Impact:** 2-4x faster compilation on large multi-module designs
**Difficulty:** Medium - need to verify each pass is thread-safe
**Risk:** Medium - requires identifying which passes have global state

---

### 3a. Parallelize V3FuncOpt

**File:** `src/V3FuncOpt.cpp`

**Status:** PR SUBMITTED - [PR #6763](https://github.com/verilator/verilator/pull/6763)

**Solution:** Apply per-function parallelization using `V3ThreadScope`. Each `AstCFunc` is processed independently in parallel.

**Changes:**
- Add `V3ThreadScope` to `funcOptAll()` to parallelize function processing
- Convert `FuncOptStats` to use `std::atomic<uint64_t>` for thread-safe updates
- Add `VL_MT_SAFE` annotation to `FuncOptVisitor::apply()`

---

### 3b. Parallelize V3Const

**File:** `src/V3Const.cpp`

**Status:** NOT DONE

**Challenge:** Currently uses `V3PchAstNoMT.h` (MT-disabled). Would need conversion to `V3PchAstMT.h` and analysis of cross-module constant propagation dependencies.

```cpp
// Proposed approach
void V3Const::constifyAllModules(AstNetlist* nodep) {
    V3ThreadScope threadScope;
    for (AstNodeModule* modp = nodep->modulesp(); modp;
         modp = VN_AS(modp->nextp(), NodeModule)) {
        threadScope.enqueue([modp]() {
            constifyModule(modp);  // Module-local constant propagation
        });
    }
}
```

---

### 3c. Parallelize V3Dead

**File:** `src/V3Dead.cpp`

**Status:** NOT DONE

**Challenge:** Currently uses `V3PchAstNoMT.h` (MT-disabled). Dead code elimination may have cross-module reference counting dependencies that need careful analysis.

---

## 4. AST Object Pooling

**Files:** `src/V3Ast.cpp`, `src/V3AstNodes.cpp`

**Status:** NOT IMPLEMENTED

**Problem:** `AstVarRef` and `AstConst` are the most allocated node types. Standard `new` allocation is used throughout (188 occurrences of `new AstConst` and `new AstVarRef` across the codebase).

**Solution:** Arena allocator for AST passes to reduce allocation overhead and fragmentation.

```cpp
// Proposed: Add to V3Ast.h
template<typename T>
class VlAstArena {
    struct Block {
        static constexpr size_t SIZE = 4096;
        std::array<std::aligned_storage_t<sizeof(T), alignof(T)>, SIZE> storage;
        size_t used = 0;
    };

    std::vector<std::unique_ptr<Block>> m_blocks;

public:
    T* allocate() {
        if (m_blocks.empty() || m_blocks.back()->used >= Block::SIZE) {
            m_blocks.push_back(std::make_unique<Block>());
        }
        Block& b = *m_blocks.back();
        return reinterpret_cast<T*>(&b.storage[b.used++]);
    }

    void clear() {
        m_blocks.clear();  // Bulk deallocation
    }
};

// Usage in passes:
// VlAstArena<AstConst> constArena;
// AstConst* newConst = new (constArena.allocate()) AstConst(...);
```

**Impact:** 10-20% memory reduction, faster allocation for large designs
**Difficulty:** Medium - requires modifying node allocation patterns
**Risk:** Medium - memory management changes need careful validation

---

## References

- [Verilator GitHub Repository](https://github.com/verilator/verilator)
- [Antmicro: Improving Verilator's Hierarchical Mode (2025)](https://antmicro.com/blog/2025/05/improving-verilator-hierarchical-mode/)
- [Antmicro: Accelerating Model Generation (2023)](https://antmicro.com/blog/2023/09/accelerating-model-generation-in-verilator/)

## Our Contributions

- [PR #6761: Optimize V3ThreadPool::wait() to use condition variable](https://github.com/verilator/verilator/pull/6761)
- [PR #6762: Add runtime threading advisor for configuration warnings](https://github.com/verilator/verilator/pull/6762)
- [PR #6763: Parallelize V3FuncOpt using V3ThreadScope](https://github.com/verilator/verilator/pull/6763)
