#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Create static folder if it doesn't exist
mkdir -p static

echo "Build completed"