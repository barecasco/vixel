"""
play video using opencv
"""

import tkinter as tk
from tkinter import ttk, filedialog
import cv2
import threading
import PIL.Image, PIL.ImageTk
import time

class VideoPlayer:
    def __init__(self, window):
        self.window = window
        self.window.title("Simple Video Player")
        
        # Video state variables
        self.video_source = None
        self.vid = None
        self.is_playing = False
        self.thread = None
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Top frame for controls
        self.control_frame = ttk.Frame(self.window)
        self.control_frame.pack(side=tk.TOP, pady=5)
        
        # Video address entry
        self.address_label = ttk.Label(self.control_frame, text="Video Address:")
        self.address_label.pack(side=tk.LEFT, padx=5)
        
        self.address_entry = ttk.Entry(self.control_frame, width=50)
        self.address_entry.pack(side=tk.LEFT, padx=5)
        
        # Browse button
        self.browse_btn = ttk.Button(self.control_frame, text="Browse", command=self.browse_file)
        self.browse_btn.pack(side=tk.LEFT, padx=5)
        
        # Load button
        self.load_btn = ttk.Button(self.control_frame, text="Load", command=self.load_video)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        # Play/Pause button
        self.play_btn = ttk.Button(self.control_frame, text="Play", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        # Canvas for video display
        self.canvas = tk.Canvas(self.window, width=800, height=600)
        self.canvas.pack(pady=5)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mkv *.mov"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.address_entry.delete(0, tk.END)
            self.address_entry.insert(0, filename)
    
    def load_video(self):
        if self.is_playing:
            self.is_playing = False
            if self.thread:
                self.thread.join()
        
        video_path = self.address_entry.get()
        if video_path:
            try:
                self.vid = cv2.VideoCapture(video_path)
                if not self.vid.isOpened():
                    raise ValueError("Unable to open video source")
                
                # Get video properties
                self.width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Resize canvas to match video dimensions (maintaining aspect ratio)
                aspect_ratio = self.width / self.height
                new_width = min(800, self.width)
                new_height = int(new_width / aspect_ratio)
                self.canvas.config(width=new_width, height=new_height)
                
                # Update play button text
                self.play_btn.config(text="Play")
                self.is_playing = False
                
            except Exception as e:
                tk.messagebox.showerror("Error", str(e))
    
    def toggle_play(self):
        if self.vid is None:
            return
        
        if self.is_playing:
            self.is_playing = False
            self.play_btn.config(text="Play")
            if self.thread:
                self.thread.join()
        else:
            self.is_playing = True
            self.play_btn.config(text="Pause")
            self.thread = threading.Thread(target=self.update_frame)
            self.thread.daemon = True
            self.thread.start()
    
    def update_frame(self):
        while self.is_playing:
            ret, frame = self.vid.read()
            if ret:
                # Resize frame to fit canvas
                frame = cv2.resize(frame, (self.canvas.winfo_width(), self.canvas.winfo_height()))
                # Convert frame to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert to PhotoImage
                photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
                
                # Update canvas
                self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
                self.canvas.photo = photo
                
                # Control frame rate
                time.sleep(1/30)  # Limit to approximately 30 FPS
            else:
                # Video ended
                self.is_playing = False
                self.play_btn.config(text="Play")
                self.vid.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning
                break
    
    def __del__(self):
        if self.vid:
            self.vid.release()

# Create and run the application
if __name__ == "__main__":
    root = tk.Tk()
    player = VideoPlayer(root)
    root.mainloop()