# Top-Level RTL Makefile
# Part of the tri-mode SoC project
#
# Phase 1: Minimal in-order RV64I pipeline with Verilator testbench

.PHONY: all build run test clean lint programs help

# Default target
all: build

# Build Verilator simulation
build:
	$(MAKE) -C tb/verilator build

# Run simulation (with default test)
run: build
	$(MAKE) -C tb/verilator run

# Run with specific program
run-program: build programs
	$(MAKE) -C tb/verilator run-program PROGRAM=$(PROGRAM)

# Build test programs
programs:
	$(MAKE) -C tb/programs all

# Run all tests
test: build programs
	@echo "Running all tests..."
	@passed=0; failed=0; \
	for hex in tb/programs/bin/*.hex; do \
		name=$$(basename $$hex .hex); \
		echo "Running $$name..."; \
		if ./tb/verilator/obj_dir/Vsoc_top +program=$$hex +max_cycles=10000 2>&1 | grep -q "TEST PASSED"; then \
			echo "  PASSED"; \
			passed=$$((passed + 1)); \
		else \
			echo "  FAILED"; \
			failed=$$((failed + 1)); \
		fi; \
	done; \
	echo ""; \
	echo "Results: $$passed passed, $$failed failed"; \
	if [ $$failed -gt 0 ]; then exit 1; fi

# Lint RTL only
lint:
	$(MAKE) -C tb/verilator lint

# Clean all build artifacts
clean:
	$(MAKE) -C tb/verilator clean
	$(MAKE) -C tb/programs clean

# Show help
help:
	@echo "Tri-Mode SoC RTL Project - Phase 1"
	@echo ""
	@echo "Targets:"
	@echo "  all       - Build Verilator simulation (default)"
	@echo "  build     - Build Verilator simulation"
	@echo "  run       - Run simulation with default settings"
	@echo "  run-program PROGRAM=<path> - Run with specific hex file"
	@echo "  programs  - Build all test programs"
	@echo "  test      - Run all test programs"
	@echo "  lint      - Lint RTL files only"
	@echo "  clean     - Clean all build artifacts"
	@echo "  help      - Show this help"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - Verilator (tested with 5.x)"
	@echo "  - RISC-V toolchain (riscv64-unknown-elf-*)"
