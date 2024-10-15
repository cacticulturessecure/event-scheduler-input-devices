#!/usr/bin/env python3

import pyautogui
import time
import os
import sys

def capture_screen(output_dir, duration, interval):
    start_time = time.time()
    count = 0
    while time.time() - start_time < duration:
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(output_dir, f"screenshot_{count:06d}.png"))
        count += 1
        time.sleep(interval)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python screen_capture.py <output_directory> <duration> <interval>")
        sys.exit(1)

    output_dir = sys.argv[1]
    duration = float(sys.argv[2])
    interval = float(sys.argv[3])

    capture_screen(output_dir, duration, interval)
