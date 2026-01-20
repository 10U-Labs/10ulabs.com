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

## Usefulness

### Low Usefulness

#### High Complexity

7.3.2 Tagged unions: Defines type-safe unions where a tag tracks which member is currently valid. Borrowed from functional programming languages, but the SystemVerilog community never adopted them. Engineers stick with regular unions.

11.9 Tagged union expressions: Syntax for creating and accessing tagged union values with the `tagged` keyword. Requires 7.3.2 (tagged unions) to be useful. Rarely seen in practice since tagged unions themselves aren't widely used.

12.6.1 Pattern matching in case: Extends case statements with `matches` keyword to deconstruct tagged unions and structures. Elegant but rarely used since it depends on tagged unions, which the community never adopted.

12.6.2 Pattern matching in if: Extends if statements with pattern matching using the `&&&` operator. Allows conditional logic based on tagged union structure. Same adoption problem as other pattern matching features.

12.6.3 Pattern matching in conditionals: Extends ternary expressions (`?:`) with pattern matching predicates. The least commonly needed of the pattern matching features since ternaries are already compact.

18.17.7 Randsequence value passing: Randsequence is a way to generate random sequences of operations, like a grammar for test scenarios. It's a clever feature, but in practice almost nobody uses it. UVM sequences provide a more flexible and widely-adopted approach to the same problem.

#### Medium Complexity

6.6.4 Trireg nets: Models capacitors that hold their charge when disconnected. This matters for transistor-level simulation of things like DRAM cells or dynamic logic, but Verilator focuses on RTL simulation where you're working at a higher abstraction level. Most designs never use this.

9.4.5 Intra-assignment timing: Lets you write `a = #5 b` to mean "capture b's value now, but assign it to a after 5 time units." This is an obscure syntax that confuses more than it helps. Modern coding styles avoid it in favor of clearer alternatives.

10.3.4 Continuous assignment strengths: Specifying drive strength for continuous assignments. Matters for gate-level simulation but Verilator targets RTL where strength modeling is rarely needed.

10.6.1 assign/deassign: An old way to temporarily override a signal's value. The SystemVerilog standard itself marks this as deprecated and recommends using `force/release` instead. Not worth implementing something the industry is moving away from.

### Medium Usefulness

#### High Complexity

6.6.7 User-defined nettypes: Custom net types with user-defined resolution functions. Useful for mixed-signal simulation where you need custom wire behavior, but this is a niche use case for most digital designs.

6.6.8 Generic interconnect: Typeless nets declared as `interconnect` for abstraction-independent netlists. Useful for EDA tool flows but rarely written by hand in RTL.

#### Medium Complexity

6.5 Nets and variables: Mixed procedural and continuous assignments to different elements of the same aggregate. Occasionally needed but usually easy to work around by restructuring code.

8.26.6.1 Method name conflict resolution: Resolving conflicts when interface classes inherit multiple methods with the same name. Only matters for complex OOP hierarchies in verification code.

8.26.6.2 Parameter/type inheritance conflicts: Resolving name collisions when parameters or types are inherited from multiple interface classes. Same niche as 8.26.6.1.

8.26.6.3 Diamond relationship: Handling multiple inheritance diamond patterns in interface classes. Rare edge case in verification code.

#### Low Complexity

11.4.5 Equality operators: Case equality (`===`/`!==`) with class handles and interface class handles. Basic operators likely have partial support already; this covers edge cases.

11.4.6 Wildcard equality operators: `==?` and `!=?` operators that treat x/z in the right operand as wildcards. Simple operators but less commonly used than regular equality.

### High Usefulness

#### High Complexity

9.4.2.4 Sequence events: Lets you write code that waits for a complex pattern to occur: "pause here until you see A followed by B followed by C." This bridges the gap between assertions (which check properties) and procedural code (which takes actions). Useful for sophisticated testbenches that need to react to specific protocol sequences.

11.4.14.4 Streaming with dynamic sizing: Network protocols and bus transactions often have variable-length payloads—a packet header says "the next N bytes are data." This feature lets you pack and unpack such structures elegantly in one line. Without it, you're writing manual loops to serialize and deserialize data, which is verbose and bug-prone.

16.7 Sequences: The foundation of SystemVerilog Assertions (SVA). Sequences describe temporal patterns like "A followed by B within 5 cycles." Every professional verification environment uses assertions, making this a critical missing feature.

16.9 Sequence operations: Operators for combining sequences: repetition (`[*]`, `[->]`, `[=]`), `throughout`, `within`, `intersect`, `and`, `or`. These build on 16.7 to express complex temporal patterns concisely.

16.10 Local variables: Dynamically created variables within sequences/properties for tracking data across clock cycles. Essential for verifying pipelined designs where you need to compare input data against output appearing many cycles later.

16.17 Expect statement: Procedural blocking statement that waits for a property to succeed or fail. Bridges assertions and procedural code, letting testbenches pause until specific conditions are met.

18.7 Inline constraints: When generating random test data, you often need to add extra rules on the fly: "this time, make the packet size small" or "force an error condition." Inline constraints with `randomize() with {}` let you do this without modifying class definitions. This is used constantly in UVM testbenches to create directed-random tests that target specific scenarios.

#### Medium Complexity

15.5 Named events: Named events let different parts of a testbench signal each other: "I'm done with setup" or "the transaction completed." They're the basic building blocks for coordinating parallel processes in a simulation. UVM testbenches use events constantly to synchronize drivers, monitors, and scoreboards. Without them, you're stuck using clumsy workarounds like polling variables.

#### Low Complexity

7.2.2 Structure default values: Lets you set sensible defaults when defining a struct type, so you don't have to manually initialize every field every time you create one. This is a basic quality-of-life feature that most programmers expect from any language with structs. Without it, engineers must write boilerplate initialization code everywhere, which is tedious and error-prone.

20.14 Distribution functions: Functions like `$random`, `$dist_normal`, and `$dist_uniform` generate random numbers with different statistical distributions. These are workhorses in testbenches—you need them to create realistic test data, model timing variations, inject random delays, and stress-test designs. Almost every serious verification environment uses these.
