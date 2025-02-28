
import yaml
import sys
import os
from tqdm import tqdm


# -------------------------------------------------------------------
def get_base_filename(file_path):
    filename = os.path.basename(file_path)
    return os.path.splitext(filename)[0]

# -------------------------------------------------------------------
config              = None
config_file_path    = "config.yaml"
with open(config_file_path, 'r') as f:
    config = yaml.safe_load(f)  # Use safe_load for security

if not config:
    print(f">> Error: Configuration file not found at {config_file_path} <<")
    sys.exit()


# -------------------------------------------------------------------
filepath        = config.get("frag_filepath")
filepath        = os.path.abspath(filepath)
subject_dirpath = os.path.dirname(filepath)
base_fname      = get_base_filename(filepath)
sliced_path     = os.path.join(subject_dirpath, "sliced_" + base_fname + ".mp4")
frag_fps        = config.get("frag_fps")
start_time      = config.get("frag_start_time")
end_time        = config.get("frag_end_time")



# ------------------------------------------------------------------- SLICE
print("<< start slicing >>")
cmd_list = [
    "ffmpeg -i",
    filepath,
    "-ss",
    start_time,
    "-to",
    end_time,
    "-c copy",
    sliced_path,
    "-y"
]

os.system(" ".join(cmd_list))
print("<< slicing done >>")

# ------------------------------------------------------------------- FRAG
print("<< start fragmenting >>")
cmd_list = [
    'ffmpeg -i',
    sliced_path,
    '-vf',
    f'"fps={frag_fps}"',
    '-frame_pts 1',
    ' -qscale:v 1',
    f'"{subject_dirpath}/fps_{frag_fps}_frame_%d.jpg"'
]

print(" ".join(cmd_list))
# sys.exit()
os.system(" ".join(cmd_list))
os.remove(sliced_path)
print("<< fragmenting done >>")

