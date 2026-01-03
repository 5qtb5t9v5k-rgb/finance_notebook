#!/bin/bash
# Convenience script to activate virtual environment

cd "$(dirname "$0")"
source venv/bin/activate
echo "✅ Virtual environment activated!"
echo "You can now run:"
echo "  - streamlit run app/main.py"
echo "  - jupyter notebook"
echo "  - python scripts"

