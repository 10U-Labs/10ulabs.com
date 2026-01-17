# Verilator Unsupported SystemVerilog Features (IEEE 1800-2023)

| Section | Feature | Description | Complexity |
|---------|---------|-------------|------------|
| 6.5 | Nets and variables | Mixed procedural and continuous assignments to different elements of the same aggregate (struct/array). Each bit is an independent element that can be driven by different assignment types. | Medium |
| 6.6.4 | Trireg net | Charge storage nets that retain their last driven value when all drivers are high-impedance. Supports capacitive state with small/medium/large strength levels. | Medium |
| 6.6.7 | User-defined nettypes | Custom net types with user-defined data types and resolution functions. Allows defining atomic nets with custom resolution behavior using SystemVerilog functions. | High |
| 6.6.8 | Generic interconnect | Typeless/generic nets declared as `interconnect` for abstraction-independent netlists. Type is inferred from connected ports. Cannot be used in procedural contexts. | High |
| 7.2.2 | Assigning to structures | Default member values in structure type definitions using initial assignments. Members can have individual default values that are overridden by explicit initialization. | Low |
| 7.3.2 | Tagged unions | Type-safe unions with automatic tag tracking. The tag and value can only be updated together consistently. Runtime type checking prevents misinterpretation of bits. | High |
| 8.26.6.1 | Method name conflict resolution | Resolving conflicts when interface classes inherit multiple methods with the same name. A single implementation must satisfy all inherited prototypes. | Medium |
| 8.26.6.2 | Parameter/type inheritance conflicts | Resolving name collisions when parameters or types are inherited from multiple interface classes. Subclass must override conflicting declarations. | Medium |
| 8.26.6.3 | Diamond relationship | Handling multiple inheritance diamond patterns in interface classes where the same base is inherited through different paths. | Medium |
| 9.4.2.4 | Sequence events | Using SVA sequence instances in event expressions (`@sequence_name`) to control procedural execution based on sequence endpoint matches. | High |
| 9.4.5 | Intra-assignment timing controls | Delay/event controls within assignment statements that evaluate RHS before the delay but assign to LHS after. Includes repeat timing control. | Medium |
| 10.3.4 | Continuous assignment strengths | Specifying drive strength (supply/strong/pull/weak/highz) for continuous assignments to scalar nets. Strength applies when driving 0 or 1. | Medium |
| 10.6.1 | assign/deassign statements | Procedural continuous assignment that overrides all other procedural assignments until deassign. Used for modeling async clear/preset. (Deprecated) | Medium |
| 11.4.5 | Equality operators | Case equality (`===`/`!==`) and logical equality (`==`/`!=`) operators, including behavior with class handles, chandles, and interface class handles. | Low |
| 11.4.6 | Wildcard equality operators | `==?` and `!=?` operators that treat x/z in the right operand as wildcards matching any bit value. Left operand x/z are not wildcards. | Low |
| 11.4.14.4 | Streaming dynamically sized data | Streaming operators with `with` expression for variable-size fields. Allows unpacking packets with dynamic array sizes specified inline. | High |
| 11.9 | Tagged union expressions | Creating tagged union values with `tagged` keyword and accessing members with dot notation. Runtime type checking ensures tag consistency. | High |
| 12.6.1 | Pattern matching in case | Case statements with `matches` keyword for pattern matching on tagged unions and structures. Supports wildcards, constants, and filter expressions. | High |
| 12.6.2 | Pattern matching in if | If statements with `matches` clauses using `&&&` operator for sequential pattern matching. Pattern identifiers scope to the true branch. | High |
| 12.6.3 | Pattern matching in conditionals | Ternary expressions (`?:`) with pattern matching predicates using `&&&` operator. Pattern identifiers scope to the consequent expression. | High |
| 15.5 | Named events | Event data type with `->` trigger, `->>` nonblocking trigger, `triggered` method, and `wait_order()` construct for event sequencing. | Medium |
| 16.7 | Sequences | SVA sequence declarations with concatenation (`##`), repetition, and composition operators. Foundation of concurrent assertions. | High |
| 16.9 | Sequence operations | Sequence operators: consecutive repetition (`[*]`), goto repetition (`[->`), nonconsecutive repetition (`[=]`), `throughout`, `within`, `intersect`, `and`, `or`. | High |
| 16.10 | Local variables | Dynamically created local variables in sequences/properties for pipelined transaction checking. Assigned at sequence match points. | High |
| 16.17 | Expect statement | Procedural blocking statement that waits for property success/failure. Blocks executing process until property evaluation completes. | High |
| 18.7 | Inline constraints (randomize with) | Adding constraints inline at randomize() call site. Supports local variable references and scope resolution with `local::` qualifier. | High |
| 18.17.7 | Randsequence value passing | Passing data to/from productions in randsequence. Productions can accept arguments (like tasks) and return values (like functions). | High |
| 20.14 | Probabilistic distribution functions | `$random`, `$dist_uniform`, `$dist_normal`, `$dist_exponential`, `$dist_poisson`, `$dist_chi_square`, `$dist_t`, `$dist_erlang` functions. | Low |

## Complexity Legend

- **Low**: Straightforward implementation, mostly parsing and basic code generation changes
- **Medium**: Requires moderate architectural changes, new data structures, or simulation semantics
- **High**: Requires significant infrastructure (assertion engine, constraint solver, type system extensions)

## Implementation Priority Recommendations

### Quick Wins (Low Complexity)
- 7.2.2 Structure default values
- 11.4.5/11.4.6 Equality operators (likely partial support exists)
- 20.14 Distribution functions

### Medium Effort
- 6.5 Mixed assignments to aggregates
- 6.6.4 Trireg nets
- 9.4.5 Intra-assignment timing
- 10.3.4 Drive strengths
- 10.6.1 assign/deassign (deprecated, lower priority)
- 15.5 Named events
- 8.26.6.* Interface class inheritance

### Major Features (High Complexity)
- 6.6.7/6.6.8 User-defined nettypes and interconnect
- 7.3.2/11.9/12.6.* Tagged unions and pattern matching (interdependent)
- 9.4.2.4/16.7/16.9/16.10/16.17 SVA sequences and assertions (interdependent)
- 11.4.14.4 Streaming with dynamic sizing
- 18.7/18.17.7 Advanced randomization features
