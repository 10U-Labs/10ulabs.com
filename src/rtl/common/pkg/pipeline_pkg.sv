// pipeline_pkg.sv - Pipeline stage interface structures
// Part of the tri-mode SoC project

package pipeline_pkg;

    import types_pkg::*;
    import rv64_pkg::*;

    // Fetch -> Decode pipeline register
    typedef struct packed {
        pc_t        pc;             // Program counter of this instruction
        instr_t     instr;          // Fetched instruction
        logic       valid;          // Instruction is valid
        logic       exception;      // Exception occurred during fetch
        exc_code_t  exc_code;       // Exception code
    } if_id_t;

    // Decode -> Execute pipeline register
    typedef struct packed {
        pc_t        pc;             // Program counter
        xlen_t      rs1_data;       // Source register 1 data
        xlen_t      rs2_data;       // Source register 2 data
        rf_addr_t   rs1_addr;       // Source register 1 address (for forwarding)
        rf_addr_t   rs2_addr;       // Source register 2 address (for forwarding)
        rf_addr_t   rd_addr;        // Destination register address
        xlen_t      imm;            // Sign-extended immediate
        logic       rd_we;          // Register write enable
        alu_op_t    alu_op;         // ALU operation
        logic       alu_src;        // ALU source: 0=rs2, 1=immediate
        logic       word_op;        // 32-bit W-variant operation
        logic       is_branch;      // Is a branch instruction
        logic [2:0] branch_funct;   // Branch function (BEQ, BNE, etc.)
        logic       is_jal;         // Is JAL
        logic       is_jalr;        // Is JALR
        logic       is_load;        // Is a load instruction
        logic       is_store;       // Is a store instruction
        logic [2:0] mem_size;       // Memory access size
        logic       mem_signed;     // Load sign extension
        logic       valid;          // Instruction is valid
    } id_ex_t;

    // Execute -> Memory pipeline register
    typedef struct packed {
        pc_t        pc;             // Program counter
        xlen_t      alu_result;     // ALU result / memory address
        xlen_t      rs2_data;       // Store data
        rf_addr_t   rd_addr;        // Destination register address
        logic       rd_we;          // Register write enable
        logic       is_load;        // Is a load instruction
        logic       is_store;       // Is a store instruction
        logic [2:0] mem_size;       // Memory access size
        logic       mem_signed;     // Load sign extension
        logic       branch_taken;   // Branch was taken
        pc_t        branch_target;  // Branch/jump target address
        logic       valid;          // Instruction is valid
    } ex_mem_t;

    // Memory -> Writeback pipeline register
    typedef struct packed {
        rf_addr_t   rd_addr;        // Destination register address
        xlen_t      rd_data;        // Data to write back
        logic       rd_we;          // Register write enable
        logic       valid;          // Instruction is valid
    } mem_wb_t;

    // Forwarding selection
    typedef enum logic [1:0] {
        FWD_NONE    = 2'b00,        // No forwarding, use register file
        FWD_EX_MEM  = 2'b01,        // Forward from EX/MEM stage
        FWD_MEM_WB  = 2'b10         // Forward from MEM/WB stage
    } fwd_sel_t;

    // Hazard control signals
    typedef struct packed {
        logic       stall_if;       // Stall IF stage
        logic       stall_id;       // Stall ID stage
        logic       flush_if;       // Flush IF stage
        logic       flush_id;       // Flush ID stage
        logic       flush_ex;       // Flush EX stage
        fwd_sel_t   fwd_rs1;        // Forwarding for rs1
        fwd_sel_t   fwd_rs2;        // Forwarding for rs2
    } hazard_ctrl_t;

    // Default/reset values
    parameter if_id_t IF_ID_RESET = '{
        pc: '0,
        instr: 32'h00000013,        // NOP (ADDI x0, x0, 0)
        valid: 1'b0,
        exception: 1'b0,
        exc_code: EXC_NONE
    };

    parameter id_ex_t ID_EX_RESET = '{
        pc: '0,
        rs1_data: '0,
        rs2_data: '0,
        rs1_addr: '0,
        rs2_addr: '0,
        rd_addr: '0,
        imm: '0,
        rd_we: 1'b0,
        alu_op: ALU_ADD,
        alu_src: 1'b0,
        word_op: 1'b0,
        is_branch: 1'b0,
        branch_funct: 3'b0,
        is_jal: 1'b0,
        is_jalr: 1'b0,
        is_load: 1'b0,
        is_store: 1'b0,
        mem_size: 3'b0,
        mem_signed: 1'b0,
        valid: 1'b0
    };

    parameter ex_mem_t EX_MEM_RESET = '{
        pc: '0,
        alu_result: '0,
        rs2_data: '0,
        rd_addr: '0,
        rd_we: 1'b0,
        is_load: 1'b0,
        is_store: 1'b0,
        mem_size: 3'b0,
        mem_signed: 1'b0,
        branch_taken: 1'b0,
        branch_target: '0,
        valid: 1'b0
    };

    parameter mem_wb_t MEM_WB_RESET = '{
        rd_addr: '0,
        rd_data: '0,
        rd_we: 1'b0,
        valid: 1'b0
    };

endpackage
