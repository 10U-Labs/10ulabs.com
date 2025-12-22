// pipeline_regs.sv - Pipeline Register Module
// Part of the tri-mode SoC project
//
// Contains all inter-stage pipeline registers with stall/flush control:
// - IF/ID: Fetch -> Decode
// - ID/EX: Decode -> Execute
// - EX/MEM: Execute -> Memory
// - MEM/WB: Memory -> Writeback

module pipeline_regs
    import types_pkg::*;
    import pipeline_pkg::*;
(
    input  logic        clk,
    input  logic        rst_n,

    // IF/ID register
    input  if_id_t      if_id_in,
    input  logic        if_id_stall,
    input  logic        if_id_flush,
    output if_id_t      if_id_out,

    // ID/EX register
    input  id_ex_t      id_ex_in,
    input  logic        id_ex_stall,
    input  logic        id_ex_flush,
    output id_ex_t      id_ex_out,

    // EX/MEM register
    input  ex_mem_t     ex_mem_in,
    input  logic        ex_mem_stall,
    input  logic        ex_mem_flush,
    output ex_mem_t     ex_mem_out,

    // MEM/WB register
    input  mem_wb_t     mem_wb_in,
    input  logic        mem_wb_stall,
    input  logic        mem_wb_flush,
    output mem_wb_t     mem_wb_out
);

    // IF/ID pipeline register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            if_id_out <= IF_ID_RESET;
        end else if (if_id_flush) begin
            if_id_out <= IF_ID_RESET;
        end else if (!if_id_stall) begin
            if_id_out <= if_id_in;
        end
        // On stall, hold current value
    end

    // ID/EX pipeline register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            id_ex_out <= ID_EX_RESET;
        end else if (id_ex_flush) begin
            id_ex_out <= ID_EX_RESET;
        end else if (!id_ex_stall) begin
            id_ex_out <= id_ex_in;
        end
        // On stall, hold current value
    end

    // EX/MEM pipeline register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ex_mem_out <= EX_MEM_RESET;
        end else if (ex_mem_flush) begin
            ex_mem_out <= EX_MEM_RESET;
        end else if (!ex_mem_stall) begin
            ex_mem_out <= ex_mem_in;
        end
        // On stall, hold current value
    end

    // MEM/WB pipeline register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mem_wb_out <= MEM_WB_RESET;
        end else if (mem_wb_flush) begin
            mem_wb_out <= MEM_WB_RESET;
        end else if (!mem_wb_stall) begin
            mem_wb_out <= mem_wb_in;
        end
        // On stall, hold current value
    end

endmodule
