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
import psutil
import subprocess

# Configuration
CONFIG = {
    'EVENT_LIMIT': 20,
    'CHECK_INTERVAL': 60,
    'MIN_DISK_SPACE': 1000000000,  # 1 GB in bytes
    'MAX_CPU_USAGE': 90,  # 90%
    'SCREENSHOT_INTERVAL': 0.5,  # 2 screenshots per second
}

# Ensure the logs directory exists
if not os.path.exists('./logs/'):
    os.makedirs('./logs/')

# Configure logging with rotation
log_handler = RotatingFileHandler('./logs/screen_capture_log.txt', maxBytes=10000000, backupCount=5)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        log_handler,
        logging.StreamHandler(sys.stdout)
    ]
)


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



def run_screen_capture(event):
    try:
        start_time = datetime.strptime(f"{event['start_date']} {event['start_time']}", "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(f"{event['end_date']} {event['end_time']}", "%Y-%m-%d %H:%M:%S")
        duration = (end_time - start_time).total_seconds()
        logging.debug(f"Event duration calculated: {duration} seconds")

        # Create a directory for the event
        event_dir = os.path.join('screen_captures', event['title'])
        os.makedirs(event_dir, exist_ok=True)

        # Start screen capture process
        capture_command = f"python3 screen_capture.py {event_dir} {duration} {CONFIG['SCREENSHOT_INTERVAL']}"
        subprocess.Popen(capture_command, shell=True)

        logging.info(f"Started screen capture for event: {event['title']}")

    except Exception as e:
        logging.error(f"Error running screen capture for event '{event['title']}': {e}")
        logging.debug("Exception details:", exc_info=True)

def schedule_events():
    scheduler = BackgroundScheduler()
    current_time = datetime.now()
    scheduled_count = 0

    for batch in load_events():
        for event in sorted(batch, key=lambda x: datetime.strptime(f"{x['start_date']} {x['start_time']}", "%Y-%m-%d %H:%M:%S")):
            start_time = datetime.strptime(f"{event['start_date']} {event['start_time']}", "%Y-%m-%d %H:%M:%S")
            if start_time < current_time:
                continue

            scheduler.add_job(
                run_screen_capture,
                'date',
                run_date=start_time,
                args=[event],
                id=event['title'] + "_" + start_time.strftime("%Y%m%d_%H%M%S")
            )
            logging.info(f"Scheduled screen capture for '{event['title']}' at {start_time}")

            scheduled_count += 1
            if scheduled_count >= CONFIG['EVENT_LIMIT']:
                logging.info(f"Reached scheduled events limit of {CONFIG['EVENT_LIMIT']}")
                return scheduler, scheduled_count

    logging.info(f"Total events scheduled: {scheduled_count}")
    return scheduler, scheduled_count

def main(args):
    logging.info("Starting screen capture scheduler")
    scheduler, scheduled_count = schedule_events()
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
        logging.info("Scheduler stopped. Exiting.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Screen Capture Scheduler")
    parser.add_argument("--event-limit", type=int, help="Maximum number of events to schedule")
    parser.add_argument("--check-interval", type=int, help="Interval to check for completed events (seconds)")
    args = parser.parse_args()

    if args.event_limit:
        CONFIG['EVENT_LIMIT'] = args.event_limit
    if args.check_interval:
        CONFIG['CHECK_INTERVAL'] = args.check_interval

    main(args)
