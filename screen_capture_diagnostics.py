import os
import subprocess
import sys

def run_command(command):
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

def check_xorg_permissions():
    print("Checking Xorg permissions:")
    commands = [
        ["xhost"],
        ["xauth", "list"],
        ["ls", "-l", "/dev/input/event*"],
        ["groups"],
    ]
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        print(run_command(cmd))
        print()

def check_screen_capture_tools():
    print("Checking screen capture tools:")
    tools = ["scrot", "import", "xwd"]
    for tool in tools:
        print(f"Checking {tool}:")
        print(run_command(["which", tool]))
        print(run_command([tool, "--version"]))
        print()

def check_display_info():
    print("Checking display information:")
    commands = [
        ["xrandr"],
        ["xdpyinfo"],
    ]
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        print(run_command(cmd))
        print()

def test_screen_capture():
    print("Testing screen capture:")
    tools = [
        ["scrot", "scrot_test.png"],
        ["import", "-window", "root", "import_test.png"],
        ["xwd", "-root", "-out", "xwd_test.xwd"],
    ]
    for cmd in tools:
        print(f"Running: {' '.join(cmd)}")
        result = run_command(cmd)
        print(result)
        if os.path.exists(cmd[-1]):
            print(f"File created: {cmd[-1]}")
            file_size = os.path.getsize(cmd[-1])
            print(f"File size: {file_size} bytes")
            if file_size > 1000:
                print("File size seems reasonable, likely captured successfully.")
            else:
                print("File size is small, might be a blank or failed capture.")
        else:
            print(f"File not created: {cmd[-1]}")
        print()

if __name__ == "__main__":
    print("Screen Capture Diagnostics")
    print("==========================")
    
    check_xorg_permissions()
    check_screen_capture_tools()
    check_display_info()
    test_screen_capture()
