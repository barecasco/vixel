"""
play video using ffmpeg ffplay
"""


import subprocess
import os
import time
import threading
import sys
import cv2
import numpy as np
from datetime import datetime

class VideoPlayer:
    def __init__(self):
        self.process = None
        self.is_playing = False
        self.start_time = 0
        self.duration = 0
        self.video_path = None
        self.capture = None
        self.current_frame = None
        self.frame_lock = threading.Lock()

    def print_controls(self):
        """Print playback control instructions"""
        print("\nPlayback Controls:")
        print("------------------")
        print("Space or p: Toggle pause")
        print("c: Capture current frame")
        print("q or ESC: Quit")
        print("f: Toggle fullscreen")
        print("m: Toggle mute")
        print("Left/Right arrows: Seek backward/forward by 10 seconds")
        print("Up/Down arrows: Seek forward/backward by 1 minute")
        print("Mouse click: Seek to percentage")
        print("------------------\n")

    def time_to_seconds(self, time_str):
        """Convert time string to seconds"""
        h, m, s = map(float, time_str.split(':'))
        return h * 3600 + m * 60 + s

    def capture_frame(self):
        """Capture the current frame and save it"""
        with self.frame_lock:
            if self.current_frame is not None:
                # Create screenshots directory if it doesn't exist
                if not os.path.exists('screenshots'):
                    os.makedirs('screenshots')
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshots/frame_{timestamp}.png"
                
                # Save the frame
                cv2.imwrite(filename, self.current_frame)
                print(f"\nFrame captured: {filename}")


    def frame_grabber(self):
        """Continuously grab frames from the video"""
        self.capture = cv2.VideoCapture(self.video_path)
        
        # Seek to start time
        self.capture.set(cv2.CAP_PROP_POS_MSEC, self.start_time * 1000)
        
        while self.is_playing:
            ret, frame = self.capture.read()
            if ret:
                with self.frame_lock:
                    self.current_frame = frame
            else:
                break
            
            # Control frame rate
            time.sleep(1/30)  # Limit to approximately 30 FPS
        
        self.capture.release()


    def progress_indicator(self):
        """Display a simple progress indicator"""
        elapsed = 0
        while self.is_playing and elapsed <= self.duration:
            sys.stdout.write(f"\rProgress: {elapsed:.1f}s / {self.duration:.1f}s ")
            sys.stdout.flush()
            time.sleep(0.1)
            elapsed += 0.1
        sys.stdout.write("\n")


    def play_video_segment(self, video_path, start_time, end_time):
        """Play a video segment using ffplay with playback controls"""
        
        if not os.path.exists(video_path):
            print(f"Error: Video file '{video_path}' not found.")
            return

        self.video_path = video_path
        self.print_controls()

        try:
            # Calculate duration
            self.start_time = self.time_to_seconds(start_time)
            end_seconds = self.time_to_seconds(end_time)
            self.duration = end_seconds - self.start_time

            command = [
                'ffplay',
                '-i', video_path,
                '-ss', start_time,
                '-t', str(self.duration),
                '-autoexit',
                '-window_title', f'Playing: {os.path.basename(video_path)}',
                '-x', '800',  # Window width
                '-y', '600'   # Window height
            ]
            
            print(f"Playing video from {start_time} to {end_time}")
            
            # Start the frame grabber in a separate thread
            self.is_playing = True
            frame_thread = threading.Thread(target=self.frame_grabber)
            frame_thread.daemon = True
            frame_thread.start()

            # # Start the progress indicator in a separate thread
            # progress_thread = threading.Thread(target=self.progress_indicator)
            # progress_thread.daemon = True
            # progress_thread.start()

            # Start keyboard listener for frame capture
            keyboard_thread = threading.Thread(target=self.keyboard_listener)
            keyboard_thread.daemon = True
            keyboard_thread.start()

            # Start the video playback
            self.process = subprocess.Popen(command)
            self.process.wait()

            # Clean up
            self.is_playing = False
            frame_thread.join()
            # progress_thread.join()
            keyboard_thread.join()
            
        except subprocess.CalledProcessError as e:
            print(f"Error playing video: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if self.process:
                self.process.terminate()
            if self.capture:
                self.capture.release()

    def keyboard_listener(self):
        """Listen for keyboard input to capture frames"""
        try:
            import keyboard
            
            while self.is_playing:
                if keyboard.is_pressed('c'):
                    self.capture_frame()
                    # Small delay to prevent multiple captures
                    time.sleep(0.5)
                time.sleep(0.1)
                
        except ImportError:
            print("Keyboard module not found. Install it using: pip install keyboard")


def main():
    player = VideoPlayer()
    
    try:
        video_file  = input("Enter video path: ")
        start       = input("Enter start time (HH:MM:SS): ")
        end         = input("Enter end time (HH:MM:SS): ")
        
        player.play_video_segment(video_file, start, end)
    
    except KeyboardInterrupt:
        print("\nPlayback interrupted by user")
        if player.process:
            player.process.terminate()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()