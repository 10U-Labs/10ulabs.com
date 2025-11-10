#!/usr/bin/env python3
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: tri-inspect <component>")
        sys.exit(1)
    component = sys.argv[1]
    print(f"Inspecting component: {component}")

if __name__ == "__main__":
    main()
