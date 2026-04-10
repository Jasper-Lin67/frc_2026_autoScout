import cv2
import numpy as np
import csv

def find_circles(img):
    output = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 1)
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=10,
        param1=100,
        param2=10,
        minRadius=2,
        maxRadius=11
    )
    
    positions = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for x, y, r in circles[0]:
            cv2.circle(output, (x, y), r, (0, 255, 0), 1)
            cv2.circle(output, (x, y), 2, (0, 0, 255), 2)
            positions.append((x, y, r))
    return output, positions

def process_video(input_path, output_video_path, output_csv_path):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {input_path}")
    if output_video_path:
        fps    = cap.get(cv2.CAP_PROP_FPS)
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"h265")
        writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    with open(output_csv_path, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["frame", "circle_index", "x", "y", "radius"])
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            annotated, positions = find_circles(frame)
            if output_video_path:
                writer.write(annotated)
            for circle_idx, (x, y, r) in enumerate(positions):
                csv_writer.writerow([frame_idx, circle_idx, x, y, r])
            frame_idx += 1
            if frame_idx % 100 == 0:
                print(f"  Processed {frame_idx} frames...")
    cap.release()
    writer.release()
    print(f"Done — {frame_idx} frames processed.")
    print(f"  Video : {output_video_path}")
    print(f"  CSV   : {output_csv_path}")

process_video(
    "/home/jasper/Python projects/Data/both.mp4",
    "",
    "both_out.csv"
)