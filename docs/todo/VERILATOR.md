# Verilator Unsupported SystemVerilog Features (IEEE 1800-2023)

| Section | Feature | Description | Complexity | Usefulness |
|---------|---------|-------------|------------|------------|
| 6.5 | Nets and variables | Mixed procedural and continuous assignments to different elements of the same aggregate (struct/array). Each bit is an independent element that can be driven by different assignment types. | Medium | Medium |
| 6.6.4 | Trireg net | Charge storage nets that retain their last driven value when all drivers are high-impedance. Supports capacitive state with small/medium/large strength levels. | Medium | Low |
| 6.6.7 | User-defined nettypes | Custom net types with user-defined data types and resolution functions. Allows defining atomic nets with custom resolution behavior using SystemVerilog functions. | High | Medium |
| 6.6.8 | Generic interconnect | Typeless/generic nets declared as `interconnect` for abstraction-independent netlists. Type is inferred from connected ports. Cannot be used in procedural contexts. | High | Medium |
| 7.2.2 | Assigning to structures | Default member values in structure type definitions using initial assignments. Members can have individual default values that are overridden by explicit initialization. | Low | High |
| 7.3.2 | Tagged unions | Type-safe unions with automatic tag tracking. The tag and value can only be updated together consistently. Runtime type checking prevents misinterpretation of bits. | High | Low |
| 8.26.6.1 | Method name conflict resolution | Resolving conflicts when interface classes inherit multiple methods with the same name. A single implementation must satisfy all inherited prototypes. | Medium | Medium |
| 8.26.6.2 | Parameter/type inheritance conflicts | Resolving name collisions when parameters or types are inherited from multiple interface classes. Subclass must override conflicting declarations. | Medium | Medium |
| 8.26.6.3 | Diamond relationship | Handling multiple inheritance diamond patterns in interface classes where the same base is inherited through different paths. | Medium | Medium |
| 9.4.2.4 | Sequence events | Using SVA sequence instances in event expressions (`@sequence_name`) to control procedural execution based on sequence endpoint matches. | High | High |
| 9.4.5 | Intra-assignment timing controls | Delay/event controls within assignment statements that evaluate RHS before the delay but assign to LHS after. Includes repeat timing control. | Medium | Low |
| 10.3.4 | Continuous assignment strengths | Specifying drive strength (supply/strong/pull/weak/highz) for continuous assignments to scalar nets. Strength applies when driving 0 or 1. | Medium | Low |
| 10.6.1 | assign/deassign statements | Procedural continuous assignment that overrides all other procedural assignments until deassign. Used for modeling async clear/preset. (Deprecated) | Medium | Low |
| 11.4.5 | Equality operators | Case equality (`===`/`!==`) and logical equality (`==`/`!=`) operators, including behavior with class handles, chandles, and interface class handles. | Low | Medium |
| 11.4.6 | Wildcard equality operators | `==?` and `!=?` operators that treat x/z in the right operand as wildcards matching any bit value. Left operand x/z are not wildcards. | Low | Medium |
| 11.4.14.4 | Streaming dynamically sized data | Streaming operators with `with` expression for variable-size fields. Allows unpacking packets with dynamic array sizes specified inline. | High | High |
| 11.9 | Tagged union expressions | Creating tagged union values with `tagged` keyword and accessing members with dot notation. Runtime type checking ensures tag consistency. | High | Low |
| 12.6.1 | Pattern matching in case | Case statements with `matches` keyword for pattern matching on tagged unions and structures. Supports wildcards, constants, and filter expressions. | High | Low |
| 12.6.2 | Pattern matching in if | If statements with `matches` clauses using `&&&` operator for sequential pattern matching. Pattern identifiers scope to the true branch. | High | Low |
| 12.6.3 | Pattern matching in conditionals | Ternary expressions (`?:`) with pattern matching predicates using `&&&` operator. Pattern identifiers scope to the consequent expression. | High | Low |
| 15.5 | Named events | Event data type with `->` trigger, `->>` nonblocking trigger, `triggered` method, and `wait_order()` construct for event sequencing. | Medium | High |
| 16.7 | Sequences | SVA sequence declarations with concatenation (`##`), repetition, and composition operators. Foundation of concurrent assertions. | High | High |
| 16.9 | Sequence operations | Sequence operators: consecutive repetition (`[*]`), goto repetition (`[->`), nonconsecutive repetition (`[=]`), `throughout`, `within`, `intersect`, `and`, `or`. | High | High |
| 16.10 | Local variables | Dynamically created local variables in sequences/properties for pipelined transaction checking. Assigned at sequence match points. | High | High |
| 16.17 | Expect statement | Procedural blocking statement that waits for property success/failure. Blocks executing process until property evaluation completes. | High | High |
| 18.7 | Inline constraints (randomize with) | Adding constraints inline at randomize() call site. Supports local variable references and scope resolution with `local::` qualifier. | High | High |
| 18.17.7 | Randsequence value passing | Passing data to/from productions in randsequence. Productions can accept arguments (like tasks) and return values (like functions). | High | Low |
| 20.14 | Probabilistic distribution functions | `$random`, `$dist_uniform`, `$dist_normal`, `$dist_exponential`, `$dist_poisson`, `$dist_chi_square`, `$dist_t`, `$dist_erlang` functions. | Low | High |

