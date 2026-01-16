#!/bin/bash
# Start the gateway server using the virtual environment

echo "Activating virtual environment..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "Virtual environment activated."
else
    echo "Warning: Virtual environment not found at .venv/bin/activate"
    echo "Make sure you have created and activated the virtual environment."
    exit 1
fi

echo ""
echo "Starting gateway server..."
python start_gateway.py

