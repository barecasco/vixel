"""
infer will produce frame by frame annotated output
first it will trim, then scam
"""

from ultralytics import YOLO
import cv2
import pandas as pd
import yaml
import sys
import os
import re
import json
from tqdm import tqdm
import plotly.graph_objects as go
from plotly.subplots import make_subplots



# ---------------------------------------------------------------------------
def get_base_filename(file_path):
    filename = os.path.basename(file_path)
    return os.path.splitext(filename)[0]


# Convert time strings to seconds
def time_to_seconds(time_str):
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s


# ---------------------------------------------------------------------------
# global vars
config              = None
config_file_path    = "config.yaml"
with open(config_file_path, 'r') as f:
    config = yaml.safe_load(f)  # Use safe_load for security

if not config:
    print(f">> Error: Configuration file not found at {config_file_path} <<")
    sys.exit()

species         = config.get("species")
model_path      = os.path.abspath(config.get("scanf_model_path"))

infer_path      = config.get("scanf_video_path")
infer_path      = os.path.abspath(infer_path)
video_name      = get_base_filename(infer_path)

video_fps       = config["scanf_fps"]
frame_interval  = int(config.get("scanf_interval"))

result_path     = os.path.join("./report", video_name)
res_img_path    = os.path.join(result_path, "images")

# result_path     = os.path.abspath(config.get("scanf_output_path"))
# res_img_path    = os.path.join(result_path, "images")

store_images    = config["scanf_store_images"]
full_scan       = config["scanf_full_scan"]

conf_thres      = config.get("scanf_conf_thres")
iou_thres       = config.get("scanf_iou_thres")
infer_imgsz     = config.get("scanf_rescale_size")

start_time      = config.get("scanf_start_time")
end_time        = config.get("scanf_end_time")

start_seconds   = time_to_seconds(start_time)
end_seconds     = time_to_seconds(end_time)

# Calculate start and end frames
start_frame     = int(start_seconds * video_fps)
end_frame       = int(end_seconds * video_fps)

# detection annotation
font            = cv2.FONT_HERSHEY_SIMPLEX
font_scale      = 0.5
padding         = 3
thickness       = 1

# set output folder
os.makedirs(result_path, exist_ok=True)
os.makedirs(res_img_path, exist_ok=True)

# Load the model
model = YOLO(model_path)
print("<< model loaded >>")


# ---------------------------------------------------------------------------
def infer(path):
    # Single image inference
    results = model.predict(
        source      = path,
        conf        = conf_thres,             
        iou         = iou_thres,              
        imgsz       = infer_imgsz,            
        save        = False,
        verbose     = False
    )

    return results

# ---------------------------------------------------------------------------
def process_inference(results):
    # Process results
    r = results[0]

    # masks = r.masks
    boxes = r.boxes  # box object for bounding boxes

    img   = r.plot(
        labels  = False,
        conf    = False,
        boxes   = False,
        masks   = False,
        probs   = False
    )

    for box in boxes:
        # get box coordinates in (top, left, bottom, right) format
        x1, y1, x2, y2 = box.xyxy[0]  
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # Draw box
        dw = 1
        cv2.rectangle(img, (x1, y1), (x2, y2), (38, 173, 255), dw)
        cv2.rectangle(img, (x1-dw, y1-dw), (x2+dw, y2+dw), (0, 0, 0), dw)
        
        # Add label
        label       = f"{model.names[int(box.cls)]} {float(box.conf):.2f}".upper()
        (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
        bg_rect = [
            (x1, y1 - text_height - padding * 2),
            (x1 + text_width + padding * 2, y1 + padding)
        ]
        
        # Draw background rectangle
        cv2.rectangle(img, bg_rect[0], bg_rect[1], (0, 0, 0), -1)  # Black background
        cv2.putText(
            img, label, (x1 + padding, y1 - padding), 
            font, font_scale, (255, 255, 255), thickness,
            cv2.LINE_AA
        )
    
    return img, boxes


# -------------------------------------------------------------------
def run_inference():
    global start_frame, end_frame
    cap             = cv2.VideoCapture(infer_path)
    video_fps       = cap.get(cv2.CAP_PROP_FPS)

    if not cap.isOpened():
        print(f"Error: Could not open video file: {infer_path}")
        sys.exit()

    max_frame   = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))    

    if full_scan:
        start_frame = 0
        end_frame   = max_frame
    else:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)



    boxd_list   = []
    for i in tqdm(range(start_frame, end_frame)):
        if i % frame_interval != 0:
            continue
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame  = cap.read() 
        
        if not ret:
            print("Error reading video frame")
            break

        results     = infer(frame)
        img, boxes  = process_inference(results)

        # Save the annotated image
        if store_images:
            fpath   = os.path.join(res_img_path, "frame-"+str(i)+".png")
            cv2.imwrite(fpath, img)

        timestamp   = round(i/video_fps, 2)
        
        shape            = boxes.orig_shape
        frame_height     = shape[0]
        frame_width      = shape[1]
        species_count    = len(boxes.conf)
        
        boxd = {
            "timestamp"     : timestamp,
            "species"       : species,
            "count"         : species_count,
            "frame_height"  : frame_height,
            "frame_width"   : frame_width,
            "cls"           : boxes.cls.cpu().numpy().tolist(),
            "conf"          : boxes.conf.cpu().numpy().tolist(),
            "xywh"          : boxes.xywh.cpu().numpy().tolist()
        } 

        boxd_list.append(boxd)
    
    # Pretty print with indentation
    boxd_sorted = sorted(boxd_list, key=lambda x: x['timestamp'])
    json_path   = os.path.join(result_path, video_name+".json")
    with open(json_path, 'w') as file:
        json.dump(boxd_sorted, file, indent=4)

    cap.release()


# -------------------------------------------------------------------
def analyze_result():
    json_path   = os.path.join(result_path, video_name+".json")
    json_path   = os.path.abspath(json_path)

    with open(json_path, "r") as f:
        ds = json.load(f)

    timestamps  = [item['timestamp'] for item in ds]
    counts      = [item['count'] for item in ds]
    conf_sums   = [sum(item['conf']) for item in ds]

    df = pd.DataFrame({
        "timestamp"     : timestamps,
        "fish-count"    : counts,
        "conf-sum"      : conf_sums 
    })

    # Create the plot
    fig = make_subplots()

    # Add fish count line
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['fish-count'],
            mode='lines+markers',
            name='Fish Count',
            line=dict(color='blue', width=2),
            marker=dict(size=1)
        )
    )

    # Find maximum fish count and add horizontal line
    max_fish_count = df['fish-count'].max()
    fig.add_hline(
        y=max_fish_count,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Max: {max_fish_count}",
        annotation_position="top right"
    )

    # Update layout
    fig.update_layout(
        title= 'Model count over time: ' + species,
        xaxis_title='Timestamp',
        yaxis_title='Number of Fish',
        template='plotly_white',
        hovermode='x unified',
        legend=dict(x=0.01, y=0.99, orientation='h'),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    # Make y-axis show only integer values since fish count is discrete
    fig.update_yaxes(dtick=1)

    # -------------------------------------------------------------------
    subject_name    = get_base_filename(json_path)
    subject_dirpath = os.path.dirname(json_path)
    html_path       = subject_dirpath + "/" + video_name +".html"
    csv_path        = subject_dirpath + "/" + video_name +".csv"
    fig.write_html(html_path)
    df.to_csv(csv_path)




if __name__=="__main__":
    run_inference()
    analyze_result()