## Complexity Legend

- **Low**: Straightforward implementation, mostly parsing and basic code generation changes
- **Medium**: Requires moderate architectural changes, new data structures, or simulation semantics
- **High**: Requires significant infrastructure (assertion engine, constraint solver, type system extensions)

## Usefulness Legend

- **Low**: Rarely used in practice, niche use cases, or deprecated features
- **Medium**: Useful for specific domains or occasionally needed in testbenches
- **High**: Commonly used in UVM testbenches, verification IP, or RTL design

## Implementation Priority Recommendations

### Best ROI (High Usefulness, Low/Medium Complexity)

**7.2.2 Structure default values** (Low/High)
Lets you set sensible defaults when defining a struct type, so you don't have to manually initialize every field every time you create one. This is a basic quality-of-life feature that most programmers expect from any language with structs. Without it, engineers must write boilerplate initialization code everywhere, which is tedious and error-prone.

**20.14 Distribution functions** (Low/High)
Functions like `$random`, `$dist_normal`, and `$dist_uniform` generate random numbers with different statistical distributions. These are workhorses in testbenches—you need them to create realistic test data, model timing variations, inject random delays, and stress-test designs. Almost every serious verification environment uses these.

**15.5 Named events** (Medium/High)
Named events let different parts of a testbench signal each other: "I'm done with setup" or "the transaction completed." They're the basic building blocks for coordinating parallel processes in a simulation. UVM testbenches use events constantly to synchronize drivers, monitors, and scoreboards. Without them, you're stuck using clumsy workarounds like polling variables.

### High Impact but Major Effort

**16.7/16.9/16.10/16.17 SVA sequences and assertions** (High/High)
SystemVerilog Assertions (SVA) let you write rules like "after request goes high, acknowledge must follow within 5 cycles." The simulator then automatically checks these rules throughout the entire simulation, catching bugs that manual inspection would miss. This is arguably the most powerful verification feature in SystemVerilog—it's like having thousands of automated checkers watching your design. Every professional verification environment relies heavily on assertions.

**18.7 Inline constraints** (High/High)
When generating random test data, you often need to add extra rules on the fly: "this time, make the packet size small" or "force an error condition." Inline constraints with `randomize() with {}` let you do this without modifying class definitions. This is used constantly in UVM testbenches to create directed-random tests that target specific scenarios.

**11.4.14.4 Streaming with dynamic sizing** (High/High)
Network protocols and bus transactions often have variable-length payloads—a packet header says "the next N bytes are data." This feature lets you pack and unpack such structures elegantly in one line. Without it, you're writing manual loops to serialize and deserialize data, which is verbose and bug-prone.

**9.4.2.4 Sequence events** (High/High)
Lets you write code that waits for a complex pattern to occur: "pause here until you see A followed by B followed by C." This bridges the gap between assertions (which check properties) and procedural code (which takes actions). Useful for sophisticated testbenches that need to react to specific protocol sequences.

### Lower Priority

**6.6.4 Trireg nets** (Medium/Low)
Models capacitors that hold their charge when disconnected. This matters for transistor-level simulation of things like DRAM cells or dynamic logic, but Verilator focuses on RTL simulation where you're working at a higher abstraction level. Most designs never use this.

**9.4.5 Intra-assignment timing** (Medium/Low)
Lets you write `a = #5 b` to mean "capture b's value now, but assign it to a after 5 time units." This is an obscure syntax that confuses more than it helps. Modern coding styles avoid it in favor of clearer alternatives.

**10.6.1 assign/deassign** (Medium/Low)
An old way to temporarily override a signal's value. The SystemVerilog standard itself marks this as deprecated and recommends using `force/release` instead. Not worth implementing something the industry is moving away from.

**7.3.2/11.9/12.6.* Tagged unions and pattern matching** (High/Low)
These are elegant features borrowed from functional programming languages like ML and Haskell. They let you create type-safe unions and deconstruct them cleanly. However, the SystemVerilog community never really adopted them—you'll rarely see these in actual verification code. Engineers stick with regular unions and if/case statements.

**18.17.7 Randsequence value passing** (High/Low)
Randsequence is a way to generate random sequences of operations, like a grammar for test scenarios. It's a clever feature, but in practice almost nobody uses it. UVM sequences provide a more flexible and widely-adopted approach to the same problem.
