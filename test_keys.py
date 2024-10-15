from pynput import keyboard

tracked_keys = ['`', '*']

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
        return False

with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
