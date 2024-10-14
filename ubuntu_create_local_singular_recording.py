#!/usr/bin/env python3

import os
import json
from datetime import datetime, timedelta
import subprocess
import sys
import logging
import shlex
from apscheduler.schedulers.background import BackgroundScheduler
import time
import traceback

# Ensure the logs directory exists
if not os.path.exists('./logs/'):
    os.makedirs('./logs/')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/scheduling_log.txt'),
        logging.StreamHandler(sys.stdout)
    ]
)


def load_events():
    events = []
    export_dir = os.path.abspath(os.path.join('.', 'media', 'exports'))
    logging.debug(f"Looking for events in directory: {export_dir}")

    if not os.path.exists(export_dir):
        logging.warning(f"Export directory does not exist: {export_dir}")
        return events

    for root, dirs, files in os.walk(export_dir):
        logging.debug(f"Scanning directory: {root}")
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                logging.debug(f"Found JSON file: {file_path}")
                try:
                    with open(file_path, 'r') as f:
                        event = json.load(f)
                        event['title'] = event['title'].strip().replace(' ', '_')
                        logging.debug(f"Loaded event from {file_path}: {event}")
                        events.append(event)
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from {file_path}: {e}")
                    logging.debug("Exception details:", exc_info=True)
                except Exception as e:
                    logging.error(f"Unexpected error loading {file_path}: {e}")
                    logging.debug("Exception details:", exc_info=True)

    logging.info(f"Total events loaded: {len(events)}")
    return events

completed_events = 0

def run_recording(event):
    global completed_events
    try:
        start_time = datetime.strptime(f"{event['start_date']} {event['start_time']}", "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(f"{event['end_date']} {event['end_time']}", "%Y-%m-%d %H:%M:%S")
        duration = (end_time - start_time).total_seconds()
        logging.debug(f"Event duration calculated: {duration} seconds")

        script_dir = os.path.abspath(os.path.dirname(__file__))
        logging.debug(f"Script directory: {script_dir}")

        start_script = os.path.join(script_dir, 'singular_start_recording.sh')
        start_script = os.path.abspath(start_script)
        logging.debug(f"Start script path: {start_script}")

        if not os.access(start_script, os.X_OK):
            os.chmod(start_script, 0o755)
            logging.info(f"Made start script executable: {start_script}")

        command = f"{shlex.quote(start_script)} {duration} {shlex.quote(event['title'])}"
        logging.debug(f"Command to run: {command}")

        # Run the command directly without using gnome-terminal
        subprocess.run(command, shell=True, check=True)
        logging.info(f"Recording process completed for event: {event['title']}")

        completed_events += 1
        logging.info(f"Completed event: {event['title']}. Total completed: {completed_events}")

    except Exception as e:
        logging.error(f"Error running recording for event '{event['title']}': {e}")
        logging.debug("Exception details:", exc_info=True)


def schedule_events():
    global completed_events
    scheduler = BackgroundScheduler()
    events = load_events()
    current_time = datetime.now()
    logging.debug(f"Current time: {current_time}")

    if not events:
        logging.warning("No events found to schedule.")
        return scheduler, 0

    events.sort(key=lambda x: datetime.strptime(f"{x['start_date']} {x['start_time']}", "%Y-%m-%d %H:%M:%S"))

    last_end_time = None
    scheduled_count = 0

    for event in events:
        try:
            start_time = datetime.strptime(f"{event['start_date']} {event['start_time']}", "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(f"{event['end_date']} {event['end_time']}", "%Y-%m-%d %H:%M:%S")
            logging.debug(f"Scheduling event: {event['title']} from {start_time} to {end_time}")

            if start_time < current_time:
                logging.info(f"Skipping past event: {event['title']} at {start_time}")
                continue

            if last_end_time and start_time < last_end_time:
                logging.warning(f"Skipping overlapping event: {event['title']} at {start_time}")
                continue

            scheduler.add_job(
                run_recording,
                'date',
                run_date=start_time,
                args=[event],
                id=event['title'] + "_" + start_time.strftime("%Y%m%d_%H%M%S")
            )
            logging.info(f"Scheduled recording for '{event['title']}' at {start_time}")

            last_end_time = end_time
            scheduled_count += 1

            if scheduled_count >= 20:  # Event limit set to 20
                logging.info("Reached scheduled events limit of 20")
                break

        except Exception as e:
            logging.error(f"Error scheduling event '{event.get('title', 'Unknown')}': {e}")
            logging.debug("Exception details:", exc_info=True)

    logging.info(f"Total events scheduled: {scheduled_count}")
    return scheduler, scheduled_count


def all_events_completed(scheduled_count):
    return completed_events >= scheduled_count

if __name__ == "__main__":
    logging.info("Starting ubuntu_create_local_singular_recording.py")
    scheduler, scheduled_count = schedule_events()
    scheduler.start()
    logging.info("Scheduler started. Waiting for events...")
    try:
        while not all_events_completed(scheduled_count):
            time.sleep(60)
            logging.debug(f"Completed events: {completed_events}/{scheduled_count}")
    except (KeyboardInterrupt, SystemExit):
        logging.info("Received exit signal. Shutting down scheduler.")
    finally:
        scheduler.shutdown()
        logging.info("Scheduler stopped.")
        logging.info("All scheduled events completed. Exiting.")

