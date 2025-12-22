// writeback_stage.sv - Writeback Stage
// Part of the tri-mode SoC project
//
// Responsibilities:
// - Write results back to register file
// - Provide forwarding data

module writeback_stage
    import types_pkg::*;
    import pipeline_pkg::*;
(
    // Input from MEM/WB pipeline register
    input  mem_wb_t     mem_wb_in,

    // Register file write port
    output rf_addr_t    rf_rd_addr,
    output xlen_t       rf_rd_data,
    output logic        rf_rd_we,

    // Forwarding output
    output xlen_t       wb_fwd_data
);

    // Direct connection to register file
    assign rf_rd_addr = mem_wb_in.rd_addr;
    assign rf_rd_data = mem_wb_in.rd_data;
    assign rf_rd_we = mem_wb_in.rd_we && mem_wb_in.valid;

    // Forwarding data
    assign wb_fwd_data = mem_wb_in.rd_data;

endmodule
