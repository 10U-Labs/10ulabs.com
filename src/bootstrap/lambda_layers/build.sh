#!/bin/bash
# Build a Lambda layer with Python dependencies
# Usage: ./build_lambda_layer.sh <layer_name> <requirements_path> <output_path>

set -euo pipefail

LAYER_NAME="${1:?Layer name required}"
REQUIREMENTS_PATH="${2:?Requirements path required}"
OUTPUT_PATH="${3:?Output path required}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
LAYER_SRC_DIR="$(dirname "$REQUIREMENTS_PATH")"

BUILD_DIR=$(mktemp -d)
trap 'rm -rf "$BUILD_DIR"' EXIT

echo "Building Lambda layer: $LAYER_NAME"
echo "Requirements: $REQUIREMENTS_PATH"
echo "Output: $OUTPUT_PATH"

# Lambda layers expect packages in python/ directory
mkdir -p "$BUILD_DIR/python"

# Install dependencies for Lambda's x86_64 Linux runtime
pip install \
    -r "$REQUIREMENTS_PATH" \
    -t "$BUILD_DIR/python" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.13 \
    --only-binary=:all: \
    --quiet

# Copy any Python modules from the layer source directory
for pyfile in "$LAYER_SRC_DIR"/*.py; do
    if [ -f "$pyfile" ]; then
        cp "$pyfile" "$BUILD_DIR/python/"
        echo "Added module: $(basename "$pyfile")"
    fi
done

# Create output directory if needed
mkdir -p "$(dirname "$OUTPUT_PATH")"

# Create the zip
cd "$BUILD_DIR"
zip -r -q "$OUTPUT_PATH" python/

echo "Layer built: $OUTPUT_PATH ($(du -h "$OUTPUT_PATH" | cut -f1))"
