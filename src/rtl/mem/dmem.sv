// dmem.sv - Data Memory
// Part of the tri-mode SoC project
//
// Single-cycle data memory with byte-enable writes.
// 64-bit wide, 64KB capacity.

module dmem
    import types_pkg::*;
#(
    parameter string INIT_FILE = ""
)(
    input  logic        clk,
    input  xlen_t       addr,
    input  xlen_t       wdata,
    input  byte_en_t    be,
    input  logic        we,
    input  logic        req,
    output xlen_t       rdata
);

    // Memory array (doubleword-addressed)
    // 64KB = 8K doublewords
    logic [63:0] mem [0:DMEM_DEPTH-1];

    // Doubleword address (drop lower 3 bits)
    logic [DMEM_ADDR_W-4:0] dword_addr;
    assign dword_addr = addr[DMEM_ADDR_W-1:3];

    // Initialize memory
    initial begin
        for (int i = 0; i < DMEM_DEPTH; i++) begin
            mem[i] = 64'h0;
        end

        // Load hex file if specified
        if (INIT_FILE != "") begin
            $readmemh(INIT_FILE, mem);
        end
    end

    // Synchronous read
    always_ff @(posedge clk) begin
        if (req && !we) begin
            rdata <= mem[dword_addr];
        end
    end

    // Synchronous write with byte enables
    always_ff @(posedge clk) begin
        if (req && we) begin
            if (be[0]) mem[dword_addr][7:0]   <= wdata[7:0];
            if (be[1]) mem[dword_addr][15:8]  <= wdata[15:8];
            if (be[2]) mem[dword_addr][23:16] <= wdata[23:16];
            if (be[3]) mem[dword_addr][31:24] <= wdata[31:24];
            if (be[4]) mem[dword_addr][39:32] <= wdata[39:32];
            if (be[5]) mem[dword_addr][47:40] <= wdata[47:40];
            if (be[6]) mem[dword_addr][55:48] <= wdata[55:48];
            if (be[7]) mem[dword_addr][63:56] <= wdata[63:56];
        end
    end

endmodule
