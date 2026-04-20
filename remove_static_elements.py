import numpy as np
import cv2

def hex_to_hsv_ranges(hex_color, h_tol, s_tol, v_tol):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    rgb_pixel = np.uint8([[[b, g, r]]])
    hsv_pixel = cv2.cvtColor(rgb_pixel, cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = int(hsv_pixel[0]), int(hsv_pixel[1]), int(hsv_pixel[2])

    s_lower, s_upper = np.clip([s - s_tol, s + s_tol], 0, 255)
    v_lower, v_upper = np.clip([v - v_tol, v + v_tol], 0, 255)
    h_lower, h_upper = h - h_tol, h + h_tol

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

def process_video(videoIn, videoOut, pngOut, allowed_colors, 
                  start_sec=0, analyze_duration_sec=30, static_threshold_pct=0.95, 
                  h_t=8, s_t=50, v_t=50, 
                  expand_pixels=10, median_blur=5):
    
    video = cv2.VideoCapture(videoIn)
    if not video.isOpened():
        print(f"Error: Could not open {videoIn}")
        return

    fps = video.get(cv2.CAP_PROP_FPS)
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_video_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(videoOut, fourcc, fps, (width, height))

    all_ranges = []
    for color in allowed_colors:
        all_ranges.extend(hex_to_hsv_ranges(color, h_tol=h_t, s_tol=s_t, v_tol=v_t))

    # PHASE 1: ANALYZE
    video.set(cv2.CAP_PROP_POS_MSEC, start_sec * 1000)
    total_frames_to_check = int(fps * analyze_duration_sec)
    hit_counter = np.zeros((height, width), dtype=np.uint32)

    print(f"Phase 1: Analyzing for static elements...")

    for i in range(total_frames_to_check):
        ret, frame = video.read()
        if not ret: break
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        current_frame_mask = np.zeros((height, width), dtype=np.uint8)
        for lower, upper in all_ranges:
            m = cv2.inRange(hsv, lower, upper)
            current_frame_mask = cv2.bitwise_or(current_frame_mask, m)

        hit_counter += (current_frame_mask > 0).astype(np.uint32)

    required_hits = total_frames_to_check * static_threshold_pct
    static_mask = np.where(hit_counter >= required_hits, 255, 0).astype(np.uint8)

    # --- MASK EXPANSION (Dilation) ---
    if expand_pixels > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (expand_pixels, expand_pixels))
        static_mask = cv2.dilate(static_mask, kernel, iterations=1)

    # --- BLUR CLEANUP ---
    if median_blur > 0:
        static_mask = cv2.medianBlur(static_mask, median_blur)

    # --- RE-BINARIZE: ensure mask is strictly 0 or 255 before inversion ---
    _, static_mask = cv2.threshold(static_mask, 127, 255, cv2.THRESH_BINARY)

    # Save reference
    video.set(cv2.CAP_PROP_POS_FRAMES, 0) 
    ret, first_frame = video.read()
    if ret:
        png_result = cv2.bitwise_and(first_frame, first_frame, mask=static_mask)
        cv2.imwrite(pngOut, png_result)

    # PHASE 2: SUBTRACT
    print("Phase 2: Subtracting expanded static elements...")
    inverse_static_mask = cv2.bitwise_not(static_mask)
    video.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    frame_idx = 0
    while True:
        ret, frame = video.read()
        if not ret: break
        frame_idx += 1
        result = cv2.bitwise_and(frame, frame, mask=inverse_static_mask)
        out.write(result)
        print(f"Processed {frame_idx} / {total_video_frames} frames...", end="\r")

    video.release()
    out.release()
    print("\nProcessing complete.")

if __name__ == "__main__":
    ALLOWED_HEX_LIST = ["#943045", "#5A2227", "#CE2C27"]
    process_video(
        videoIn="/home/jasper/Python projects/Data/testdat1.mp4", 
        videoOut="/home/jasper/Python projects/Data/static_removed.mp4", 
        pngOut="/home/jasper/Python projects/Data/static_reference.png",
        allowed_colors=ALLOWED_HEX_LIST,
        start_sec=30,               
        analyze_duration_sec=10,    
        static_threshold_pct=0.95,  
        h_t=7, s_t=55, v_t=35,
        expand_pixels=0,
        median_blur=5,
    )