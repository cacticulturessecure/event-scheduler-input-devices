#!/usr/bin/env python3

import sys
import wave
import logging
import os
from datetime import datetime
import json
import sounddevice as sd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/audio_recording_log.txt'),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_config():
    config_file = os.path.join(os.path.dirname(__file__), 'recording_config.json')
    with open(config_file, 'r') as f:
        return json.load(f)

def record_audio(total_duration, event_title):
    logging.info(f"Starting audio-only recording for event: {event_title}")

    config = load_config()
    output_directories = config.get("output_directories", [])
    audio_config = config.get("audio_only_recording", {})

    device_index = audio_config.get('device', {}).get('device_index')
    if device_index is None:
        logging.error("No audio device index specified in configuration for ReSpeaker.")
        return

    try:
        device_info = sd.query_devices(device_index, 'input')
        samplerate = int(device_info['default_samplerate'])
        channels = device_info['max_input_channels']

        logging.info(f"Audio-only recording started for {total_duration} seconds using ReSpeaker")
        logging.info(f"Device: {device_info['name']}, Sample rate: {samplerate}, Channels: {channels}")

        recording = sd.rec(int(total_duration * samplerate), samplerate=samplerate, channels=channels, dtype='int16', device=device_index)
        sd.wait()

        logging.info("Audio-only recording completed")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for output_dir in output_directories:
            try:
                output_dir = os.path.abspath(output_dir)
                date_folder = datetime.now().strftime("%Y-%m-%d")
                output_folder = os.path.join(output_dir, date_folder)
                output_filename = os.path.join(output_folder, f"audio_only_{event_title}_{timestamp}.wav")

                os.makedirs(output_folder, exist_ok=True)
                logging.info(f"Output folder ensured at: {output_folder}")

                wf = wave.open(output_filename, 'wb')
                wf.setnchannels(channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(samplerate)
                wf.writeframes(recording.tobytes())
                wf.close()
                logging.info(f"Audio-only recording saved to: {output_filename}")

            except Exception as e:
                logging.error(f"Failed to save audio-only recording to {output_filename}: {e}")
                logging.debug("Exception details:", exc_info=True)

    except Exception as e:
        logging.error(f"Failed to record audio-only using ReSpeaker: {e}")
        logging.debug("Exception details:", exc_info=True)

    logging.info("Audio-only recording process completed")

if __name__ == "__main__":
    logging.info(f"Script called with args: {sys.argv}")
    if len(sys.argv) == 3:
        try:
            total_duration = float(sys.argv[1])
            event_title = sys.argv[2]
            logging.info(f"Parsed arguments: total_duration={total_duration}, event_title={event_title}")
            record_audio(total_duration, event_title)
        except ValueError:
            logging.error("Invalid total_duration provided. It must be a number representing seconds.")
    else:
        logging.error("Incorrect number of arguments provided. Usage: python ubuntu_create_local_singular_audio_recording.py <duration> <event_title>")
