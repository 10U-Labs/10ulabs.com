// fetch_stage.sv - Instruction Fetch Stage
// Part of the tri-mode SoC project
//
// Responsibilities:
// - Maintain program counter
// - Interface with instruction memory
// - Handle stalls and flushes

module fetch_stage
    import types_pkg::*;
    import pipeline_pkg::*;
(
    input  logic        clk,
    input  logic        rst_n,

    // Control inputs
    input  logic        stall,          // Stall the fetch stage
    input  logic        flush,          // Flush (redirect)
    input  pc_t         redirect_pc,    // New PC on redirect

    // Instruction memory interface
    output pc_t         imem_addr,      // Address to instruction memory
    input  instr_t      imem_rdata,     // Instruction from memory
    input  logic        imem_valid,     // Instruction is valid

    // Output to decode stage
    output if_id_t      if_id_out,
    output logic        if_valid
);

    // Program counter register
    pc_t pc_reg;
    pc_t pc_next;

    // PC update logic
    always_comb begin
        if (flush) begin
            pc_next = redirect_pc;
        end else if (stall) begin
            pc_next = pc_reg;
        end else begin
            pc_next = pc_reg + 64'd4;
        end
    end

    // PC register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_reg <= 64'h0000_0000_8000_0000;  // Reset vector
        end else begin
            pc_reg <= pc_next;
        end
    end

    // Instruction memory address
    assign imem_addr = pc_reg;

    // Output to IF/ID pipeline register
    always_comb begin
        if_id_out.pc = pc_reg;
        if_id_out.instr = imem_rdata;
        if_id_out.valid = imem_valid && !flush;
        if_id_out.exception = 1'b0;  // No exception handling in Phase 1
        if_id_out.exc_code = EXC_NONE;
    end

    assign if_valid = imem_valid && !stall && !flush;

endmodule
