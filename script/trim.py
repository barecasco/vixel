import subprocess
import time
import yaml
import sys
import os
import cv2

# -------------------------------------------------------------------
def trim_video_ffmpeg(input_path, output_path, start_time, end_time):
    """
    Trim video using FFmpeg
    """
    try:
        # FFmpeg command
        command = [
            'ffmpeg',
            '-i', input_path,
            '-ss', start_time,
            '-to', end_time,
            '-c:v', 'copy',     # Stream copy (no re-encode)
            '-c:a', 'copy',     # Stream copy (no re-encode)
            output_path,
            '-y'               # Overwrite output file if it exists
        ]
        
        # Run FFmpeg command
        subprocess.run(command, check=True)
        print(f"Video trimmed successfully! Saved to {output_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running FFmpeg: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


# -------------------------------------------------------------------
def trim_video_opencv(input_path, output_path, start_time, end_time):
    """
    Trim a video file based on start and end times.
    
    Parameters:
    input_path (str): Path to input video file
    output_path (str): Path to save trimmed video
    start_time (str): Start time in format "HH:MM:SS"
    end_time (str): End time in format "HH:MM:SS"
    """
    try:
        # Open the video file
        video = cv2.VideoCapture(input_path)
        
        # Get video properties
        fps = video.get(cv2.CAP_PROP_FPS)
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Convert time strings to seconds
        def time_to_seconds(time_str):
            h, m, s = map(int, time_str.split(':'))
            return h * 3600 + m * 60 + s
        
        start_seconds   = time_to_seconds(start_time)
        end_seconds     = time_to_seconds(end_time)
        
        # Calculate start and end frames
        start_frame     = int(start_seconds * fps)
        end_frame       = int(end_seconds * fps)
        
        # Set video writer
        fourcc  = cv2.VideoWriter_fourcc(*'mp4v')
        out     = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Set frame position to start_frame
        video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Read and write frames
        current_frame = start_frame
        
        while current_frame <= end_frame:
            ret, frame = video.read()
            
            if not ret:
                break
                
            out.write(frame)
            current_frame += 1
            
            # Optional: Show progress
            print(f"Processing frame {current_frame} of {end_frame}", end='\r')
        
        # Release resources
        video.release()
        out.release()
        
        print(f"\nVideo trimmed successfully! Saved to {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        # Ensure resources are released
        if 'video' in locals():
            video.release()
        if 'out' in locals():
            out.release()
        cv2.destroyAllWindows()



# -------------------------------------------------------------------
def get_base_filename(file_path):
    filename = os.path.basename(file_path)
    return os.path.splitext(filename)[0]



if __name__ == "__main__":
    # -------------------------------------------------------------------
    config              = None
    config_file_path    = "config.yaml"
    with open(config_file_path, 'r') as f:
        config = yaml.safe_load(f)  # Use safe_load for security

    if not config:
        print(f">> Error: Configuration file not found at {config_file_path} <<")
        sys.exit()


    input_video         = config["trim_filepath"]
    output_video        = config["trim_outpath"]
    start_time          = config["trim_start"]
    end_time            = config["trim_end"]
    
    # create output directory
    output_dir  = os.path.abspath(os.path.dirname(output_video))
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.abspath(output_video)

    # Test FFmpeg
    start = time.time()
    trim_video_ffmpeg(input_video, output_file, start_time, end_time)
    ffmpeg_time = time.time() - start
    print(f"FFmpeg processing time: {ffmpeg_time:.2f} seconds")

