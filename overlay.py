import cv2
import csv
from collections import defaultdict


def load_csv(csv_path):
    """Load circle positions from CSV, indexed by frame number."""
    frames = defaultdict(list)
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            frame = int(row["frame_idx"])
            frames[frame].append({
                "circle_index": row["circle_idx"],
                "x": int(float(row["x"])),
                "y": int(float(row["y"])),
                "track_id": row["track_id"],
            })
    return frames


def overlay_ball_ids(input_video_path, csv_path, output_video_path):
    """
    Read circle positions from a CSV and superimpose ball IDs
    onto the corresponding video frames.

    Args:
        input_video_path:  Path to the original .mp4 file.
        csv_path:          Path to the tracked CSV produced by the DeepSort script.
        output_video_path: Path for the annotated output .mp4 file.
    """
    frames_data = load_csv(csv_path)

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {input_video_path}")

    fps    = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        for ball in frames_data.get(frame_idx, []):
            x, y = ball["x"], ball["y"]
            label = str(ball["track_id"])

            # Draw circle outline and centre dot
            cv2.circle(frame, (x, y), 10, (0, 255, 0), 1)
            cv2.circle(frame, (x, y), 2,  (0, 0, 255), 2)

            # Place the track ID label just above the circle
            font       = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.4
            thickness  = 1
            (tw, th), _ = cv2.getTextSize(label, font, font_scale, thickness)
            tx = x - tw // 2
            ty = y - 14

            # Dark background rectangle for readability
            cv2.rectangle(frame, (tx - 1, ty - th - 1), (tx + tw + 1, ty + 1), (0, 0, 0), -1)
            cv2.putText(frame, label, (tx, ty), font, font_scale, (0, 255, 255), thickness)

        writer.write(frame)
        frame_idx += 1
        
        print(f"  Processed {frame_idx} frames...", end="\r", flush=True)

    cap.release()
    writer.release()
    print(f"Done — {frame_idx} frames processed.")
    print(f"  Output: {output_video_path}")