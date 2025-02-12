#!/bin/bash

# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Ensure build tool is installed
uv pip install build

# Build package
echo "Building package..."
python -m build

# Install locally
echo "Installing locally..."
uv pip install -e .

# Test installation
echo "Testing installation..."
nanidao-eval --list-behaviors

echo "Build complete! Test the installation by running 'nanidao-eval --help'"