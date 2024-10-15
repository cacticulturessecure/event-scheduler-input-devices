we are having issues with the event listenter not working. What are some test I can run to record what the buttons are the user is entering to ensure our program works. Review the current code and then produce a a few python scripts that will record what the user depresses so we can best leverage keys like ` and *. i'm on ubuntu so we need to ensure we're tracking the keys properly in the program when we run python.

import os
import time
from datetime import datetime
from pynput import keyboard
from PIL import ImageGrab
import json
import threading

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
    
    while not stop_event.is_set():
        if is_capturing:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if image_count % BATCH_SIZE == 0:
                batch_count += 1
                batch_dirs = [os.path.join(dir, f"batch_{batch_count:04d}") for dir in output_dirs]
                for dir in batch_dirs:
                    os.makedirs(dir, exist_ok=True)
            
            screenshot = ImageGrab.grab()
            
            for dir in batch_dirs:
                screenshot.save(os.path.join(dir, f"{timestamp}.png"))
            
            image_count += 1
            time.sleep(CAPTURE_INTERVAL)

def on_press(key):
    global is_capturing, capture_thread, event_folder_name
    
    try:
        if key.char == '`':  # Check for the backtick character
            toggle_capture()
    except AttributeError:
        # Not a character key
        pass

    if key == keyboard.Key.ctrl_l:
        return True  # Continue to listen for the 's' key

def on_release(key):
    if key == keyboard.Key.ctrl_l:
        return True  # Continue to listen for the 's' key
    
    if key == keyboard.KeyCode.from_char('s'):
        print("Stopping screen capture")
        stop_event.set()
        global is_capturing
        is_capturing = False
        if capture_thread:
            capture_thread.join()
        return False  # Stop the listener

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

print("Screen Capture Tool")

event_folder_name = input("Enter the name of the directory for screenshots: ").strip()

print("Press '`' to start/pause capturing")
print("Press Ctrl+S to stop the program")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
To help you track and record the keys pressed by the user, especially for keys like `` and `*`, I'll provide you with a few Python scripts that can help you achieve this. These scripts will work on Ubuntu and should help you identify any issues with your event listener.

1. Basic Key Logger:

This script will log all key presses to a file:

```python
from pynput import keyboard
import logging

# Set up logging
logging.basicConfig(filename="key_log.txt", level=logging.DEBUG, format='%(asctime)s: %(message)s')

def on_press(key):
    try:
        logging.info(f'Key pressed: {key.char}')
    except AttributeError:
        logging.info(f'Special key pressed: {key}')

def on_release(key):
    logging.info(f'Key released: {key}')
    if key == keyboard.Key.esc:
        # Stop listener
        return False

# Collect events until released
with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
```

2. Real-time Key Display:

This script will display key presses in real-time in the console:

```python
from pynput import keyboard

def on_press(key):
    try:
        print(f'Key pressed: {key.char}')
    except AttributeError:
        print(f'Special key pressed: {key}')

def on_release(key):
    print(f'Key released: {key}')
    if key == keyboard.Key.esc:
        # Stop listener
        return False

# Collect events until released
with keyboard.Listener(
     pynput import keyboard

tracke    on_press=on_press,d_keys = ['`', '*']

def on_press(key):
    try:
        if key.char in tracked_keys:
            print(f'Tracked key pressed: {key.char}')
    except AttributeError:
        pass

def on_release(key):
    try:
        if key.char in tracked_keys:
            print(f'Tracked key released: {key.char}')
    except AttributeError:
        pass
    
    if key == keyboard.Key.esc:
        # Stop listener
        return False

# Collect events until released
with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
```

To use these scripts:

1. Make sure you have the `pynput` library installed. If not, install it using pip:
   ```
   pip install pynput
   ```

2. Save each script as a separate Python file (e.g., `key_logger.py`, `realtime_display.py`, `specific_key_tracker.py`).

3. Run the scripts using Python from the terminal:
   ```
   python3 script_name.py
   ```

4. Press keys and observe the output. Press the 'Esc' key to stop the script.

These scripts should help you track and record key presses, allowing you to debug your event listener issues. The first script logs all key presses to a file, the second displays them in real-time in the console, and the third focuses on specific keys you're interested in.

Remember to run these scripts with appropriate permissions, as key logging can be sensitive. Always inform users if you're logging their keystrokes and ensure you comply with relevant privacy laws and regulations.
        on_release=on_release) as listener:
    listener.join()
```

3. Specific Key Tracker:

This script will focus on tracking specific keys like `` and `*`:

```python
from
