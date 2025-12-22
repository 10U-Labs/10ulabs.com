// imem.sv - Instruction Memory
// Part of the tri-mode SoC project
//
// Simple single-cycle instruction memory (ROM-like behavior).
// Initialized from hex file for testing.

module imem
    import types_pkg::*;
#(
    parameter string INIT_FILE = ""
)(
    input  logic        clk,
    input  pc_t         addr,
    output instr_t      rdata,
    output logic        valid
);

    // Memory array (word-addressed)
    // 64KB = 16K words
    logic [31:0] mem [0:IMEM_DEPTH-1];

    // Word address (drop lower 2 bits)
    logic [IMEM_ADDR_W-3:0] word_addr;
    assign word_addr = addr[IMEM_ADDR_W-1:2];

    // Initialize memory from file
    initial begin
        // Initialize to NOP (ADDI x0, x0, 0)
        for (int i = 0; i < IMEM_DEPTH; i++) begin
            mem[i] = 32'h00000013;
        end

        // Load hex file if specified
        if (INIT_FILE != "") begin
            $readmemh(INIT_FILE, mem);
        end
    end

    // Synchronous read (registered output for timing)
    always_ff @(posedge clk) begin
        rdata <= mem[word_addr];
    end

    // Always valid (no wait states in Phase 1)
    assign valid = 1'b1;

endmodule
