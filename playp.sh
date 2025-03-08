#!/bin/bash

# Usage: ./play_video_segment.sh input_file start_time end_time
# Example: ./play_video_segment.sh video.mp4 00:01:30 00:02:45

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install it first."
    exit 1
fi

# Check if ffplay is installed
if ! command -v ffplay &> /dev/null; then
    echo "Error: ffplay is not installed. Please install it first."
    exit 1
fi

# Check if correct number of arguments provided
if [ $# -ne 3 ]; then
    echo "Usage: $0 input_file start_time end_time"
    echo "Times should be in format HH:MM:SS or SS"
    exit 1
fi

INPUT_FILE="$1"
START_TIME="$2"
END_TIME="$3"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' does not exist."
    exit 1
fi

# Calculate duration
duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$INPUT_FILE")
start_seconds=$(echo "$START_TIME" | awk -F: '{ if (NF==3) print ($1*3600)+($2*60)+$3; else if (NF==2) print ($1*60)+$2; else print $1 }')
end_seconds=$(echo "$END_TIME" | awk -F: '{ if (NF==3) print ($1*3600)+($2*60)+$3; else if (NF==2) print ($1*60)+$2; else print $1 }')

# Validate time inputs
if (( $(echo "$start_seconds >= $duration" | bc -l) )); then
    echo "Error: Start time exceeds video duration."
    exit 1
fi

if (( $(echo "$end_seconds > $duration" | bc -l) )); then
    echo "Warning: End time exceeds video duration. Using video end instead."
    end_seconds=$duration
fi

if (( $(echo "$start_seconds >= $end_seconds" | bc -l) )); then
    echo "Error: Start time must be less than end time."
    exit 1
fi

# Calculate segment duration
segment_duration=$(echo "$end_seconds - $start_seconds" | bc)

echo "Playing segment from $START_TIME to $END_TIME (duration: $segment_duration seconds)"

# Play the video segment
ffplay -i "$INPUT_FILE" -ss "$START_TIME" -t "$segment_duration" -autoexit