#!/bin/bash
echo "Installing dependencies..."
pip install PyQt6 matplotlib numpy pandas pyvista vtk opencv-python --break-system-packages -q
echo "Launching AI Digital Twin..."
python3 main.py
