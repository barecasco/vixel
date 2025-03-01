import cv2
import pandas as pd
import yaml
import math
import sys
import os
import re
import json
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots



# ---------------------------------------------------------------------------
# global vars
config              = None
config_file_path    = "config.yaml"
with open(config_file_path, 'r') as f:
    config = yaml.safe_load(f)  # Use safe_load for security

if not config:
    print(f"<< Error: Configuration file not found at {config_file_path} >>")
    sys.exit()

cam_sep         = config["cam_separation"]
cam_hfov         = config["cam_hfov"]
cam_vfov         = config["cam_vfov"]
cam_hdev         = config["cam_hdev"]
left_json_path   = config["left_cam_json"]
right_json_path  = config["right_cam_json"]


def central_longitude_from_px(px):
    coef_a          = config["lon_coef_a"]
    coef_t          = config["lon_coef_t"]
    res   = coef_a * np.atan(coef_t * px)
    return res    


def central_latitude_from_py(px):
    coef_a          = config["lat_coef_a"]
    coef_t          = config["lat_coef_t"]
    res   = coef_a * np.atan(coef_t * px)
    return res    


def calculate_fov(focal_length_mm, sensor_width_mm, sensor_height_mm):
    """
    Calculates the horizontal and vertical field of view (FOV) in degrees.

    Args:
        focal_length_mm: The focal length of the lens in millimeters.
        sensor_width_mm: The width of the sensor in millimeters.
        sensor_height_mm: The height of the sensor in millimeters.

    Returns:
        A tuple containing (HFOV_degrees, VFOV_degrees).  Returns (None, None) on error.
    """

    try:
        hfov_radians = 2 * math.atan(sensor_width_mm / (2 * focal_length_mm))
        vfov_radians = 2 * math.atan(sensor_height_mm / (2 * focal_length_mm))

        hfov_degrees = math.degrees(hfov_radians)
        vfov_degrees = math.degrees(vfov_radians)

        return hfov_degrees, vfov_degrees
    except Exception as e:
        print(f"Error calculating FOV: {e}")
        return None, None
    


def segment_distance(cam_dist, alpha, beta):
    c = cam_dist
    h = c * np.sin(alpha) * np.sin(beta) / np.sin(alpha + beta)
    return h


def get_distance_3d(a, b):
    x1 = a[0]
    y1 = a[1]
    z1 = a[2]

    x2 = b[0]
    y2 = b[1]
    z2 = b[2]

    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
    return distance


def angular_distance_law_of_cosines(lat1_rad, lon1_rad, lat2_rad, lon2_rad):
  # Apply the Spherical Law of Cosines
  cos_delta = (math.sin(lat1_rad) * math.sin(lat2_rad) +
               math.cos(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad))

  #Handle potential floating-point errors where cos_delta > 1 or < -1
  #If the points are near antipodal they can cause an error
  cos_delta = max(min(cos_delta, 1.0), -1.0) #clip to -1 to 1

  delta = math.acos(cos_delta)

  return delta



def get_principal_coordinates(cam_sep, left_lat, left_lon, right_lat, right_lon):
    # system parameter
    ab   = cam_sep

    # Image input
    caq  = left_lat
    qab  = left_lon

    cbq  = right_lat
    qba  = right_lon

    # calculate wipe angular distance
    cab = angular_distance_law_of_cosines(caq, qab, 0, 0)
    cba = angular_distance_law_of_cosines(cbq, qba, 0, 0)


    # calculate point distance to principal line
    hc = segment_distance(ab, cab, cba)

    # get x coordinate
    c_x = hc / np.tan(cab)

    # get hypotenuse
    ac = hc / np.sin(cab)

    # get z coordinate
    c_z = ac * np.sin(caq)

    # get plane hypotenuse
    aq = ac * np.cos(caq)
    # get y coordinate
    c_y = aq * np.sin(qab)

    # error analysis on c_y
   # c_y = hc / np.sin(cab) * np.cos(caq) * np.sin(qab)
    return [c_x, c_y, c_z]


def print_coordinates(coord):
    for id, cor in zip(['x', 'y', 'z'], coord):
        print(id, ":", round(float(cor), 4))


def print_coordinates_unity(coord):
    unity_coord = {}
    for id, cor in zip(['x', 'z', 'y'], coord):
        unity_coord[id] = cor
    for id in ['x', 'y', 'z']:
        print(id, ":", round(float(unity_coord[id]), 4))




# ---------------------------------------------------------------------
with open(left_json_path, "r") as f:
    left_cam = json.load(f)

with open(right_json_path, "r") as f:
    right_cam = json.load(f)

img_width       = left_cam['imageWidth']
img_height      = left_cam['imageHeight']
center_width    = img_width/2
center_height   = img_height/2
look_shift      = cam_hdev



leftpoints = {}
for mark in left_cam['shapes']:
    label = mark['label']
    leftpoints[label] = mark['points']

rightpoints = {}
for mark in right_cam['shapes']:
    label = mark['label']
    rightpoints[label] = mark['points']



leftpixels  = {}
rightpixels = {}

for key, points in leftpoints.items():
    leftpixels[key] = []
    for point in points:
        px = point[0] - center_width
        py = -(point[1] - center_height)
        leftpixels[key].append([px, py])

for key, points in rightpoints.items():
    rightpixels[key] = []
    for point in points:
        px = point[0] - center_width
        py = -(point[1] - center_height)
        rightpixels[key].append([px, py])


leftlonlats  = {}
rightlonlats = {}

for key, points in leftpixels.items():
    leftlonlats[key] = []
    
    for point in points:
        px = point[0]
        py = point[1]
        lon  = 90 - central_longitude_from_px(px) - 7
        lat  = central_latitude_from_py(py)
        leftlonlats[key].append([lon, lat])


for key, points in rightpixels.items():
    rightlonlats[key] = []
    for point in  points:
        px = point[0]
        py = point[1]
        lon  = 90 + central_longitude_from_px(px) - 7
        lat  = central_latitude_from_py(py)
        rightlonlats[key].append([lon, lat])
        


# Radian coef
to_rad      = np.pi/180.
distances   = {}

for key in leftlonlats:
    lefts       = leftlonlats[key]
    rights      = rightlonlats[key]
    coords      = []
    for i in [0, 1]:
        leftlonlat  = lefts[i]
        rightlonlat = rights[i]
        left_lon    = leftlonlat[0] * to_rad
        left_lat    = leftlonlat[1] * to_rad
        right_lon   = rightlonlat[0] * to_rad
        right_lat   = rightlonlat[1] * to_rad
        coord       = get_principal_coordinates(cam_sep, left_lat, left_lon, right_lat, right_lon)
        coords.append(coord)
    
    distance = np.round(get_distance_3d(coords[0], coords[1]) * 100, 3)
    distances[key] = distance
    

# ---------------------------------------------------------------
df = pd.DataFrame([distances]).transpose()
df.columns = ['size']
df.to_csv(config['output_file'])