import os

from both import main as clean_video
from detect_circle import process_video
from overlay import overlay_ball_ids
from track_csv import run as connect
from format_csv import main as format_csv
from fit_parabola import main as fit_parabola
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

user_input = input("presets\n\tjust do it--- : a \n\tdebug-------- : b\n\tbenchmark---- : c\nmanual\n\tisolate balls : 1\n\tfind circle-- : 2\n\timport csv--- : 3\n\tfit parabola- : 4\n:")



que = []

if "a" in user_input:
    
    user_filepath = input("File path:")
    ensure_dir(user_filepath)
    
    video_in = input ("Video path in:")
    video_processed = user_filepath + "video_processed.mp4"  
    que.append("clean_video")
    video_out_debug1 = ""   
    csv_log = user_filepath + "csv_log.csv"
    que.append("process_video")
    
    csv_unformated_out = user_filepath + "csv_unformated_out.csv"
    que.append("connect")
    csv_formated_out = user_filepath + "csv_formated_out.csv"
    que.append("format_csv")
    
    csv_parabola_out = user_filepath + "csv_parabola_out.csv"
    que.append("fit_parabola")
    que.append("remove_logs")
    
elif "b" in user_input:
    
    user_filepath = input("File path:")
    ensure_dir(user_filepath)
    
    video_in = input ("Video path in:")
    video_processed = user_filepath + "video_processed.mp4"  
    que.append("clean_video")
    
    video_out_debug1 = user_filepath + "debug1_video_out.mp4"
    csv_log = user_filepath + "csv_log.csv"
    que.append("process_video")
    
    csv_unformated_out = user_filepath + "csv_unformated_out.csv"
    que.append("connect")
    video_out_debug2 = user_filepath + "debug2_video_out.mp4"
    que.append("overlay_ball_ids")
    csv_formated_out = user_filepath + "csv_formated_out.csv"
    que.append("format_csv")
    
    csv_parabola_out = user_filepath + "csv_parabola_out.csv"
    que.append("fit_parabola")
    
elif "c" in user_input:
    
    user_filepath = "/home/jasper/Python projects/Data/BENCHMARK/BENCHMARK"
    ensure_dir(user_filepath)
    
    video_in = "/home/jasper/Python projects/Data/original.mp4"
    video_processed = user_filepath + "video_processed.mp4"  
    que.append("clean_video")
    
    video_out_debug1 = ""   
    csv_log = user_filepath + "csv_log.csv"
    que.append("process_video")
    
    csv_unformated_out = user_filepath + "csv_unformated_out.csv"
    que.append("connect")
    csv_formated_out = user_filepath + "csv_formated_out.csv"
    que.append("format_csv")
    
    csv_parabola_out = user_filepath + "csv_parabola_out.csv"
    que.append("fit_parabola")
    que.append("remove_logs")
else:
    
    user_filepath = input("File path:")
    ensure_dir(user_filepath)
    
    if "1" in user_input:
       
        video_in = input ("Video path in:")
        video_processed = user_filepath + "video_processed.mp4"  
        que.append("clean_video")
    
    if "2" in user_input:
            
        
        if input("video out?(y/N)") == "y":
            video_out_debug1 = user_filepath + "debug1_video_out.mp4"
        else:
            video_out_debug1 = ""      
        csv_log = user_filepath + "csv_log.csv"
        que.append("process_video")
    if "3" in user_input:
        if "2" not in user_input:
            
            csv_log = input ("csv path in:")
        csv_unformated_out = user_filepath + "csv_unformated_out.csv"
        que.append("connect")
        if "y" == input("overlay ball id?(y/N)"):
            if "1" not in user_input:
                video_in = input ("Video path in:")
            video_out_debug2 = user_filepath + "debug2_video_out.mp4"
            que.append("overlay_ball_ids")
        csv_formated_out = user_filepath + "csv_formated_out.csv"
        que.append("format_csv")
    if "4" in user_input:
        if "3" not in user_input:
            csv_formated_out = input("csv formated out path in:")
        csv_parabola_out = user_filepath + "csv_parabola_out.csv"
        que.append("fit_parabola")
    if "y" == input("remove log files(y/N)"):
        que.append("remove_logs")

if "clean_video" in que:
    clean_video(video_in,video_processed)
if "process_video" in que:
    process_video(video_processed, video_out_debug1, csv_log)
if "connect" in que:
    connect(csv_log, csv_unformated_out)
if "overlay_ball_ids" in que:
    overlay_ball_ids(video_in,csv_unformated_out,overlay_output)
if "format_csv" in que:
    format_csv(csv_unformated_out,csv_formated_out)
if "fit_parabola" in que:
    fit_parabola(csv_formated_out,csv_parabola_out)
if "remove_logs" in que:
    remove_file(video_processed)
    remove_file(csv_log)
    remove_file(csv_unformated_out)
    remove_file(csv_formated_out)