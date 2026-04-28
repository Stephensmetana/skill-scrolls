#!/bin/bash

# Create a virtual environment named 'venv' in the current directory
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install requirements from requirements.txt
pip install -r requirements.txt
