#!/usr/bin/env python3

import os
import json
from datetime import datetime, timedelta
import sys
import logging
from logging.handlers import RotatingFileHandler
import argparse
from apscheduler.schedulers.background import BackgroundScheduler
import time
from tmux_session_manager import TmuxSessionManager
import psutil

# Configuration
CONFIG = {
    'EVENT_LIMIT': 20,
    'RETRY_LIMIT': 3,
    'CHECK_INTERVAL': 60,
    'MIN_DISK_SPACE': 1000000000,  # 1 GB in bytes
    'MAX_CPU_USAGE': 90,  # 90%
}

# Ensure the logs directory exists
if not os.path.exists('./logs/'):
    os.makedirs('./logs/')

# Configure logging with rotation
log_handler = RotatingFileHandler('./logs/scheduling_log.txt', maxBytes=10000000, backupCount=5)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        log_handler,
        logging.StreamHandler(sys.stdout)
    ]
)

def load_config():
    config_file = os.path.join(os.path.dirname(__file__), 'recording_config.json')
    with open(config_file, 'r') as f:
        return json.load(f)

def load_events(batch_size=100):
    export_dir = os.path.abspath(os.path.join('.', 'media', 'exports'))
    logging.debug(f"Looking for events in directory: {export_dir}")

    if not os.path.exists(export_dir):
        logging.warning(f"Export directory does not exist: {export_dir}")
        return

    for root, dirs, files in os.walk(export_dir):
        logging.debug(f"Scanning directory: {root}")
        batch = []
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        event = json.load(f)
                    event['title'] = event['title'].strip().replace(' ', '_')
                    batch.append(event)
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from {file_path}: {e}")
                except Exception as e:
                    logging.error(f"Unexpected error loading {file_path}: {e}")
        if batch:
            yield batch

def check_system_resources():
    disk_space = psutil.disk_usage('/').free
    cpu_usage = psutil.cpu_percent(interval=1)
    if disk_space < CONFIG['MIN_DISK_SPACE']:
        logging.error(f"Low disk space: {disk_space} bytes available")
        return False
    if cpu_usage > CONFIG['MAX_CPU_USAGE']:
        logging.error(f"High CPU usage: {cpu_usage}%")
        return False
    return True

def run_recording(event, tmux_manager):
    try:
        start_time = datetime.strptime(f"{event['start_date']} {event['start_time']}", "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(f"{event['end_date']} {event['end_time']}", "%Y-%m-%d %H:%M:%S")
        duration = (end_time - start_time).total_seconds()
        logging.debug(f"Event duration calculated: {duration} seconds")

        # Terminate any existing sessions
        tmux_manager.terminate_all_sessions()

        # Force release all devices
        tmux_manager.force_release_all_devices()

        # Start both audio and video recordings
        audio_session = tmux_manager.start_audio_recording(duration, event['title'])
        video_session = tmux_manager.start_video_recording(duration, event['title'])

        # Wait for both sessions to finish or timeout
        recording_start_time = time.time()
        max_wait_time = duration + 60  # Add 60 seconds buffer

        while time.time() - recording_start_time < max_wait_time:
            if not tmux_manager.session_exists(audio_session) and not tmux_manager.session_exists(video_session):
                break
            time.sleep(5)

        # If sessions are still running after max_wait_time, terminate them
        if tmux_manager.session_exists(audio_session):
            tmux_manager.kill_session(audio_session)
            logging.warning(f"Audio session {audio_session} exceeded max duration and was terminated.")
        if tmux_manager.session_exists(video_session):
            tmux_manager.kill_session(video_session)
            logging.warning(f"Video session {video_session} exceeded max duration and was terminated.")

        actual_duration = time.time() - recording_start_time

        # Release devices after recording
        tmux_manager.release_devices()

        logging.info(f"Completed event: {event['title']}. Duration: {actual_duration:.2f}s")

        # Start combination process
        config = load_config()
        output_directories = config.get("output_directories", [])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_folder = datetime.now().strftime("%Y-%m-%d")

        for output_dir in output_directories:
            output_folder = os.path.join(output_dir, date_folder)
            video_file = os.path.join(output_folder, f"video_{event['title']}_{timestamp}.mp4")
            audio_file = os.path.join(output_folder, f"audio_{event['title']}_{timestamp}.wav")
            output_file = os.path.join(output_folder, f"combined_{event['title']}_{timestamp}.mp4")
            
            combine_session = tmux_manager.start_combination_process(video_file, audio_file, output_file)
            logging.info(f"Started combination process for {event['title']} in session {combine_session}")

    except Exception as e:
        logging.error(f"Error running recording for event '{event['title']}': {e}")
        logging.debug("Exception details:", exc_info=True)
        # Ensure devices are released even if an error occurs
        tmux_manager.force_release_all_devices()

def schedule_events(tmux_manager):
    scheduler = BackgroundScheduler()
    current_time = datetime.now()
    scheduled_count = 0

    for batch in load_events():
        for event in sorted(batch, key=lambda x: datetime.strptime(f"{x['start_date']} {x['start_time']}", "%Y-%m-%d %H:%M:%S")):
            start_time = datetime.strptime(f"{event['start_date']} {event['start_time']}", "%Y-%m-%d %H:%M:%S")
            if start_time < current_time:
                continue

            scheduler.add_job(
                run_recording,
                'date',
                run_date=start_time,
                args=[event, tmux_manager],
                id=event['title'] + "_" + start_time.strftime("%Y%m%d_%H%M%S")
            )
            logging.info(f"Scheduled recording for '{event['title']}' at {start_time}")

            scheduled_count += 1
            if scheduled_count >= CONFIG['EVENT_LIMIT']:
                logging.info(f"Reached scheduled events limit of {CONFIG['EVENT_LIMIT']}")
                return scheduler, scheduled_count

    logging.info(f"Total events scheduled: {scheduled_count}")
    return scheduler, scheduled_count

def main(args):
    logging.info("Starting recording scheduler")
    tmux_manager = TmuxSessionManager()
    scheduler, scheduled_count = schedule_events(tmux_manager)
    scheduler.start()
    logging.info("Scheduler started. Waiting for events...")

    try:
        while scheduler.get_jobs():
            time.sleep(CONFIG['CHECK_INTERVAL'])
            logging.debug(f"Active jobs: {len(scheduler.get_jobs())}")
    except (KeyboardInterrupt, SystemExit):
        logging.info("Received exit signal. Shutting down scheduler.")
    finally:
        scheduler.shutdown()
        tmux_manager.cleanup()
        logging.info("Scheduler stopped. Exiting.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recording Scheduler")
    parser.add_argument("--event-limit", type=int, help="Maximum number of events to schedule")
    parser.add_argument("--check-interval", type=int, help="Interval to check for completed events (seconds)")
    args = parser.parse_args()

    if args.event_limit:
        CONFIG['EVENT_LIMIT'] = args.event_limit
    if args.check_interval:
        CONFIG['CHECK_INTERVAL'] = args.check_interval

    main(args)
