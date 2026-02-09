#!/bin/bash

# Render build script for monorepo (backend: Flask + frontend: React)
# This script handles building both services

set -e

echo "==> Stock Engine Build Started"

# Change to project root
cd "$(dirname "$0")"

# Install backend dependencies
echo "==> Installing backend dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo "==> Stock Engine Backend Ready"
echo "==> Use 'gunicorn -w 1 -b 0.0.0.0:\$PORT api:handler' to start"
