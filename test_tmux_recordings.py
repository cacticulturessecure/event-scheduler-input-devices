import unittest
import time
import logging
from tmux_session_manager import TmuxSessionManager

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TestTmuxRecordings(unittest.TestCase):
    def setUp(self):
        self.manager = TmuxSessionManager()

    def tearDown(self):
        self.manager.cleanup()

    def test_audio_recording(self):
        duration = 5  # 5 seconds
        event_title = "test_audio_event"
        session_name = self.manager.start_audio_recording(duration, event_title)
        
        time.sleep(1)  # Give it a moment to start
        self.assertTrue(self.manager.session_exists(session_name))
        
        try:
            self.manager.wait_for_session_to_finish(session_name, timeout=duration + 10)
        except TimeoutError:
            self.fail("Audio recording session timed out")
        
        self.assertFalse(self.manager.session_exists(session_name))
        self.manager.release_devices()

    def test_video_recording(self):
        duration = 5  # 5 seconds
        event_title = "test_video_event"
        session_name = self.manager.start_video_recording(duration, event_title)
        
        time.sleep(1)  # Give it a moment to start
        self.assertTrue(self.manager.session_exists(session_name))
        
        try:
            self.manager.wait_for_session_to_finish(session_name, timeout=duration + 15)
        except TimeoutError:
            self.fail("Video recording session timed out")
        
        self.assertFalse(self.manager.session_exists(session_name))
        self.manager.release_devices()

    def test_concurrent_recordings(self):
        audio_duration = 10
        video_duration = 8
        audio_event = "concurrent_audio_event"
        video_event = "concurrent_video_event"

        audio_session = self.manager.start_audio_recording(audio_duration, audio_event)
        video_session = self.manager.start_video_recording(video_duration, video_event)

        time.sleep(1)
        self.assertTrue(self.manager.session_exists(audio_session))
        self.assertTrue(self.manager.session_exists(video_session))

        try:
            self.manager.wait_for_session_to_finish(video_session, timeout=video_duration + 15)
            self.manager.wait_for_session_to_finish(audio_session, timeout=audio_duration + 15)
        except TimeoutError:
            self.fail("One or both concurrent recording sessions timed out")

        self.assertFalse(self.manager.session_exists(audio_session))
        self.assertFalse(self.manager.session_exists(video_session))
        self.manager.release_devices()

if __name__ == '__main__':
    unittest.main()
