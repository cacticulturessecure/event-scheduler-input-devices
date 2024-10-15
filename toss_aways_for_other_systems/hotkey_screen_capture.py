import os
import sys
import time
import tty
import termios
from datetime import datetime
import json
import threading
import mss
import mss.tools

# Load configuration
with open('recording_config.json', 'r') as f:
    config = json.load(f)

OUTPUT_DIRS = config['output_directories']
CAPTURE_INTERVAL = 1  # 1 second between captures
BATCH_SIZE = 5  # Number of images per folder

is_capturing = False
capture_thread = None
stop_event = threading.Event()
event_folder_name = None

def create_output_dirs(folder_name):
    date_str = datetime.now().strftime("%Y-%m-%d")
    return [os.path.join(dir, date_str, folder_name) for dir in OUTPUT_DIRS]

def capture_screen(output_dirs):
    image_count = 0
    batch_count = 0
    
    with mss.mss() as sct:
        monitor = sct.monitors[0]  # Capture the primary monitor
        
        while not stop_event.is_set():
            if is_capturing:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if image_count % BATCH_SIZE == 0:
                    batch_count += 1
                    batch_dirs = [os.path.join(dir, f"batch_{batch_count:04d}") for dir in output_dirs]
                    for dir in batch_dirs:
                        os.makedirs(dir, exist_ok=True)
                
                screenshot = sct.grab(monitor)
                
                for dir in batch_dirs:
                    mss.tools.to_png(screenshot.rgb, screenshot.size, output=os.path.join(dir, f"{timestamp}.png"))
                
                image_count += 1
                print(f"Captured image {image_count} in batch {batch_count}")  # Debug output
                time.sleep(CAPTURE_INTERVAL)

def toggle_capture():
    global is_capturing, capture_thread, event_folder_name
    
    is_capturing = not is_capturing
    if is_capturing:
        print(f"Screen capture started. Saving to folder: {event_folder_name}")
        
        if not capture_thread or not capture_thread.is_alive():
            output_dirs = create_output_dirs(event_folder_name)
            capture_thread = threading.Thread(target=capture_screen, args=(output_dirs,))
            capture_thread.start()
    else:
        print("Screen capture paused")

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def read_escape_sequence():
    sequence = ""
    while True:
        char = getch()
        sequence += char
        if char == '~':
            break
    return sequence

def main():
    global event_folder_name, is_capturing
    
    print("Screen Capture Tool")
    event_folder_name = input("Enter the name of the directory for screenshots: ").strip()
    
    print("Press Fn+F9 to start/pause capturing")
    print("Press Fn+F10 to stop the program")

    while True:
        char = getch()
        if char == '\x1b':  # ESC character
            sequence = read_escape_sequence()
            if sequence == '[20~':
                print("Fn+F9 pressed")
                toggle_capture()
            elif sequence == '[21~':
                print("Fn+F10 pressed")
                print("Stopping screen capture")
                stop_event.set()
                if capture_thread and capture_thread.is_alive():
                    capture_thread.join()
                break
        elif char == '\x03':  # Ctrl+C
            print("Ctrl+C pressed. Exiting.")
            stop_event.set()
            if capture_thread and capture_thread.is_alive():
                capture_thread.join()
            break

if __name__ == "__main__":
    main()
