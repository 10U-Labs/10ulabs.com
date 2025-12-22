// alu.sv - 64-bit Integer ALU for RV64I
// Part of the tri-mode SoC project
//
// Features:
// - Full 64-bit arithmetic and logic operations
// - 32-bit W-variant support (operate on lower 32 bits, sign-extend result)
// - Flags for branch comparison

module alu
    import types_pkg::*;
    import rv64_pkg::*;
(
    input  xlen_t       a,          // Operand A (rs1 or PC)
    input  xlen_t       b,          // Operand B (rs2 or immediate)
    input  alu_op_t     op,         // ALU operation
    input  logic        word_op,    // 1 = 32-bit W-variant operation
    output xlen_t       result,     // ALU result
    output logic        zero,       // Result is zero
    output logic        negative,   // Result is negative (MSB set)
    output logic        overflow    // Signed overflow occurred
);

    // Internal 64-bit result before W-variant handling
    xlen_t result_64;

    // 32-bit operands for W-variants
    logic [31:0] a_32, b_32;
    logic [31:0] result_32;

    assign a_32 = a[31:0];
    assign b_32 = b[31:0];

    // Shift amounts (6 bits for 64-bit, 5 bits for 32-bit)
    logic [5:0] shamt_64;
    logic [4:0] shamt_32;

    assign shamt_64 = b[5:0];
    assign shamt_32 = b[4:0];

    // Main ALU logic
    always_comb begin
        result_64 = '0;
        result_32 = '0;
        overflow = 1'b0;

        case (op)
            ALU_ADD: begin
                if (word_op) begin
                    result_32 = a_32 + b_32;
                end else begin
                    result_64 = a + b;
                    // Signed overflow: operands same sign, result different sign
                    overflow = (a[63] == b[63]) && (result_64[63] != a[63]);
                end
            end

            ALU_SUB: begin
                if (word_op) begin
                    result_32 = a_32 - b_32;
                end else begin
                    result_64 = a - b;
                    // Signed overflow for subtraction
                    overflow = (a[63] != b[63]) && (result_64[63] != a[63]);
                end
            end

            ALU_AND: begin
                if (word_op) begin
                    result_32 = a_32 & b_32;
                end else begin
                    result_64 = a & b;
                end
            end

            ALU_OR: begin
                if (word_op) begin
                    result_32 = a_32 | b_32;
                end else begin
                    result_64 = a | b;
                end
            end

            ALU_XOR: begin
                if (word_op) begin
                    result_32 = a_32 ^ b_32;
                end else begin
                    result_64 = a ^ b;
                end
            end

            ALU_SLT: begin
                // Set Less Than (signed comparison)
                // Returns 1 if a < b (signed), else 0
                result_64 = {{63{1'b0}}, $signed(a) < $signed(b)};
            end

            ALU_SLTU: begin
                // Set Less Than Unsigned
                // Returns 1 if a < b (unsigned), else 0
                result_64 = {{63{1'b0}}, a < b};
            end

            ALU_SLL: begin
                // Shift Left Logical
                if (word_op) begin
                    result_32 = a_32 << shamt_32;
                end else begin
                    result_64 = a << shamt_64;
                end
            end

            ALU_SRL: begin
                // Shift Right Logical
                if (word_op) begin
                    result_32 = a_32 >> shamt_32;
                end else begin
                    result_64 = a >> shamt_64;
                end
            end

            ALU_SRA: begin
                // Shift Right Arithmetic (preserves sign)
                if (word_op) begin
                    result_32 = $signed(a_32) >>> shamt_32;
                end else begin
                    result_64 = $signed(a) >>> shamt_64;
                end
            end

            ALU_PASS_A: begin
                // Pass operand A through (used for JALR return address)
                result_64 = a;
            end

            ALU_PASS_B: begin
                // Pass operand B through (used for LUI)
                result_64 = b;
            end

            default: begin
                result_64 = '0;
            end
        endcase
    end

    // Final result: sign-extend 32-bit result for W-variants
    always_comb begin
        if (word_op && op != ALU_SLT && op != ALU_SLTU) begin
            // Sign-extend 32-bit result to 64 bits
            result = {{32{result_32[31]}}, result_32};
        end else begin
            result = result_64;
        end
    end

    // Flag outputs
    assign zero = (result == '0);
    assign negative = result[63];

endmodule
