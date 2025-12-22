// memory_stage.sv - Memory Access Stage
// Part of the tri-mode SoC project
//
// Responsibilities:
// - Interface with data memory for loads/stores
// - Forward load data to writeback

module memory_stage
    import types_pkg::*;
    import rv64_pkg::*;
    import pipeline_pkg::*;
(
    // Input from EX/MEM pipeline register
    input  ex_mem_t     ex_mem_in,

    // Data memory interface
    output xlen_t       dmem_addr,
    output xlen_t       dmem_wdata,
    output byte_en_t    dmem_be,
    output logic        dmem_we,
    output logic        dmem_req,
    input  xlen_t       dmem_rdata,

    // Output to MEM/WB pipeline register
    output mem_wb_t     mem_wb_out,

    // Forwarding output (for EX stage)
    output xlen_t       mem_fwd_data
);

    // Load data from LSU
    xlen_t load_data;

    // Instantiate LSU
    lsu u_lsu (
        .addr           (ex_mem_in.alu_result),
        .store_data     (ex_mem_in.rs2_data),
        .mem_size       (ex_mem_in.mem_size),
        .mem_signed     (ex_mem_in.mem_signed),
        .is_load        (ex_mem_in.is_load),
        .is_store       (ex_mem_in.is_store),
        .dmem_addr      (dmem_addr),
        .dmem_wdata     (dmem_wdata),
        .dmem_be        (dmem_be),
        .dmem_we        (dmem_we),
        .dmem_req       (dmem_req),
        .dmem_rdata     (dmem_rdata),
        .load_data      (load_data)
    );

    // Output to MEM/WB pipeline register
    always_comb begin
        mem_wb_out.rd_addr = ex_mem_in.rd_addr;
        mem_wb_out.rd_we = ex_mem_in.rd_we && ex_mem_in.valid;

        // Select between ALU result and load data
        if (ex_mem_in.is_load) begin
            mem_wb_out.rd_data = load_data;
        end else begin
            mem_wb_out.rd_data = ex_mem_in.alu_result;
        end

        mem_wb_out.valid = ex_mem_in.valid;
    end

    // Forwarding data (ALU result, not load - load-use hazard handled by stall)
    assign mem_fwd_data = ex_mem_in.alu_result;

endmodule
