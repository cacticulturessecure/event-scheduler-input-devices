#!/usr/bin/env python3

import subprocess
import os
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    with open('recording_config.json', 'r') as f:
        return json.load(f)

def screen_capture(output_dir, duration, event_title):
    config = load_config()
    screen_config = config['screen_capture']
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{event_title}_{timestamp}.{screen_config['output_format']}"
    output_path = os.path.join(output_dir, output_filename)
    
    ffmpeg_command = [
        "ffmpeg",
        "-f", "x11grab",
        "-framerate", str(screen_config['framerate']),
        "-video_size", "1920x1080",  # Adjust if your resolution is different
        "-i", screen_config['display'],
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        output_path
    ]
    
    logging.info(f"Starting screen capture: {' '.join(ffmpeg_command)}")
    
    try:
        subprocess.run(ffmpeg_command, check=True)
        logging.info(f"Screen capture completed: {output_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during screen capture: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python ffmpeg_screen_capture.py <output_directory> <duration> <event_title>")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    duration = float(sys.argv[2])
    event_title = sys.argv[3]
    
    screen_capture(output_dir, duration, event_title)
