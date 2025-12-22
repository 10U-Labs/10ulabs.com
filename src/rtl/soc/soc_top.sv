// soc_top.sv - Top-Level SoC
// Part of the tri-mode SoC project
//
// Integrates CPU core with instruction and data memories.
// This is the top-level module for simulation.

module soc_top
    import types_pkg::*;
#(
    parameter string IMEM_INIT_FILE = "",
    parameter string DMEM_INIT_FILE = ""
)(
    input  logic        clk,
    input  logic        rst_n,

    // Debug/trace interface (optional, active during simulation)
    output pc_t         dbg_pc,
    output logic        dbg_valid,
    output logic [31:0] dbg_instr,
    output logic [4:0]  dbg_rd_addr,
    output logic [63:0] dbg_rd_data,
    output logic        dbg_rd_we
);

    // =========================================================================
    // Internal Signals
    // =========================================================================

    // Instruction memory interface
    pc_t        imem_addr;
    instr_t     imem_rdata;
    logic       imem_valid;

    // Data memory interface
    xlen_t      dmem_addr;
    xlen_t      dmem_wdata;
    byte_en_t   dmem_be;
    logic       dmem_we;
    logic       dmem_req;
    xlen_t      dmem_rdata;

    // =========================================================================
    // CPU Core
    // =========================================================================

    core_top u_core (
        .clk            (clk),
        .rst_n          (rst_n),
        .imem_addr      (imem_addr),
        .imem_rdata     (imem_rdata),
        .imem_valid     (imem_valid),
        .dmem_addr      (dmem_addr),
        .dmem_wdata     (dmem_wdata),
        .dmem_be        (dmem_be),
        .dmem_we        (dmem_we),
        .dmem_req       (dmem_req),
        .dmem_rdata     (dmem_rdata)
    );

    // =========================================================================
    // Instruction Memory
    // =========================================================================

    imem #(
        .INIT_FILE      (IMEM_INIT_FILE)
    ) u_imem (
        .clk            (clk),
        .addr           (imem_addr),
        .rdata          (imem_rdata),
        .valid          (imem_valid)
    );

    // =========================================================================
    // Data Memory
    // =========================================================================

    dmem #(
        .INIT_FILE      (DMEM_INIT_FILE)
    ) u_dmem (
        .clk            (clk),
        .addr           (dmem_addr),
        .wdata          (dmem_wdata),
        .be             (dmem_be),
        .we             (dmem_we),
        .req            (dmem_req),
        .rdata          (dmem_rdata)
    );

    // =========================================================================
    // Debug Interface
    // =========================================================================

    // Expose internal signals for debugging/tracing
    // These track the MEM/WB stage for committed instructions
    assign dbg_pc = u_core.mem_wb_reg.valid ? u_core.ex_mem_reg.pc : '0;
    assign dbg_valid = u_core.mem_wb_reg.valid;
    assign dbg_instr = '0;  // Would need to propagate through pipeline
    assign dbg_rd_addr = u_core.mem_wb_reg.rd_addr;
    assign dbg_rd_data = u_core.mem_wb_reg.rd_data;
    assign dbg_rd_we = u_core.mem_wb_reg.rd_we && u_core.mem_wb_reg.valid;

endmodule
