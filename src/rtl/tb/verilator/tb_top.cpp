// tb_top.cpp - Verilator Testbench for RV64I Pipeline
// Part of the tri-mode SoC project

#include <verilated.h>
#include <verilated_fst_c.h>
#include "Vsoc_top.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

// Simulation parameters
static uint64_t max_cycles = 10000;
static bool trace_enabled = false;
static std::string program_file = "";

// Test pass/fail detection
// Convention: x31 = 1 means PASS, x31 = 0 means FAIL after test completion
static const uint64_t PASS_VALUE = 1;
static const int PASS_REG = 31;

void print_usage(const char* prog) {
    printf("Usage: %s [options]\n", prog);
    printf("Options:\n");
    printf("  +trace              Enable FST waveform tracing\n");
    printf("  +max_cycles=N       Maximum simulation cycles (default: 10000)\n");
    printf("  +program=FILE       Program hex file to load\n");
    printf("  +help               Show this help message\n");
}

void parse_args(int argc, char** argv) {
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "+trace") == 0) {
            trace_enabled = true;
        } else if (strncmp(argv[i], "+max_cycles=", 12) == 0) {
            max_cycles = strtoull(argv[i] + 12, nullptr, 10);
        } else if (strncmp(argv[i], "+program=", 9) == 0) {
            program_file = argv[i] + 9;
        } else if (strcmp(argv[i], "+help") == 0) {
            print_usage(argv[0]);
            exit(0);
        }
    }
}

int main(int argc, char** argv) {
    // Initialize Verilator
    Verilated::commandArgs(argc, argv);
    parse_args(argc, argv);

    // Create DUT instance
    Vsoc_top* dut = new Vsoc_top;

    // Setup tracing
    VerilatedFstC* tfp = nullptr;
    if (trace_enabled) {
        Verilated::traceEverOn(true);
        tfp = new VerilatedFstC;
        dut->trace(tfp, 99);
        tfp->open("sim.fst");
        printf("Tracing enabled: sim.fst\n");
    }

    // Reset sequence
    dut->clk = 0;
    dut->rst_n = 0;

    // Hold reset for 5 cycles
    for (int i = 0; i < 10; i++) {
        dut->clk = !dut->clk;
        dut->eval();
        if (tfp) tfp->dump(i);
    }

    // Release reset
    dut->rst_n = 1;

    // Main simulation loop
    uint64_t cycle = 0;
    uint64_t time_ps = 10;  // Start after reset
    bool test_done = false;
    bool test_passed = false;

    uint64_t last_pc = 0;
    int same_pc_count = 0;

    printf("Starting simulation...\n");
    if (!program_file.empty()) {
        printf("Program: %s\n", program_file.c_str());
    }
    printf("Max cycles: %lu\n", max_cycles);

    while (cycle < max_cycles && !test_done) {
        // Toggle clock
        dut->clk = !dut->clk;
        dut->eval();

        if (tfp) tfp->dump(time_ps);
        time_ps += 5;  // 100MHz clock = 10ns period = 5ns per edge

        // Check on rising edge
        if (dut->clk) {
            cycle++;

            // Debug output every 1000 cycles
            if (cycle % 1000 == 0) {
                printf("Cycle %lu: PC=0x%016lx valid=%d\n",
                       cycle, dut->dbg_pc, dut->dbg_valid);
            }

            // Detect infinite loop (same PC for many cycles)
            if (dut->dbg_valid) {
                if (dut->dbg_pc == last_pc) {
                    same_pc_count++;
                    if (same_pc_count > 10) {
                        printf("Detected infinite loop at PC=0x%016lx after %lu cycles\n",
                               last_pc, cycle);
                        test_done = true;

                        // Check x31 for pass/fail
                        // Note: In a real testbench, we'd read the register file
                        // For now, we check if rd_we was writing to x31
                        if (dut->dbg_rd_we && dut->dbg_rd_addr == PASS_REG) {
                            test_passed = (dut->dbg_rd_data == PASS_VALUE);
                        }
                    }
                } else {
                    last_pc = dut->dbg_pc;
                    same_pc_count = 0;
                }
            }

            // Check for test completion via x31 write
            if (dut->dbg_valid && dut->dbg_rd_we && dut->dbg_rd_addr == PASS_REG) {
                printf("Test register x31 written with value %lu at cycle %lu\n",
                       dut->dbg_rd_data, cycle);
                if (dut->dbg_rd_data == PASS_VALUE) {
                    test_passed = true;
                }
            }
        }
    }

    // Final status
    printf("\n=== Simulation Complete ===\n");
    printf("Total cycles: %lu\n", cycle);

    if (test_passed) {
        printf("TEST PASSED\n");
    } else if (cycle >= max_cycles) {
        printf("TEST TIMEOUT (max cycles reached)\n");
    } else {
        printf("TEST FAILED\n");
    }

    // Cleanup
    if (tfp) {
        tfp->close();
        delete tfp;
    }
    delete dut;

    return test_passed ? 0 : 1;
}
