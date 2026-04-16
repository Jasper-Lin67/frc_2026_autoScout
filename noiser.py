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

    # --- THE SPEED TRICK ---
    # We allocate this block of memory exactly ONE time before the loop starts.
    # Re-creating empty arrays on every frame is a massive speed killer.
    noise_buffer = np.empty((height, width, 3), dtype=np.uint8)

    print("Processing started...")
    start_time = time.time()
    frame_idx = 0

    while True:
        ret, frame = video.read()
        if not ret:
            break

        # 1. Create a mask of pure black pixels. 
        # (0, 0, 0) to (0, 0, 0) means ONLY absolute black.
        mask = cv2.inRange(frame, (0, 0, 0), (0, 0, 0))

        # 2. Fill our pre-allocated buffer with random numbers (0 to 255).
        # cv2.randu is significantly faster than np.random.randint
        cv2.randu(noise_buffer, 0, 256)

        # 3. Paste the noise onto the frame, but ONLY where the mask is white (where black was).
        # This modifies the 'frame' directly in memory.
        cv2.copyTo(src=noise_buffer, mask=mask, dst=frame)

        # Write and track progress
        out.write(frame)
        
        frame_idx += 1
        
        print(f"Processed {frame_idx} frames...", end="\r")

    video.release()
    out.release()
    
    elapsed = time.time() - start_time
    print(f"\nProcessing complete! Processed {frame_idx} frames in {elapsed:.2f} seconds.")
    print(f"Average speed: {frame_idx / elapsed:.2f} FPS")

if __name__ == "__main__":
    # Change these paths to your actual files
    INPUT_VIDEO = "/home/jasper/Python projects/Data/red_out.mp4"
    OUTPUT_VIDEO = "/home/jasper/Python projects/Data/noise_out.mp4"
    
    black_to_noise(INPUT_VIDEO, OUTPUT_VIDEO)