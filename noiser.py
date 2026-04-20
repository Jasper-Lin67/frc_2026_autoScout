import cv2
import numpy as np
import time

def black_to_noise(videoIn, videoOut):
    video = cv2.VideoCapture(videoIn)
    if not video.isOpened():
        print(f"Error: Could not open {videoIn}")
        return

    # Get video properties
    width  = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = video.get(cv2.CAP_PROP_FPS)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(videoOut, fourcc, fps, (width, height))

    # Pre-allocate noise buffer for speed
    noise_buffer = np.empty((height, width, 3), dtype=np.uint8)

    start_time = time.time()
    frame_idx = 0

    # Define the threshold (3% of 255 is roughly 8)
    # This catches pixels from (0,0,0) up to (8,8,8)
    LOWER_BLACK = (0, 0, 0)
    UPPER_BLACK = (8, 8, 8)

    while True:
        ret, frame = video.read()
        if not ret:
            break

        # 1. Create a mask of "near-black" pixels (accounts for compression artifacts)
        mask = cv2.inRange(frame, LOWER_BLACK, UPPER_BLACK)

        # 2. Fill pre-allocated buffer with random noise
        cv2.randu(noise_buffer, 0, 256)

        # 3. Apply noise only to the masked areas
        cv2.copyTo(src=noise_buffer, mask=mask, dst=frame)

        out.write(frame)
        
        frame_idx += 1
        print(f"Processed {frame_idx} frames...", end="\r")

    video.release()
    out.release()
    
    elapsed = time.time() - start_time
    print(f"\nProcessing complete! {frame_idx} frames in {elapsed:.2f}s ({frame_idx/elapsed:.2f} FPS).")

if __name__ == "__main__":
    INPUT_VIDEO = "/home/jasper/Python projects/Data/red_out.mp4"
    OUTPUT_VIDEO = "/home/jasper/Python projects/Data/noise_out.mp4"
    
    black_to_noise(INPUT_VIDEO, OUTPUT_VIDEO)