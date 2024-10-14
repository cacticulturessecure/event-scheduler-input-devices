import os
import shutil
from datetime import date

# Source and destination directories
SOURCE_DIR = '/home/securemeup/workspace/dev-workspace/localdock-to-colab/media/exports'
DEST_DIR = '/home/securemeup/workspace/dev-workspace/event-scheduler-input-devices/media/exports'

def copy_json_files():
    current_date = date.today()
    date_str = current_date.strftime('%Y-%m-%d')
    source_path = os.path.join(SOURCE_DIR, date_str)
    dest_path = os.path.join(DEST_DIR, date_str)

    if os.path.exists(source_path):
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        for filename in os.listdir(source_path):
            if filename.endswith('.json'):
                source_file = os.path.join(source_path, filename)
                dest_file = os.path.join(dest_path, filename)
                shutil.copy2(source_file, dest_file)
                print(f"Copied: {source_file} -> {dest_file}")
    else:
        print(f"No directory found for date: {date_str}")

def main():
    print("This script will copy JSON files from the local Docker exports to the event-scheduler-input-devices directory for the current day.")
    copy_json_files()
    print("File copying complete.")

if __name__ == "__main__":
    main()
