import numpy as np
import cv2
from collections import deque

def hex_to_hsv_ranges(hex_color, h_tol=10, s_tol=40, v_tol=40):
    """
    Converts hex to HSV and applies individual tolerances for Hue, Saturation, and Value.
    """
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    rgb_pixel = np.uint8([[[b, g, r]]])
    hsv_pixel = cv2.cvtColor(rgb_pixel, cv2.COLOR_BGR2HSV)[0][0]

    h, s, v = int(hsv_pixel[0]), int(hsv_pixel[1]), int(hsv_pixel[2])

    s_lower, s_upper = np.clip([s - s_tol, s + s_tol], 0, 255)
    v_lower, v_upper = np.clip([v - v_tol, v + v_tol], 0, 255)
    
    h_lower = h - h_tol
    h_upper = h + h_tol

    ranges = []
    if h_lower < 0:
        ranges.append((np.array([0, s_lower, v_lower], dtype=np.uint8),
                       np.array([h_upper, s_upper, v_upper], dtype=np.uint8)))
        ranges.append((np.array([180 + h_lower, s_lower, v_lower], dtype=np.uint8),
                       np.array([180, s_upper, v_upper], dtype=np.uint8)))
    elif h_upper > 180:
        ranges.append((np.array([h_lower, s_lower, v_lower], dtype=np.uint8),
                       np.array([180, s_upper, v_upper], dtype=np.uint8)))
        ranges.append((np.array([0, s_lower, v_lower], dtype=np.uint8),
                       np.array([h_upper - 180, s_upper, v_upper], dtype=np.uint8)))
    else:
        ranges.append((np.array([h_lower, s_lower, v_lower], dtype=np.uint8),
                       np.array([h_upper, s_upper, v_upper], dtype=np.uint8)))
    return ranges

def main(videoIn, videoOut, allowed_colors, lookback_frames=10, h_t=10, s_t=50, v_t=50, box_size=(35, 75)):
    video = cv2.VideoCapture(videoIn)
    if not video.isOpened():
        print(f"Error: Could not open {videoIn}")
        return

    width  = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = video.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(videoOut, fourcc, fps, (width, height))

    all_ranges = []
    for color in allowed_colors:
        all_ranges.extend(hex_to_hsv_ranges(color, h_tol=h_t, s_tol=s_t, v_tol=v_t))

    mask_history = deque(maxlen=lookback_frames + 1)
    
    # --- Create the Solid Box Kernel ---
    # This defines the exact rectangular area we will expand detected pixels into.
    box_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, box_size)

    print(f"Tracking with tolerances -> H:{h_t}, S:{s_t}, V:{v_t}")

    frame_idx = 0
    while True:
        ret, frame = video.read()
        if not ret:
            break

        frame_idx += 1
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        current_mask = np.zeros((height, width), dtype=np.uint8)
        for lower, upper in all_ranges:
            mask = cv2.inRange(hsv, lower, upper)
            current_mask = cv2.bitwise_or(current_mask, mask)

        mask_history.append(current_mask)
        temporal_mask = current_mask.copy()
        for past_mask in mask_history:
            temporal_mask = cv2.bitwise_or(temporal_mask, past_mask)

        # --- The Native OpenCV Box Area ---
        # Dilation expands the mask natively in binary format. 
        # Any white pixel becomes a solid white rectangle of `box_size`.
        temporal_mask = cv2.dilate(temporal_mask, box_kernel, iterations=1)

        result = cv2.bitwise_and(frame, frame, mask=temporal_mask)
        out.write(result)
        print(f"Processed {frame_idx} frames...", end="\r")

    video.release()
    out.release()
    print("\nProcessing complete.")

if __name__ == "__main__":
    ALLOWED_HEX_LIST = ["#943045" ,"#6C4475"]
                        #,"#964E5F", "#2F1F21"]
    
    main(
        videoIn="/home/jasper/Python projects/Data/static_removed.mp4", 
        videoOut="/home/jasper/Python projects/Data/red_out.mp4", 
        allowed_colors=ALLOWED_HEX_LIST, 
        lookback_frames=7,
        h_t=8,
        s_t=45,
        v_t=60,
        box_size=(75, 85)  # (width, height) of the expansion box
    )