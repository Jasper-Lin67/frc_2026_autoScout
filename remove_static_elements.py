import numpy as np
import cv2

def process_video(videoIn, videoOut, pngOut, 
                  start_sec=0, analyze_duration_sec=30, static_threshold_pct=0.95, 
                  motion_threshold=30, expand_pixels=0):
    
    video = cv2.VideoCapture(videoIn)
    if not video.isOpened():
        print(f"Error: Could not open {videoIn}")
        return

    # FIXED: Added _FRAME_ to these constants
    fps = video.get(cv2.CAP_PROP_FPS)
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_video_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(videoOut, fourcc, fps, (width, height))

    # ==========================================
    # PHASE 1: ANALYZE FOR STATIC PIXELS
    # ==========================================
    
    video.set(cv2.CAP_PROP_POS_MSEC, start_sec * 1000)
    ret, ref_frame = video.read() 
    if not ret:
        print("Error: Could not read reference frame at specified start_sec.")
        return

    total_frames_to_check = int(fps * analyze_duration_sec)
    static_counter = np.zeros((height, width), dtype=np.uint32)

    print(f"Phase 1: Analyzing for all static elements...")

    for i in range(total_frames_to_check):
        ret, frame = video.read()
        if not ret: break
        
        diff = cv2.absdiff(ref_frame, frame)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        current_static_pixels = np.where(gray_diff < motion_threshold, 1, 0).astype(np.uint32)
        static_counter += current_static_pixels

        if i % int(fps) == 0:
            print(f"Analyzing: {i // int(fps)} / {analyze_duration_sec} seconds", end="\r")

    required_hits = total_frames_to_check * static_threshold_pct
    static_mask = np.where(static_counter >= required_hits, 255, 0).astype(np.uint8)

    # --- MASK EXPANSION (Dilation) ---
    # FIXED: Ensure expand_pixels is handled as an integer
    if int(expand_pixels) > 0:
        k_size = int(expand_pixels)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
        static_mask = cv2.dilate(static_mask, kernel, iterations=1)

    png_result = cv2.bitwise_and(ref_frame, ref_frame, mask=static_mask)
    cv2.imwrite(pngOut, png_result)
    print(f"\nSaved static elements reference to: {pngOut}")

    # ==========================================
    # PHASE 2: SUBTRACT STATIC BACKGROUND
    # ==========================================
    
    print("Phase 2: Removing static background from video...")
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
    process_video(
        videoIn="/home/jasper/Python projects/Data/testdat1.mp4", 
        videoOut="/home/jasper/Python projects/Data/static_removed.mp4", 
        pngOut="/home/jasper/Python projects/Data/static_reference.png",
        start_sec=30,                           
        analyze_duration_sec=10,    
        static_threshold_pct=0.95,  
        motion_threshold=30,        
        expand_pixels=0  # Use an integer here (number of pixels to grow)
    )