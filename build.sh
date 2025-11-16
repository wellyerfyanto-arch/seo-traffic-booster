#!/bin/bash
echo "Starting build process..."
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
playwright install-deps
echo "Build completed successfully!"
