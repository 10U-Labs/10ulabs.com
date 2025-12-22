// types_pkg.sv - Core type definitions for RV64I pipeline
// Part of the tri-mode SoC project

package types_pkg;

    // Core parameters
    parameter int XLEN = 64;              // Register/data width
    parameter int RF_ADDR_W = 5;          // Register file address width (32 registers)
    parameter int PC_W = 64;              // Program counter width
    parameter int INSTR_W = 32;           // Instruction width
    parameter int IMEM_ADDR_W = 16;       // Instruction memory address width (64KB)
    parameter int DMEM_ADDR_W = 16;       // Data memory address width (64KB)
    parameter int IMEM_DEPTH = 1 << (IMEM_ADDR_W - 2);  // Word-addressed
    parameter int DMEM_DEPTH = 1 << (DMEM_ADDR_W - 3);  // Doubleword-addressed

    // Core type definitions
    typedef logic [XLEN-1:0]        xlen_t;         // 64-bit data
    typedef logic [RF_ADDR_W-1:0]   rf_addr_t;      // Register address (0-31)
    typedef logic [PC_W-1:0]        pc_t;           // Program counter
    typedef logic [INSTR_W-1:0]     instr_t;        // Instruction word

    // Memory types
    typedef logic [IMEM_ADDR_W-1:0] imem_addr_t;    // Instruction memory address
    typedef logic [DMEM_ADDR_W-1:0] dmem_addr_t;    // Data memory address
    typedef logic [7:0]             byte_t;         // Byte
    typedef logic [15:0]            half_t;         // Halfword
    typedef logic [31:0]            word_t;         // Word
    typedef logic [63:0]            dword_t;        // Doubleword

    // Byte enable for memory operations
    typedef logic [7:0]             byte_en_t;      // 8 bytes for 64-bit

    // Exception codes (for future use)
    typedef enum logic [3:0] {
        EXC_NONE            = 4'd0,
        EXC_INSTR_MISALIGN  = 4'd1,
        EXC_INSTR_FAULT     = 4'd2,
        EXC_ILLEGAL_INSTR   = 4'd3,
        EXC_BREAKPOINT      = 4'd4,
        EXC_LOAD_MISALIGN   = 4'd5,
        EXC_LOAD_FAULT      = 4'd6,
        EXC_STORE_MISALIGN  = 4'd7,
        EXC_STORE_FAULT     = 4'd8
    } exc_code_t;

endpackage
