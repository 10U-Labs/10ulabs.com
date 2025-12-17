# Verilator Optimization Opportunities

## Executive Summary

Remaining optimization opportunities for Verilator (v5.x).

---

## Table of Contents

| # | Issue | Status | PR | Impact | Remarks |
|---|-------|--------|-----|--------|---------|
| 1 | [Function Inlining](#1-function-inlining) | ⏳ Submitted | [#6815](https://github.com/verilator/verilator/pull/6815) | Reduces call overhead | |
| 2 | [Thread Pool Lock Contention](#2-thread-pool-lock-contention) | ⏳ Submitted | [#6761](https://github.com/verilator/verilator/pull/6761) | Faster verilate step (V3ThreadPool) | |
| 3 | [Threading Self-Diagnostic System](#3-threading-self-diagnostic-system) | ⏳ Submitted | [#6762](https://github.com/verilator/verilator/pull/6762) | Runtime threading advice (VlThreadPool) | |
| 4 | [Removing Race Conditions on AST Constructors](#4-removing-race-conditions-on-ast-constructors) | 📝 Todo | - | Prerequisite for parallelization | |
| 5 | [Module-Level Parallel Verilation](#5-module-level-parallel-verilation) | ⏸️ Paused | - | 2-4x faster compilation | Rethinking approach after #6 rejection |
| 6 | [Parallelize V3FuncOpt](#6-parallelize-v3funcopt) | ❌ Rejected | [#6763](https://github.com/verilator/verilator/pull/6763) | Per-function parallelization | Maintainers preferred different strategy |
| 7 | [Parallelize V3Const](#7-parallelize-v3const) | 📝 Todo | - | Per-module constant propagation | Blocked on approach decision |
| 8 | [Parallelize V3Dead](#8-parallelize-v3dead) | 📝 Todo | - | Per-module dead code elimination | Blocked on approach decision |
| 9 | [AST Object Pooling](#9-ast-object-pooling) | 📝 Todo | - | 10-20% memory reduction | |

---

## 1. Function Inlining

**Files:** `src/V3InlineCFuncs.cpp` (new file)

**Status:** ⏳ Submitted - [PR #6815](https://github.com/verilator/verilator/pull/6815) (supersedes closed [#6765](https://github.com/verilator/verilator/pull/6765))

**Resolves:** [Issue #2367](https://github.com/verilator/verilator/issues/2367)

**Problem:** When `--output-split-cfuncs` places functions in separate compilation units, the C++ compiler cannot inline them, resulting in function call overhead for small functions.

**Solution:** Add `--inline-cfuncs` and `--inline-cfuncs-product` options to inline small CFunc calls directly into their callers at the Verilator level.

**Two thresholds:**
- `--inline-cfuncs <n>` (default 20): Always inline if function has ≤ n AST nodes
- `--inline-cfuncs-product <n>` (default 200): Also inline if size × call_count ≤ n

**Functions are inlined when they:**
- Meet size thresholds above
- Have no `$c()` statements
- Have void return type
- Are in the same scope as caller

**Implementation details:**
- Separate V3InlineCFuncs pass running after V3Reloop
- Local variables cloned with unique names (`__Vinline_<func>_<var>`)
- V3Stats tracking: `"Optimizations, Inlined CFuncs"`
- Automatically disabled when `--prof-cfuncs` or `--trace` is used

**Impact:** Reduces function call overhead from --output-split-cfuncs
**Difficulty:** Medium - required multiple iterations based on maintainer feedback
**Risk:** Low - opt-in feature with sensible defaults

---

## 2. Thread Pool Lock Contention

**File:** `src/V3ThreadPool.cpp`

**Status:** ⏳ Submitted - [PR #6761](https://github.com/verilator/verilator/pull/6761)

**Affects:** Compile-time parallelization (verilate step). V3ThreadPool is controlled by `--verilate-jobs N` (or `-j N`), not to be confused with VlThreadPool which handles runtime simulation threading (`--threads N`).

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

**Impact:** Reduces CPU waste during verilate step, especially at high thread counts (32+) where busy-wait contention is significant. Enables better resource sharing on build farms.
**Difficulty:** Easy - isolated change, well-understood pattern
**Risk:** Low - follows same pattern already used for worker threads

---

## 3. Threading Self-Diagnostic System

**Files:** `include/verilated_threading_advisor.h`, `include/verilated.cpp`

**Status:** ⏳ Submitted - [PR #6762](https://github.com/verilator/verilator/pull/6762)

**Affects:** Runtime simulation threading (VlThreadPool, controlled by `--threads N`). This is separate from compile-time parallelization (V3ThreadPool in Section 2).

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

## 4. Removing Race Conditions on AST Constructors

**Files:** `src/V3Ast.cpp`, `src/V3AstNodes.cpp`

**Status:** 📝 Todo

**Problem:** AST node constructors have race conditions that prevent safe parallel instantiation. This is a prerequisite for broader parallelization efforts.

**Impact:** Prerequisite for parallelization
**Difficulty:** Medium - requires careful analysis of shared state
**Risk:** Low - fixes existing thread-safety issues

---

## 5. Module-Level Parallel Verilation

**Files:** `src/Verilator.cpp`, various V3*.cpp passes

**Status:** ⏸️ Paused (PR #6763 closed without merge; rethinking approach)

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

## 6. Parallelize V3FuncOpt

**File:** `src/V3FuncOpt.cpp`

**Status:** ❌ Rejected - [PR #6763](https://github.com/verilator/verilator/pull/6763) was not merged

**Proposed solution:** Apply per-function parallelization using `V3ThreadScope`. Each `AstCFunc` is processed independently in parallel.

**Changes proposed:**
- Add `V3ThreadScope` to `funcOptAll()` to parallelize function processing
- Convert `FuncOptStats` to use `std::atomic<uint64_t>` for thread-safe updates
- Add `VL_MT_SAFE` annotation to `FuncOptVisitor::apply()`

**Note:** This approach was not accepted by maintainers. Future parallelization efforts may require different strategies.

---

## 7. Parallelize V3Const

**File:** `src/V3Const.cpp`

**Status:** 📝 Todo

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

## 8. Parallelize V3Dead

**File:** `src/V3Dead.cpp`

**Status:** 📝 Todo

**Challenge:** Currently uses `V3PchAstNoMT.h` (MT-disabled). Dead code elimination may have cross-module reference counting dependencies that need careful analysis.

---

## 9. AST Object Pooling

**Files:** `src/V3Ast.cpp`, `src/V3AstNodes.cpp`

**Status:** 📝 Todo

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

**Open PRs:**
- [PR #6761: Optimize V3ThreadPool::wait() to use condition variable](https://github.com/verilator/verilator/pull/6761)
- [PR #6762: Add runtime threading advisor for configuration warnings](https://github.com/verilator/verilator/pull/6762)
- [PR #6815: Inline small CFuncs to reduce function call overhead](https://github.com/verilator/verilator/pull/6815)

**Closed PRs (not merged):**
- [PR #6763: Parallelize V3FuncOpt using V3ThreadScope](https://github.com/verilator/verilator/pull/6763)
- [PR #6765: Inline small CFuncs (superseded by #6815)](https://github.com/verilator/verilator/pull/6765)
