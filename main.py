import os
import time

from both import main as clean_video
from overlay import overlay_ball_ids
from track_csv import main as connect
from format_csv import main as format_csv
from fit_parabola import main as fit_parabola
from draw_parabola import overlay_parabolas
from draw_parabola_speed import overlay_parabolas as overlay_parabolas_speed
from new_video import main as contrast
from remove_slow_balls import main as remove_slow_balls
import detect_circle as circle_finder

def ensure_dir(filepath):
    parent = os.path.dirname(filepath)
    if parent:
        os.makedirs(parent, exist_ok=True)

def remove_file(file):
    try:
        os.remove(file)
    except FileNotFoundError:
        print("The file does not exist.")
    except PermissionError:
        print("Permission denied.")
    except OSError as e:
        print(f"Error: {e.strerror}")


def main(ThreadNum,URL):
    
    user_input = input("presets\n\tjust do it--- : a \n\tdebug-------- : b\n\tbenchmark---- : c\nmanual\n\tisolate balls : 1\n\tfind circle-- : 2\n\timport csv--- : 3\n\tfit parabola- : 4\n:")

    que = []

    if "a" in user_input:
        
        user_filepath_full = input("File path:")+ str(ThreadNum) + "/" + input("File names:")
        ensure_dir(user_filepath_full)
        print("using path", user_filepath_full)
        
        video_in = input ("Video path in:")
        video_processed = user_filepath_full + "video_processed.mp4"  
        que.append("clean_video")
        video_out_debug1 = ""   
        csv_log = user_filepath_full + "csv_log.csv"
        que.append("process_video")
        
        csv_unformated_out = user_filepath_full + "csv_unformated_out.csv"
        que.append("connect")
        csv_formated_out = user_filepath_full + "csv_formated_out.csv"
        que.append("format_csv")
        
        csv_parabola_out = user_filepath_full + "csv_parabola_out.csv"
        que.append("fit_parabola")
        que.append("remove_logs")
        que.append("log_time")
        
    elif "b" in user_input:
        
        #user_filepath_full = input("File path:") + "/" + input("File names:")
        user_filepath_full = f"/home/jasper/Python projects/Data/DEBUG_1{ThreadNum}/DEBUG_"
        ensure_dir(user_filepath_full)
        print("using path", user_filepath_full)
        
        #video_in = input ("Video path in:")
        video_in = "/home/jasper/Python projects/Data/testdat1.mp4"
        video_processed = user_filepath_full + "video_processed.mp4"  
        que.append("clean_video")#remove background
        
        video_out_debug1 = user_filepath_full + "debug1_video_out.mp4"
        csv_log = user_filepath_full + "csv_log.csv"
        que.append("process_video")#log balls
        
        #video_out_debug2 = user_filepath_full + "debug2_video_out.mp4"
        #que.append("contrast")#print better balls
        
        
        csv_unformated_out = user_filepath_full + "csv_unformated_out.csv"
        que.append("connect")
        video_out_debug3 = user_filepath_full + "debug3_video_out.mp4"
        que.append("overlay_ball_ids")
        csv_formated_out = user_filepath_full + "csv_formated_out.csv"
        que.append("format_csv")
        
        csv_parabola_out = user_filepath_full + "csv_parabola_out.csv"
        que.append("fit_parabola")
        csv_fast_ball_out = user_filepath_full + "csv_fast_ball_out.csv"
        que.append("remove_slow_balls")
        video_out_debug4 = user_filepath_full + "debug4_video_out.mp4"
        que.append("parabola_video")
        video_out_debug5 = user_filepath_full + "debug5_video_out.mp4"
        que.append("overlay_parabolas_speed")
        que.append("log_time")
        
    elif ("c" in user_input) or("z" in user_input):
        
        
        user_filepath_full = f"/home/jasper/Python projects/Data/BENCHMARK{ThreadNum}/BENCHMARK_"
        ensure_dir(user_filepath_full)
        
        video_in = "/home/jasper/Python projects/Data/testdat1.mp4"
        video_processed = user_filepath_full + "video_processed.mp4"  
        que.append("clean_video")
        
        video_out_debug1 = ""   
        csv_log = user_filepath_full + "csv_log.csv"
        que.append("process_video")
        
        csv_unformated_out = user_filepath_full + "csv_unformated_out.csv"
        que.append("connect")
        csv_formated_out = user_filepath_full + "csv_formated_out.csv"
        que.append("format_csv")
        
        csv_parabola_out = user_filepath_full + "csv_parabola_out.csv"
        que.append("fit_parabola")
        que.append("remove_logs")
        que.append("log_time")
    else:
        
        user_filepath_full = input("File path:") + "/" + input("File names:")
        ensure_dir(user_filepath_full)
        print("using path", user_filepath_full)
        
        if "1" in user_input:
        
            video_in = input ("Video path in:")
            video_processed = user_filepath_full + "video_processed.mp4"  
            que.append("clean_video")
        
        if "2" in user_input:
                
            
            if input("video out?(y/N)") == "y":
                video_out_debug1 = user_filepath_full + "debug1_video_out.mp4"
            else:
                video_out_debug1 = ""      
            csv_log = user_filepath_full + "csv_log.csv"
            que.append("process_video")
        if "3" in user_input:
            if "2" not in user_input:
                
                csv_log = input ("csv path in:")
            csv_unformated_out = user_filepath_full + "csv_unformated_out.csv"
            que.append("connect")
            if "y" == input("overlay ball id?(y/N)"):
                if "1" not in user_input:
                    video_in = input ("Video path in:")
                video_out_debug3 = user_filepath_full + "debug3_video_out.mp4"
                que.append("overlay_ball_ids")
            csv_formated_out = user_filepath_full + "csv_formated_out.csv"
            que.append("format_csv")
        if "4" in user_input:
            if "3" not in user_input:
                csv_formated_out = input("csv formated out path in:")
            csv_parabola_out = user_filepath_full + "csv_parabola_out.csv"
            que.append("fit_parabola")
            if "y" == input("overlay parabola?(y/N)"):
                if "1" not in user_input:
                    video_in = input ("Video path in:")
                video_out_debug4 = user_filepath_full + "debug4_video_out.mp4"
                que.append("parabola_video")
        if "y" == input("remove log files(y/N)"):
            que.append("remove_logs")
        que.append("log_time")

    if "log_time" in que:
        start = time.perf_counter()
    if "clean_video" in que:
        clean_video(video_in,video_processed)
    if "process_video" in que:
        circle_finder.process_video(video_processed, video_out_debug1, csv_log)
    #if "contrast" in que:
    #    contrast(csv_log, video_out_debug2)
    if "connect" in que:
        connect(csv_log, csv_unformated_out)
    if "overlay_ball_ids" in que:
        overlay_ball_ids(video_in,csv_unformated_out,video_out_debug3)
    if "format_csv" in que:
        format_csv(csv_unformated_out,csv_formated_out)
    if "fit_parabola" in que:
        fit_parabola(csv_formated_out,csv_parabola_out)
    if "remove_slow_balls" in que:
        remove_slow_balls(csv_parabola_out, csv_fast_ball_out)
    #if "parabola_video" in que:
    #    overlay_parabolas(video_in,csv_parabola_out,video_out_debug4)
    if "overlay_parabolas_speed" in que:
        overlay_parabolas_speed(video_in,csv_fast_ball_out,video_out_debug5)
    if "remove_logs" in que:
        remove_file(video_processed)
        remove_file(csv_log)
        remove_file(csv_unformated_out)
        remove_file(csv_formated_out)
    if "log_time" in que:
        end = time.perf_counter()
        total_time = end - start
        fps = circle_finder.frame_idx / total_time
        print(f"ran at {fps} fps")

if __name__ == "__main__":
    main(0,"https.google.com")