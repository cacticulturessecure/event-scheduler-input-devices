#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Get the directory of this script
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

# Path to the virtual environment's Python interpreter
VENV_PYTHON="$SCRIPT_DIR/../schedular/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
  echo "Virtual environment Python interpreter not found at $VENV_PYTHON"
  exit 1
fi

# Function to run a Python script in the background
run_python_script() {
  "$VENV_PYTHON" "$1" "$2" "$3" &
}

# Run the Python audio-only recording script with provided duration and event title arguments
echo "Starting audio-only recording..."
run_python_script "$SCRIPT_DIR/ubuntu_create_local_singular_audio_recording.py" "$1" "$2"

# Run the Python video and audio recording script with provided duration and event title arguments
echo "Starting video and audio recording..."
run_python_script "$SCRIPT_DIR/ubuntu_create_local_singular_video_recording.py" "$1" "$2"

# Wait for all background processes to complete
wait

echo "All recordings completed."
