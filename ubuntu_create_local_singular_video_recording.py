#!/usr/bin/env python3

import cv2
import sounddevice as sd
import numpy as np
import sys
import logging
import os
from datetime import datetime
import json
import scipy.io.wavfile as wavfile

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/video_recording_log.txt'),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_config():
    config_file = os.path.join(os.path.dirname(__file__), 'recording_config.json')
    with open(config_file, 'r') as f:
        return json.load(f)

def record_video_and_audio(total_duration, event_name):
    logging.info(f"Starting video and audio recording for event: {event_name}")

    config = load_config()
    output_directories = config.get("output_directories", [])
    video_config = config.get("video_recording", {})

    video_device = video_config.get('camera', {}).get('device_path')
    audio_device_index = video_config.get('audio', {}).get('device_index')

    if not video_device or audio_device_index is None:
        logging.error("Video device or audio device index not specified in configuration.")
        return

    try:
        cap = cv2.VideoCapture(video_device)
        if not cap.isOpened():
            logging.error(f"Failed to open video device: {video_device}")
            return

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        logging.info(f"Video capture initialized: {width}x{height} @ {fps} fps")

        audio_info = sd.query_devices(audio_device_index, 'input')
        samplerate = int(audio_info['default_samplerate'])
        channels = 1  # Mono audio

        logging.info(f"Audio capture initialized: Device index {audio_device_index}, Sample rate: {samplerate}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for output_dir in output_directories:
            try:
                output_dir = os.path.abspath(output_dir)
                date_folder = datetime.now().strftime("%Y-%m-%d")
                output_folder = os.path.join(output_dir, date_folder)
                os.makedirs(output_folder, exist_ok=True)

                video_filename = os.path.join(output_folder, f"video_{event_name}_{timestamp}.mp4")
                audio_filename = os.path.join(output_folder, f"audio_{event_name}_{timestamp}.wav")

                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))

                def audio_callback(indata, frames, time, status):
                    if status:
                        print(status)
                    audio_frames.append(indata.copy())

                audio_frames = []

                with sd.InputStream(samplerate=samplerate, device=audio_device_index, channels=channels, callback=audio_callback):
                    start_time = datetime.now()
                    frame_count = 0
                    while (datetime.now() - start_time).total_seconds() < total_duration:
                        ret, frame = cap.read()
                        if ret:
                            out.write(frame)
                            frame_count += 1
                        else:
                            logging.warning("Failed to capture video frame")

                out.release()
                logging.info(f"Video saved to: {video_filename}")
                logging.info(f"Total frames recorded: {frame_count}")

                audio_data = np.concatenate(audio_frames, axis=0)
                wavfile.write(audio_filename, samplerate, audio_data)
                logging.info(f"Audio saved to: {audio_filename}")

                actual_fps = frame_count / total_duration
                logging.info(f"Actual FPS: {actual_fps:.2f}")

            except Exception as e:
                logging.error(f"Failed to save recordings for event '{event_name}': {e}")
                logging.debug("Exception details:", exc_info=True)

        cap.release()

    except Exception as e:
        logging.error(f"An error occurred during recording: {e}")
        logging.debug("Exception details:", exc_info=True)

    logging.info(f"Video and audio recording process completed for event: {event_name}")


if __name__ == "__main__":
    logging.info(f"Script called with args: {sys.argv}")
    if len(sys.argv) == 3:
        try:
            total_duration = float(sys.argv[1])
            event_name = sys.argv[2]
            logging.info(f"Parsed arguments: total_duration={total_duration}, event_name={event_name}")
            record_video_and_audio(total_duration, event_name)
        except ValueError:
            logging.error("Invalid total_duration provided. It must be a number representing seconds.")
    else:
        logging.error("Incorrect number of arguments provided. Usage: python ubuntu_create_local_singular_video_recording.py <duration> <event_name>")
