// core_top.sv - Top-Level CPU Core
// Part of the tri-mode SoC project
//
// Integrates all pipeline stages, hazard handling, and register file
// into a complete 5-stage in-order RV64I pipeline.

module core_top
    import types_pkg::*;
    import rv64_pkg::*;
    import pipeline_pkg::*;
(
    input  logic        clk,
    input  logic        rst_n,

    // Instruction memory interface
    output pc_t         imem_addr,
    input  instr_t      imem_rdata,
    input  logic        imem_valid,

    // Data memory interface
    output xlen_t       dmem_addr,
    output xlen_t       dmem_wdata,
    output byte_en_t    dmem_be,
    output logic        dmem_we,
    output logic        dmem_req,
    input  xlen_t       dmem_rdata
);

    // =========================================================================
    // Pipeline Register Signals
    // =========================================================================

    // Stage outputs (combinational)
    if_id_t     if_id_next;
    id_ex_t     id_ex_next;
    ex_mem_t    ex_mem_next;
    mem_wb_t    mem_wb_next;

    // Pipeline register outputs
    if_id_t     if_id_reg;
    id_ex_t     id_ex_reg;
    ex_mem_t    ex_mem_reg;
    mem_wb_t    mem_wb_reg;

    // =========================================================================
    // Hazard Control Signals
    // =========================================================================

    logic       stall_if, stall_id;
    logic       flush_if, flush_id, flush_ex;
    pc_t        redirect_pc;

    fwd_sel_t   fwd_rs1, fwd_rs2;

    // =========================================================================
    // Register File Signals
    // =========================================================================

    rf_addr_t   rf_rs1_addr, rf_rs2_addr, rf_rd_addr;
    xlen_t      rf_rs1_data, rf_rs2_data, rf_rd_data;
    logic       rf_rd_we;

    // =========================================================================
    // Decode Stage Hazard Detection Signals
    // =========================================================================

    logic       dec_rs1_used, dec_rs2_used;
    rf_addr_t   dec_rs1_addr, dec_rs2_addr;

    // =========================================================================
    // Forwarding Data
    // =========================================================================

    xlen_t      ex_mem_fwd_data;
    xlen_t      mem_wb_fwd_data;

    // =========================================================================
    // Fetch Stage
    // =========================================================================

    logic       if_valid;

    fetch_stage u_fetch (
        .clk            (clk),
        .rst_n          (rst_n),
        .stall          (stall_if),
        .flush          (flush_if || ex_mem_reg.branch_taken),
        .redirect_pc    (ex_mem_reg.branch_taken ? ex_mem_reg.branch_target : redirect_pc),
        .imem_addr      (imem_addr),
        .imem_rdata     (imem_rdata),
        .imem_valid     (imem_valid),
        .if_id_out      (if_id_next),
        .if_valid       (if_valid)
    );

    // =========================================================================
    // Decode Stage
    // =========================================================================

    decode_stage u_decode (
        .clk            (clk),
        .rst_n          (rst_n),
        .if_id_in       (if_id_reg),
        .rf_rs1_addr    (rf_rs1_addr),
        .rf_rs2_addr    (rf_rs2_addr),
        .rf_rs1_data    (rf_rs1_data),
        .rf_rs2_data    (rf_rs2_data),
        .rs1_used       (dec_rs1_used),
        .rs2_used       (dec_rs2_used),
        .rs1_addr       (dec_rs1_addr),
        .rs2_addr       (dec_rs2_addr),
        .id_ex_out      (id_ex_next)
    );

    // =========================================================================
    // Execute Stage
    // =========================================================================

    execute_stage u_execute (
        .id_ex_in       (id_ex_reg),
        .fwd_rs1        (fwd_rs1),
        .fwd_rs2        (fwd_rs2),
        .fwd_ex_mem_data(ex_mem_fwd_data),
        .fwd_mem_wb_data(mem_wb_fwd_data),
        .ex_mem_out     (ex_mem_next)
    );

    // =========================================================================
    // Memory Stage
    // =========================================================================

    memory_stage u_memory (
        .ex_mem_in      (ex_mem_reg),
        .dmem_addr      (dmem_addr),
        .dmem_wdata     (dmem_wdata),
        .dmem_be        (dmem_be),
        .dmem_we        (dmem_we),
        .dmem_req       (dmem_req),
        .dmem_rdata     (dmem_rdata),
        .mem_wb_out     (mem_wb_next),
        .mem_fwd_data   (ex_mem_fwd_data)
    );

    // =========================================================================
    // Writeback Stage
    // =========================================================================

    writeback_stage u_writeback (
        .mem_wb_in      (mem_wb_reg),
        .rf_rd_addr     (rf_rd_addr),
        .rf_rd_data     (rf_rd_data),
        .rf_rd_we       (rf_rd_we),
        .wb_fwd_data    (mem_wb_fwd_data)
    );

    // =========================================================================
    // Register File
    // =========================================================================

    regfile u_regfile (
        .clk            (clk),
        .rst_n          (rst_n),
        .rs1_addr       (rf_rs1_addr),
        .rs2_addr       (rf_rs2_addr),
        .rs1_data       (rf_rs1_data),
        .rs2_data       (rf_rs2_data),
        .rd_addr        (rf_rd_addr),
        .rd_data        (rf_rd_data),
        .rd_we          (rf_rd_we)
    );

    // =========================================================================
    // Hazard Detection Unit
    // =========================================================================

    hazard_unit u_hazard (
        .if_id_rs1_addr (dec_rs1_addr),
        .if_id_rs2_addr (dec_rs2_addr),
        .if_id_rs1_used (dec_rs1_used),
        .if_id_rs2_used (dec_rs2_used),
        .id_ex_rd_addr  (id_ex_reg.rd_addr),
        .id_ex_is_load  (id_ex_reg.is_load),
        .id_ex_valid    (id_ex_reg.valid),
        .branch_taken   (ex_mem_reg.branch_taken && ex_mem_reg.valid),
        .branch_target  (ex_mem_reg.branch_target),
        .stall_if       (stall_if),
        .stall_id       (stall_id),
        .flush_if       (flush_if),
        .flush_id       (flush_id),
        .flush_ex       (flush_ex),
        .redirect_pc    (redirect_pc)
    );

    // =========================================================================
    // Forwarding Unit
    // =========================================================================

    forwarding_unit u_forwarding (
        .id_ex_rs1_addr (id_ex_reg.rs1_addr),
        .id_ex_rs2_addr (id_ex_reg.rs2_addr),
        .ex_mem_rd_addr (ex_mem_reg.rd_addr),
        .ex_mem_rd_we   (ex_mem_reg.rd_we),
        .ex_mem_valid   (ex_mem_reg.valid && !ex_mem_reg.is_load),  // Can't forward load in EX/MEM
        .mem_wb_rd_addr (mem_wb_reg.rd_addr),
        .mem_wb_rd_we   (mem_wb_reg.rd_we),
        .mem_wb_valid   (mem_wb_reg.valid),
        .fwd_rs1        (fwd_rs1),
        .fwd_rs2        (fwd_rs2)
    );

    // =========================================================================
    // Pipeline Registers
    // =========================================================================

    pipeline_regs u_pipeline_regs (
        .clk            (clk),
        .rst_n          (rst_n),

        // IF/ID
        .if_id_in       (if_id_next),
        .if_id_stall    (stall_id),
        .if_id_flush    (flush_id || (ex_mem_reg.branch_taken && ex_mem_reg.valid)),
        .if_id_out      (if_id_reg),

        // ID/EX
        .id_ex_in       (id_ex_next),
        .id_ex_stall    (1'b0),
        .id_ex_flush    (flush_ex || (ex_mem_reg.branch_taken && ex_mem_reg.valid)),
        .id_ex_out      (id_ex_reg),

        // EX/MEM
        .ex_mem_in      (ex_mem_next),
        .ex_mem_stall   (1'b0),
        .ex_mem_flush   (1'b0),
        .ex_mem_out     (ex_mem_reg),

        // MEM/WB
        .mem_wb_in      (mem_wb_next),
        .mem_wb_stall   (1'b0),
        .mem_wb_flush   (1'b0),
        .mem_wb_out     (mem_wb_reg)
    );

endmodule
