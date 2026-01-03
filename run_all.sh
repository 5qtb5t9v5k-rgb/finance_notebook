#!/bin/bash
# Run pipeline and then start Streamlit app

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

# Activate virtual environment
source venv/bin/activate

echo "============================================================"
echo "🔄 Ajetaan pipeline ensin..."
echo "============================================================"

# Run pipeline
python run_pipeline.py

# Check if pipeline was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "🚀 Käynnistetään Streamlit-sovellus..."
    echo "============================================================"
    echo ""
    echo "💡 Streamlit avautuu selaimessa automaattisesti"
    echo "   Paina Ctrl+C lopettaaksesi"
    echo ""
    
    # Start Streamlit app using venv Python directly to ensure correct environment
    # This ensures Streamlit uses the venv Python, not system Python
    # Set PYTHONPATH to ensure imports work correctly
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    
    # Verify venv Python exists and has required packages
    VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
    if [ ! -f "$VENV_PYTHON" ]; then
        echo "❌ Error: venv Python not found at $VENV_PYTHON"
        exit 1
    fi
    
    # Check if OpenAI is installed in venv
    if ! "$VENV_PYTHON" -c "import openai" 2>/dev/null; then
        echo "⚠️  Warning: OpenAI not found in venv. Installing..."
        "$VENV_PYTHON" -m pip install openai
    fi
    
    # Use venv Python explicitly with full path
    echo "🚀 Starting Streamlit with: $VENV_PYTHON"
    exec "$VENV_PYTHON" -m streamlit run app/main.py
else
    echo ""
    echo "❌ Pipeline epäonnistui. Streamlit-sovellusta ei käynnistetä."
    exit 1
fi

