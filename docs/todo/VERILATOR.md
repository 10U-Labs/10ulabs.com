# Verilator Unsupported SystemVerilog Features (IEEE 1800-2023)

| Section | Feature | Complexity | Usefulness |
|---------|---------|------------|------------|
| 6.5 | Nets and variables | Medium | Medium |
| 6.6.4 | Trireg net | Medium | Low |
| 6.6.7 | User-defined nettypes | High | Medium |
| 6.6.8 | Generic interconnect | High | Medium |
| 7.2.2 | Assigning to structures | Low | High |
| 7.3.2 | Tagged unions | High | Low |
| 8.26.6.1 | Method name conflict resolution | Medium | Medium |
| 8.26.6.2 | Parameter/type inheritance conflicts | Medium | Medium |
| 8.26.6.3 | Diamond relationship | Medium | Medium |
| 9.4.2.4 | Sequence events | High | High |
| 9.4.5 | Intra-assignment timing controls | Medium | Low |
| 10.3.4 | Continuous assignment strengths | Medium | Low |
| 10.6.1 | assign/deassign statements | Medium | Low |
| 11.4.5 | Equality operators | Low | Medium |
| 11.4.6 | Wildcard equality operators | Low | Medium |
| 11.4.14.4 | Streaming dynamically sized data | High | High |
| 11.9 | Tagged union expressions | High | Low |
| 12.6.1 | Pattern matching in case | High | Low |
| 12.6.2 | Pattern matching in if | High | Low |
| 12.6.3 | Pattern matching in conditionals | High | Low |
| 15.5 | Named events | Medium | High |
| 16.7 | Sequences | High | High |
| 16.9 | Sequence operations | High | High |
| 16.10 | Local variables | High | High |
| 16.17 | Expect statement | High | High |
| 18.7 | Inline constraints (randomize with) | High | High |
| 18.17.7 | Randsequence value passing | High | Low |
| 20.14 | Probabilistic distribution functions | Low | High |

## ROI

### Low

#### 6.6.4 Trireg nets (Medium Complexity/Low Usefulness)
Models capacitors that hold their charge when disconnected. This matters for transistor-level simulation of things like DRAM cells or dynamic logic, but Verilator focuses on RTL simulation where you're working at a higher abstraction level. Most designs never use this.

#### 7.3.2/11.9/12.6.* Tagged unions and pattern matching (High Complexity/Low Usefulness)
These are elegant features borrowed from functional programming languages like ML and Haskell. They let you create type-safe unions and deconstruct them cleanly. However, the SystemVerilog community never really adopted them—you'll rarely see these in actual verification code. Engineers stick with regular unions and if/case statements.

#### 9.4.5 Intra-assignment timing (Medium Complexity/Low Usefulness)
Lets you write `a = #5 b` to mean "capture b's value now, but assign it to a after 5 time units." This is an obscure syntax that confuses more than it helps. Modern coding styles avoid it in favor of clearer alternatives.

#### 10.6.1 assign/deassign (Medium Complexity/Low Usefulness)
An old way to temporarily override a signal's value. The SystemVerilog standard itself marks this as deprecated and recommends using `force/release` instead. Not worth implementing something the industry is moving away from.

#### 18.17.7 Randsequence value passing (High Complexity/Low Usefulness)
Randsequence is a way to generate random sequences of operations, like a grammar for test scenarios. It's a clever feature, but in practice almost nobody uses it. UVM sequences provide a more flexible and widely-adopted approach to the same problem.

### Medium

#### 9.4.2.4 Sequence events (High Complexity/High Usefulness)
Lets you write code that waits for a complex pattern to occur: "pause here until you see A followed by B followed by C." This bridges the gap between assertions (which check properties) and procedural code (which takes actions). Useful for sophisticated testbenches that need to react to specific protocol sequences.

#### 11.4.14.4 Streaming with dynamic sizing (High Complexity/High Usefulness)
Network protocols and bus transactions often have variable-length payloads—a packet header says "the next N bytes are data." This feature lets you pack and unpack such structures elegantly in one line. Without it, you're writing manual loops to serialize and deserialize data, which is verbose and bug-prone.

#### 16.7/16.9/16.10/16.17 SVA sequences and assertions (High Complexity/High Usefulness)
SystemVerilog Assertions (SVA) let you write rules like "after request goes high, acknowledge must follow within 5 cycles." The simulator then automatically checks these rules throughout the entire simulation, catching bugs that manual inspection would miss. This is arguably the most powerful verification feature in SystemVerilog—it's like having thousands of automated checkers watching your design. Every professional verification environment relies heavily on assertions.

#### 18.7 Inline constraints (High Complexity/High Usefulness)
When generating random test data, you often need to add extra rules on the fly: "this time, make the packet size small" or "force an error condition." Inline constraints with `randomize() with {}` let you do this without modifying class definitions. This is used constantly in UVM testbenches to create directed-random tests that target specific scenarios.

### High

#### 7.2.2 Structure default values (Low Complexity/High Usefulness)
Lets you set sensible defaults when defining a struct type, so you don't have to manually initialize every field every time you create one. This is a basic quality-of-life feature that most programmers expect from any language with structs. Without it, engineers must write boilerplate initialization code everywhere, which is tedious and error-prone.

#### 15.5 Named events (Medium Complexity/High Usefulness)
Named events let different parts of a testbench signal each other: "I'm done with setup" or "the transaction completed." They're the basic building blocks for coordinating parallel processes in a simulation. UVM testbenches use events constantly to synchronize drivers, monitors, and scoreboards. Without them, you're stuck using clumsy workarounds like polling variables.

#### 20.14 Distribution functions (Low Complexity/High Usefulness)
Functions like `$random`, `$dist_normal`, and `$dist_uniform` generate random numbers with different statistical distributions. These are workhorses in testbenches—you need them to create realistic test data, model timing variations, inject random delays, and stress-test designs. Almost every serious verification environment uses these.
