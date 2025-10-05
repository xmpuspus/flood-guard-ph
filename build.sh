#!/usr/bin/env bash
# Render build script

set -o errexit  # Exit on error

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Setting up data directory..."
mkdir -p chroma_data

echo "Embedding projects (this may take a few minutes)..."
python scripts/embed_projects.py

echo "Build completed successfully!"