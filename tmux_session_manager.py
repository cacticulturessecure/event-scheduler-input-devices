import subprocess
import time
import json
import os
import logging
import sounddevice as sd

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TmuxSessionManager:
    def __init__(self, config_path='recording_config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        logging.info("TmuxSessionManager initialized with config")
        self.devices_in_use = set()
        self.audio_device_index = self.config['audio_only_recording']['device']['device_index']
        self.video_device_path = self.config['video_recording']['camera']['device_path']

    def create_session(self, session_name, command):
        logging.info(f"Creating tmux session: {session_name}")
        subprocess.run(['tmux', 'new-session', '-d', '-s', session_name, command])

    def session_exists(self, session_name):
        result = subprocess.run(['tmux', 'has-session', '-t', session_name], capture_output=True)
        exists = result.returncode == 0
        logging.debug(f"Session {session_name} exists: {exists}")
        return exists

    def kill_session(self, session_name):
        if self.session_exists(session_name):
            logging.info(f"Killing session: {session_name}")
            subprocess.run(['tmux', 'kill-session', '-t', session_name])

    def start_audio_recording(self, duration, event_title):
        self._release_audio_device()  # Ensure the audio device is released before starting
        session_name = f"audio_{event_title}"
        script_path = os.path.abspath("ubuntu_create_local_singular_audio_recording.py")
        command = f"python3 {script_path} {duration} '{event_title}'"
        logging.info(f"Starting audio recording: {command}")
        self.create_session(session_name, command)
        self.devices_in_use.add('audio')
        return session_name

    def start_video_recording(self, duration, event_title):
        self._release_video_device()  # Ensure the video device is released before starting
        session_name = f"video_{event_title}"
        script_path = os.path.abspath("ubuntu_create_local_singular_video_recording.py")
        command = f"python3 {script_path} {duration} '{event_title}'"
        logging.info(f"Starting video recording: {command}")
        self.create_session(session_name, command)
        self.devices_in_use.add('video')
        self.devices_in_use.add('audio')
        return session_name

    def wait_for_session_to_finish(self, session_name, timeout=None):
        logging.info(f"Waiting for session to finish: {session_name}")
        start_time = time.time()
        while self.session_exists(session_name):
            time.sleep(1)
            if timeout and (time.time() - start_time) > timeout:
                self.kill_session(session_name)
                logging.error(f"Session {session_name} timed out")
                raise TimeoutError(f"Session {session_name} timed out")
        logging.info(f"Session finished: {session_name}")

    def release_devices(self):
        logging.info("Releasing devices")
        for device in list(self.devices_in_use):
            if device == 'audio':
                self._release_audio_device()
            elif device == 'video':
                self._release_video_device()
        self.devices_in_use.clear()
        time.sleep(1)  # Add a small delay to ensure devices are fully released

    def _release_audio_device(self):
        logging.info("Releasing audio device")
        try:
            sd.stop()
            sd.default.device = None  # Reset the default device
            logging.info("Audio device released successfully")
        except Exception as e:
            logging.error(f"Failed to release audio device: {e}")

    def _release_video_device(self):
        logging.info("Releasing video device")
        try:
            # Reset auto exposure
            subprocess.run(['v4l2-ctl', '-d', self.video_device_path, '-c', 'auto_exposure=3'], check=True)
            # Reset brightness, contrast, and saturation to default values
            subprocess.run(['v4l2-ctl', '-d', self.video_device_path, '-c', 'brightness=128'], check=True)
            subprocess.run(['v4l2-ctl', '-d', self.video_device_path, '-c', 'contrast=128'], check=True)
            subprocess.run(['v4l2-ctl', '-d', self.video_device_path, '-c', 'saturation=128'], check=True)
            logging.info("Video device released successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to release video device: {e}")

    def cleanup(self):
        for session_name in ['audio_session', 'video_session']:
            if self.session_exists(session_name):
                self.kill_session(session_name)
        self.release_devices()

    def get_active_sessions(self):
        result = subprocess.run(['tmux', 'list-sessions', '-F', '#{session_name}'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        return []

    def force_release_all_devices(self):
        logging.info("Force releasing all devices")
        active_sessions = self.get_active_sessions()
        for session in active_sessions:
            if session.startswith('audio_') or session.startswith('video_'):
                self.kill_session(session)
        self._release_audio_device()
        self._release_video_device()
        self.devices_in_use.clear()
        time.sleep(2)  # Longer delay for force release
        logging.info("All devices forcefully released")

    def force_release_all_devices(self):
        logging.info("Force releasing all devices")
        active_sessions = self.get_active_sessions()
        for session in active_sessions:
            if session.startswith('audio_') or session.startswith('video_'):
                self.kill_session(session)
        self._release_audio_device()
        self._release_video_device()
        self.devices_in_use.clear()
        time.sleep(2)  # Longer delay for force release


    def start_combination_process(self, video_file, audio_file, output_file):
        logging.info("Starting combination process")
        session_name = f"combine_{os.path.basename(output_file)}"
        script_path = os.path.abspath("combine_audio_video.py")
        command = f"python3 {script_path} {video_file} {audio_file} {output_file}"
        logging.info(f"Combination command: {command}")
        self.create_session(session_name, command)
        return session_name

    def terminate_all_sessions(self):
        logging.info("Terminating all active recording sessions")
        active_sessions = self.get_active_sessions()
        for session in active_sessions:
            if session.startswith('audio_') or session.startswith('video_'):
                self.kill_session(session)
                logging.info(f"Terminated session: {session}")
        time.sleep(2)  # Give some time for sessions to fully terminate
