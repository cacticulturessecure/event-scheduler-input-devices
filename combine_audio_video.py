import subprocess
import sys
import logging

def combine_audio_video(video_file, audio_file, output_file):
    cmd = f"ffmpeg -i {video_file} -i {audio_file} -c:v copy -c:a aac -strict experimental {output_file}"
    subprocess.run(cmd, shell=True, check=True)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python combine_audio_video.py <video_file> <audio_file> <output_file>")
        sys.exit(1)
    
    video_file, audio_file, output_file = sys.argv[1:]
    combine_audio_video(video_file, audio_file, output_file)
