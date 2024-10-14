import os
import django
import sys
from datetime import date, timedelta
import json

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()

from django.core.management import call_command
from django.conf import settings
from deal_calendar.utils import export_events_for_date, export_events_for_date_range
from deal_calendar.chron_jobs.setup_recording_jobs import setup_recording_jobs

def get_user_choice():
    while True:
        print("\nChoose an option:")
        print("1. Export events for today")
        print("2. Export events for tomorrow")
        print("3. Export events for the next 7 days")
        print("4. Export events for yesterday")
        print("5. Export events for the past 7 days")
        choice = input("Enter your choice (1, 2, 3, 4, or 5): ")
        if choice in ['1', '2', '3', '4', '5']:
            return int(choice)
        print("Invalid choice. Please try again.")

def print_event_details(events):
    for event in events:
        print("\nEvent Details:")
        for key, value in event.items():
            if key == 'company':
                print(f"company: {value if value is not None else 'null'}")
            else:
                print(f"{key}: {value}")
        print("-" * 50)

def load_events_from_json(export_dir):
    events = []
    if os.path.exists(export_dir):
        for filename in os.listdir(export_dir):
            if filename.endswith('.json'):
                with open(os.path.join(export_dir, filename), 'r') as f:
                    event_data = json.load(f)
                    if 'company' not in event_data:
                        event_data['company'] = None
                    events.append(event_data)
    return events

def export_and_print_events(start_date, end_date):
    exported_count = export_events_for_date_range(start_date, end_date)
    print(f"Exported {exported_count} events for the date range")

    events = []
    for export_date in [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]:
        export_dir = os.path.join(settings.BASE_DIR, 'media', 'exports', export_date.strftime('%Y-%m-%d'))
        events.extend(load_events_from_json(export_dir))

    print_event_details(events)
    return exported_count

def main():
    choice = get_user_choice()
    today = date.today()

    if choice == 1:
        dates = [today]
        print(f"Exporting events for today ({today})...")
    elif choice == 2:
        dates = [today + timedelta(days=1)]
        print(f"Exporting events for tomorrow ({dates[0]})...")
    elif choice == 3:
        start_date = today
        end_date = today + timedelta(days=6)
        print(f"Exporting events for the next 7 days ({start_date} to {end_date})...")
        exported_count = export_and_print_events(start_date, end_date)

        for export_date in [start_date + timedelta(days=i) for i in range(7)]:
            setup_recording_jobs(export_date, settings.BASE_DIR)

        print("Manual export and setup completed.")
        return
    elif choice == 4:
        dates = [today - timedelta(days=1)]
        print(f"Exporting events for yesterday ({dates[0]})...")
    else:  # choice == 5
        start_date = today - timedelta(days=7)
        end_date = today - timedelta(days=1)
        print(f"Exporting events for the past 7 days ({start_date} to {end_date})...")
        exported_count = export_and_print_events(start_date, end_date)

        for export_date in [start_date + timedelta(days=i) for i in range(7)]:
            setup_recording_jobs(export_date, settings.BASE_DIR)

        print("Manual export and setup completed.")
        return

    total_exported = 0
    for export_date in dates:
        exported_count = export_events_for_date(export_date)
        total_exported += exported_count
        print(f"Exported {exported_count} events for {export_date}")

        # Load and print event details
        export_dir = os.path.join(settings.BASE_DIR, 'media', 'exports', export_date.strftime('%Y-%m-%d'))
        events = load_events_from_json(export_dir)
        print_event_details(events)

        setup_recording_jobs(export_date, settings.BASE_DIR)

    print(f"Manual export and setup completed. Total events exported: {total_exported}")

if __name__ == "__main__":
    main()

