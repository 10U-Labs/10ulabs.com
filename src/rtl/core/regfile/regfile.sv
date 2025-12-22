// regfile.sv - 32x64-bit Register File for RV64I
// Part of the tri-mode SoC project
//
// Features:
// - 32 general-purpose 64-bit registers (x0-x31)
// - x0 is hardwired to zero
// - 2 read ports (combinational)
// - 1 write port (synchronous, rising edge)
// - Write-through: reads see writes in same cycle

module regfile
    import types_pkg::*;
(
    input  logic        clk,
    input  logic        rst_n,

    // Read port 1
    input  rf_addr_t    rs1_addr,
    output xlen_t       rs1_data,

    // Read port 2
    input  rf_addr_t    rs2_addr,
    output xlen_t       rs2_data,

    // Write port
    input  rf_addr_t    rd_addr,
    input  xlen_t       rd_data,
    input  logic        rd_we
);

    // Register array (x0-x31)
    xlen_t regs [31:1];  // x0 is not stored, always reads as 0

    // Synchronous write with reset
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all registers to 0
            for (int i = 1; i < 32; i++) begin
                regs[i] <= '0;
            end
        end else if (rd_we && rd_addr != '0) begin
            // Write to register (ignore writes to x0)
            regs[rd_addr] <= rd_data;
        end
    end

    // Combinational read with write-through
    // If reading the same register being written, return the write data
    always_comb begin
        // Read port 1
        if (rs1_addr == '0) begin
            rs1_data = '0;  // x0 always reads as 0
        end else if (rd_we && rs1_addr == rd_addr) begin
            rs1_data = rd_data;  // Write-through
        end else begin
            rs1_data = regs[rs1_addr];
        end

        // Read port 2
        if (rs2_addr == '0) begin
            rs2_data = '0;  // x0 always reads as 0
        end else if (rd_we && rs2_addr == rd_addr) begin
            rs2_data = rd_data;  // Write-through
        end else begin
            rs2_data = regs[rs2_addr];
        end
    end

endmodule
