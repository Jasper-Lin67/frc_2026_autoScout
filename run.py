import os

from detect_circle import process_video
from overlay import overlay_ball_ids
from track_csv import run as connect
from format_csv import main as format_csv

def ensure_dir(filepath):
    parent = os.path.dirname(filepath)
    if parent:
        os.makedirs(parent, exist_ok=True)

def remove_file(file):
    try:
        os.remove("file")
    except FileNotFoundError:
        print("The file does not exist.")
    except PermissionError:
        print("Permission denied.")
    except OSError as e:
        print(f"Error: {e.strerror}")

user_input = input("find circle : 1\nimport csv- : 2\n:")
user_filepath = input("File path:")

ensure_dir(user_filepath)


if "1" in user_input:
        
    video_in = input ("Video path in:")
    if input("video out?(y/N)") == "y":
        video_out = user_filepath + "stage1_video_out.mp4"
    else:
        video_out = ""
        
    csv_log = user_filepath + "csv_log.csv"
    process_video( video_in, video_out, csv_log)

if "2" in user_input:
    if "1" not in user_input:
        
        csv_log = input ("csv path in:")
    csv_unformated_out = user_filepath + "csv_unformated_out.csv"
    connect(csv_log, csv_unformated_out)
    
    if "y" == input("overlay ball id?(y/N)"):
        if "1" not in user_input:
            video_in = input ("Video path in:")
        overlay_output = user_filepath + "overlay_out.mp4"
        overlay_ball_ids(video_in,csv_unformated_out,overlay_output)
        
    csv_formated_out = user_filepath + "csv_formated_out.csv"
    format_csv(csv_unformated_out,csv_formated_out)

if "y" == input("remove log files(y/N)"):
    remove_file(csv_log)
    remove_file(csv_unformated_out)
