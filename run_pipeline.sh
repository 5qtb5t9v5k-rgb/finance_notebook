#!/bin/bash
# Pipeline runner script that ensures virtual environment is used

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virhe: virtuaaliympäristöä ei löydy!"
    echo "   Luo virtuaaliympäristö ensin:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment and run pipeline
source venv/bin/activate
python run_pipeline.py

