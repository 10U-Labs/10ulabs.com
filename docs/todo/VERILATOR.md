# Verilator Optimization Opportunities

## Table of Contents

| # | Issue | Status | PR | Impact |
|---|-------|--------|-----|--------|
| ~~1~~ | ~~Inline small CFuncs to reduce function call overhead~~ | ✅ Merged | ~~[#6815](https://github.com/verilator/verilator/pull/6815)~~ | ~~Reduces call overhead~~ |
| 2 | [Thread Pool Lock Contention](#2-thread-pool-lock-contention) | ⏳ Submitted | [#6761](https://github.com/verilator/verilator/pull/6761) | Faster verilate step (V3ThreadPool) |
| 3 | [Threading Self-Diagnostic System](#3-threading-self-diagnostic-system) | ⏳ Submitted | [#6762](https://github.com/verilator/verilator/pull/6762) | Runtime threading advice (VlThreadPool) |
| 4 | [Removing Race Conditions on AST Constructors](#4-removing-race-conditions-on-ast-constructors) | 📝 Todo | - | Prerequisite for parallelization |
| 4a | [`s_uniqueNum` → `std::atomic`](#pr-4a-make-s_uniquenum-atomic) | 📝 Todo | - | Trivial fix |
| 4b | [`s_editCntGbl` → `std::atomic`](#pr-4b-make-s_editcntgbl-atomic) | 📝 Todo | - | Low risk fix |
| 4c | [`s_cloneCntGbl` → `std::atomic`](#pr-4c-make-s_clonecntgbl-atomic) | 📝 Todo | - | Low risk fix |
| 4d | [`VNUserInUse` → atomic counters](#pr-4d-make-vnuserinuse-counters-atomic) | 📝 Todo | - | Low risk fix |
| 4e | [`AstTypeTable` mutex protection](#pr-4e-thread-safe-asttypetable) | 📝 Todo | - | Primary blocker |
| 4f | [Re-enable `V3FuncOpt` parallelization](#pr-4f-re-enable-v3funcopt-parallelization) | 📝 Todo | - | Depends on 4a-4e |
| 5 | [Module-Level Parallel Verilation](#5-module-level-parallel-verilation) | ⏸️ Paused | - | 2-4x faster compilation |
| 6 | [Parallelize V3FuncOpt](#6-parallelize-v3funcopt) | ❌ Rejected | [#6763](https://github.com/verilator/verilator/pull/6763) | Per-function parallelization |
| 7 | [Parallelize V3Const](#7-parallelize-v3const) | 📝 Todo | - | Per-module constant propagation |
| 8 | [Parallelize V3Dead](#8-parallelize-v3dead) | 📝 Todo | - | Per-module dead code elimination |
| 9 | [AST Object Pooling](#9-ast-object-pooling) | 📝 Todo | - | 10-20% memory reduction |

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

## 4. Removing Race Conditions on AST Constructors

**Files:** `src/V3Ast.cpp`, `src/V3Ast.h`, `src/V3AstNodes.cpp`, `src/V3AstNodeOther.h`, `src/V3AstNodeDType.h`

**Status:** 📝 Todo

**Problem:** AST node constructors have race conditions that prevent safe parallel instantiation. This is a prerequisite for broader parallelization efforts. PR [#6763](https://github.com/verilator/verilator/pull/6763) was rejected because "AstNode constructors are not thread safe as they may create entries in the shared Dtype table" (see [#6440](https://github.com/verilator/verilator/pull/6440)).

### Race Conditions Identified

#### 4.1 `AstTypeTable` - Type Cache (PRIMARY BLOCKER)

**Files:** `src/V3AstNodeOther.h:1699-1734`, `src/V3AstNodes.cpp:1366-1409`

The `AstTypeTable` class maintains caches of data types that are accessed without synchronization:

| Member | Type | Race Condition |
|--------|------|----------------|
| `m_basicps[_ENUM_MAX]` | `AstBasicDType*[]` | Check-then-act on array elements |
| `m_detailedMap` | `std::map<VBasicTypeKey, AstBasicDType*>` | Concurrent `operator[]` and `emplace()` |
| `m_constraintRefp` | `AstConstraintRefDType*` | Check-then-act on cached pointer |
| `m_emptyQueuep` | `AstEmptyQueueDType*` | Check-then-act on cached pointer |
| `m_queueIndexp` | `AstQueueDType*` | Check-then-act on cached pointer |
| `m_streamp` | `AstStreamDType*` | Check-then-act on cached pointer |
| `m_voidp` | `AstVoidDType*` | Check-then-act on cached pointer |

**Problematic code in `findBasicDType()` (V3AstNodes.cpp:1366-1374):**

```cpp
AstBasicDType* AstTypeTable::findBasicDType(FileLine* fl, VBasicDTypeKwd kwd) {
    if (!m_basicps[kwd]) {                    // Thread A reads null
        AstBasicDType basic{fl, kwd};
        m_basicps[kwd] = findCreateSameDType(basic);  // Thread B also read null, now overwrites
    }
    return m_basicps[kwd];
}
```

**Problematic code in `findCreateSameDType()` (V3AstNodes.cpp:1389-1399):**

```cpp
AstBasicDType* AstTypeTable::findCreateSameDType(AstBasicDType& node) {
    const VBasicTypeKey key{...};
    AstBasicDType*& entryr = m_detailedMap[key];  // std::map::operator[] is NOT thread-safe
    if (!entryr) {
        entryr = node.cloneTree(false);  // Creates new AstNode
        entryr->generic(true);
        addTypesp(entryr);               // Modifies AST tree structure
    }
    return entryr;
}
```

**Problematic code in `findInsertSameDType()` (V3AstNodes.cpp:1402-1409):**

```cpp
AstBasicDType* AstTypeTable::findInsertSameDType(AstBasicDType* nodep) {
    const VBasicTypeKey key{...};
    auto pair = m_detailedMap.emplace(key, nodep);  // std::map::emplace is NOT thread-safe
    if (pair.second) nodep->generic(true);
    return pair.first->second;
}
```

#### 4.2 `AstNodeDType::s_uniqueNum` - Static Counter

**Files:** `src/V3AstNodeDType.h:44,163`, `src/V3Ast.cpp:50`

```cpp
// V3AstNodeDType.h:44
static int s_uniqueNum;

// V3AstNodeDType.h:163
static int uniqueNumInc() { return ++s_uniqueNum; }  // Non-atomic increment!

// V3Ast.cpp:50
int AstNodeDType::s_uniqueNum = 0;
```

Every `AstBasicDType` and `AstNodeUOrStructDType` constructor calls `uniqueNumInc()`. Concurrent construction causes duplicate/skipped unique IDs due to non-atomic read-modify-write.

#### 4.3 `AstNode::s_editCntGbl` - Global Edit Counter

**Files:** `src/V3Ast.h:437,705-710`, `src/V3Ast.cpp:34`

```cpp
// V3Ast.h:437
static uint64_t s_editCntGbl;

// V3Ast.h:705-710
void editCountInc() {
    m_editCount = ++s_editCntGbl;  // Non-atomic increment!
}

// V3Ast.cpp:34
uint64_t AstNode::s_editCntGbl = 0;
```

Called on every AST mutation (node creation, linking, unlinking). Under concurrency, this causes lost updates and incorrect edit tracking.

#### 4.4 `AstNode::s_cloneCntGbl` - Clone Counter

**File:** `src/V3Ast.cpp:39`

```cpp
int AstNode::s_cloneCntGbl = 0;  // Used in cloneTree(), non-atomic
```

#### 4.5 `VNUserInUse` Counters

**File:** `src/V3Ast.cpp:40-48`

```cpp
uint32_t VNUser1InUse::s_userCntGbl = 0;  // Non-atomic
uint32_t VNUser2InUse::s_userCntGbl = 0;  // Non-atomic
uint32_t VNUser3InUse::s_userCntGbl = 0;  // Non-atomic
uint32_t VNUser4InUse::s_userCntGbl = 0;  // Non-atomic
bool VNUser1InUse::s_userBusy = false;    // Non-atomic
bool VNUser2InUse::s_userBusy = false;    // Non-atomic
bool VNUser3InUse::s_userBusy = false;    // Non-atomic
bool VNUser4InUse::s_userBusy = false;    // Non-atomic
```

### Required Atomic PRs

The following PRs fix the race conditions while maintaining full backwards compatibility (`std::atomic<T>` is a drop-in replacement for `T`).

**Dependency graph:**

```
4a ─────┬──────────────────────► 4e ──► 4f
4b ─────┤ (independent)
4c ─────┤
4d ─────┘
```

PRs 4a-4d can be submitted **in parallel** as independent PRs. PR 4e depends on 4a because `AstTypeTable::findCreateSameDType()` calls `cloneTree()`, which invokes `uniqueNumInc()` — the mutex only protects the map access, not the DType constructor's static counter.

| PR | Scope | Files | Risk | Depends On |
|----|-------|-------|------|------------|
| 4a | `s_uniqueNum` → `std::atomic<int>` | `V3AstNodeDType.h`, `V3Ast.cpp` | Trivial | - |
| 4b | `s_editCntGbl` → `std::atomic<uint64_t>` | `V3Ast.h`, `V3Ast.cpp` | Low | - |
| 4c | `s_cloneCntGbl` → `std::atomic<int>` | `V3Ast.cpp` | Low | - |
| 4d | `VNUserInUse` → atomic counters | `V3Ast.h`, `V3Ast.cpp` | Low | - |
| 4e | `AstTypeTable` mutex protection | `V3AstNodeOther.h`, `V3AstNodes.cpp` | Medium | 4a |
| 4f | Re-enable `V3FuncOpt` parallelization | `V3FuncOpt.cpp` | Medium | 4a-4e |

### PR 4a: Make `s_uniqueNum` Atomic

**Difficulty:** Trivial - single line change

```cpp
// V3AstNodeDType.h:44
- static int s_uniqueNum;
+ static std::atomic<int> s_uniqueNum;

// V3Ast.cpp:50
- int AstNodeDType::s_uniqueNum = 0;
+ std::atomic<int> AstNodeDType::s_uniqueNum{0};
```

No other changes needed - `++` on `std::atomic` is already atomic.

### PR 4b: Make `s_editCntGbl` Atomic

**Difficulty:** Low

```cpp
// V3Ast.h:437
- static uint64_t s_editCntGbl;
+ static std::atomic<uint64_t> s_editCntGbl;

// V3Ast.cpp:34
- uint64_t AstNode::s_editCntGbl = 0;
+ std::atomic<uint64_t> AstNode::s_editCntGbl{0};
```

### PR 4c: Make `s_cloneCntGbl` Atomic

**Difficulty:** Low

```cpp
// V3Ast.cpp:39
- int AstNode::s_cloneCntGbl = 0;
+ std::atomic<int> AstNode::s_cloneCntGbl{0};
```

### PR 4d: Make `VNUserInUse` Counters Atomic

**Difficulty:** Low

```cpp
// V3Ast.cpp:40-48
- uint32_t VNUser1InUse::s_userCntGbl = 0;
+ std::atomic<uint32_t> VNUser1InUse::s_userCntGbl{0};
// ... repeat for User2, User3, User4

- bool VNUser1InUse::s_userBusy = false;
+ std::atomic<bool> VNUser1InUse::s_userBusy{false};
// ... repeat for User2, User3, User4
```

### PR 4e: Thread-Safe `AstTypeTable`

**Difficulty:** Medium - requires mutex protection of multiple methods

```cpp
// V3AstNodeOther.h - add mutex member to AstTypeTable
class AstTypeTable final : public AstNode {
+   mutable V3Mutex m_mutex;
    AstBasicDType* m_basicps[VBasicDTypeKwd::_ENUM_MAX]{};
    DetailedMap m_detailedMap;
    // ...
};

// V3AstNodes.cpp - protect findBasicDType
AstBasicDType* AstTypeTable::findBasicDType(FileLine* fl, VBasicDTypeKwd kwd) {
+   const V3LockGuard lock{m_mutex};
    if (!m_basicps[kwd]) {
        AstBasicDType basic{fl, kwd};
        m_basicps[kwd] = findCreateSameDType(basic);
    }
    return m_basicps[kwd];
}

// V3AstNodes.cpp - protect findCreateSameDType
AstBasicDType* AstTypeTable::findCreateSameDType(AstBasicDType& node) {
+   // Note: caller already holds m_mutex from findBasicDType or findLogicBitDType
    const VBasicTypeKey key{...};
    AstBasicDType*& entryr = m_detailedMap[key];
    if (!entryr) {
        entryr = node.cloneTree(false);
        entryr->generic(true);
        addTypesp(entryr);
    }
    return entryr;
}

// V3AstNodes.cpp - protect findInsertSameDType
AstBasicDType* AstTypeTable::findInsertSameDType(AstBasicDType* nodep) {
+   const V3LockGuard lock{m_mutex};
    const VBasicTypeKey key{...};
    auto pair = m_detailedMap.emplace(key, nodep);
    if (pair.second) nodep->generic(true);
    return pair.first->second;
}

// Similar changes for findConstraintRefDType, findEmptyQueueDType,
// findQueueIndexDType, findStreamDType, findVoidDType
```

### PR 4f: Re-enable V3FuncOpt Parallelization

**Difficulty:** Medium - essentially resubmit [#6763](https://github.com/verilator/verilator/pull/6763) after PRs 4a-4e are merged

This PR depends on all previous PRs being merged first.

### Backwards Compatibility

All PRs maintain full API and ABI compatibility:
- `std::atomic<T>` is a drop-in replacement for `T` in terms of API
- Mutex protection is internal to `AstTypeTable` methods
- No public method signatures change
- No behavioral changes for single-threaded execution

**Impact:** Prerequisite for parallelization (Issues #5, #6, #7, #8)
**Difficulty:** Medium - requires careful ordering of PRs
**Risk:** Low - each PR is independently testable and mergeable

## 5. Module-Level Parallel Verilation

**Files:** `src/Verilator.cpp`, various V3*.cpp passes

**Status:** ⏸️ Paused (PR #6763 closed without merge; rethinking approach)

**Prerequisite:** [Issue #4](#4-removing-race-conditions-on-ast-constructors) must be completed first.

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

## 6. Parallelize V3FuncOpt

**File:** `src/V3FuncOpt.cpp`

**Status:** ❌ Rejected - [PR #6763](https://github.com/verilator/verilator/pull/6763) was not merged

**Proposed solution:** Apply per-function parallelization using `V3ThreadScope`. Each `AstCFunc` is processed independently in parallel.

**Changes proposed:**
- Add `V3ThreadScope` to `funcOptAll()` to parallelize function processing
- Convert `FuncOptStats` to use `std::atomic<uint64_t>` for thread-safe updates
- Add `VL_MT_SAFE` annotation to `FuncOptVisitor::apply()`

**Note:** This approach was not accepted by maintainers. Future parallelization efforts may require different strategies.

## 7. Parallelize V3Const

**File:** `src/V3Const.cpp`

**Status:** 📝 Todo

**Prerequisite:** [Issue #4](#4-removing-race-conditions-on-ast-constructors) must be completed first.

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

## 8. Parallelize V3Dead

**File:** `src/V3Dead.cpp`

**Status:** 📝 Todo

**Prerequisite:** [Issue #4](#4-removing-race-conditions-on-ast-constructors) must be completed first.

**Challenge:** Currently uses `V3PchAstNoMT.h` (MT-disabled). Dead code elimination may have cross-module reference counting dependencies that need careful analysis.

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

## References

- [Verilator GitHub Repository](https://github.com/verilator/verilator)
- [Antmicro: Improving Verilator's Hierarchical Mode (2025)](https://antmicro.com/blog/2025/05/improving-verilator-hierarchical-mode/)
- [Antmicro: Accelerating Model Generation (2023)](https://antmicro.com/blog/2023/09/accelerating-model-generation-in-verilator/)
