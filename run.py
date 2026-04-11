from detect_circle import process_video
from overlay import overlay_ball_ids
from track_csv import run

user_input = input("find circle : 1\nimport csv- : 2\n:")

if "1" in user_input:
    
    video_in = input ("Video path in:")
    video_out = input ("Video out(leave blank for none):")
    csv_out = input ("csv path out:")
    process_video( video_in, video_out, csv_out)

if "2" in user_input:
    if "1" not in user_input:
        csv_out = input ("csv path in:")
    csv_final_out = input ("csv path out:")
    run(csv_out, csv_final_out)
    overlay = input("overlay ball id?(y/N)")
    if "y" == overlay:
        if "1" not in user_input:
            video_in = input ("Video path in:")
        overlay_output = input ("overlay path output:")
        overlay_ball_ids(video_in,csv_final_out,overlay_output)